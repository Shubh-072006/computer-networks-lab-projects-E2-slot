"""
TCP Client for LAN File Transfer System
Handles file transfers with progress tracking and integrity verification
"""

import hashlib
import json
import os
import socket
import time
from pathlib import Path
from typing import Optional, Callable, Tuple

from config import (
    BUFFER_SIZE, CHUNK_SIZE, DEFAULT_PASSWORD
)
from utils import (
    setup_logging, calculate_file_hash, format_file_size,
    validate_file_path, log_transfer
)


class FileTransferClient:
    """
    TCP client for sending files to the server with progress tracking
    """
    
    def __init__(self, password: str = DEFAULT_PASSWORD):
        """
        Initialize the file transfer client
        
        Args:
            password (str): Pre-shared password for authentication
        """
        self.password = password
        self.logger = setup_logging()
        self.client_socket = None
        
        # Callbacks for GUI updates
        self.on_connected: Optional[Callable] = None
        self.on_transfer_progress: Optional[Callable] = None
        self.on_transfer_complete: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
    
    def connect_to_server(self, server_ip: str, server_port: int, timeout: int = 10) -> bool:
        """
        Connect to the file transfer server
        
        Args:
            server_ip (str): Server IP address
            server_port (int): Server port
            timeout (int): Connection timeout in seconds
            
        Returns:
            bool: True if connected successfully, False otherwise
        """
        try:
            # Create client socket
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(timeout)
            
            # Connect to server
            self.client_socket.connect((server_ip, server_port))
            
            self.logger.info(f"Connected to server {server_ip}:{server_port}")
            
            if self.on_connected:
                self.on_connected(server_ip, server_port)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to server: {e}")
            if self.on_error:
                self.on_error(f"Connection failed: {e}")
            return False
    
    def authenticate(self) -> bool:
        """
        Authenticate with the server using pre-shared password
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            # Receive authentication request
            auth_request = self._receive_message()
            
            if not auth_request or auth_request.get("type") != "auth_request":
                self.logger.error("Invalid authentication request received")
                return False
            
            # Send password
            auth_response = {
                "type": "auth_response",
                "password": self.password
            }
            self._send_message(auth_response)
            
            # Receive authentication result
            auth_result = self._receive_message()
            
            if auth_result and auth_result.get("type") == "auth_success":
                self.logger.info("Authentication successful")
                return True
            else:
                error_msg = auth_result.get("message", "Authentication failed") if auth_result else "No response"
                self.logger.error(f"Authentication failed: {error_msg}")
                if self.on_error:
                    self.on_error(f"Authentication failed: {error_msg}")
                return False
        
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            if self.on_error:
                self.on_error(f"Authentication error: {e}")
            return False
    
    def send_file(self, file_path: str) -> bool:
        """
        Send a file to the server
        
        Args:
            file_path (str): Path to the file to send
            
        Returns:
            bool: True if transfer successful, False otherwise
        """
        try:
            # Validate file path
            is_valid, error_msg = validate_file_path(file_path)
            if not is_valid:
                self.logger.error(f"Invalid file path: {error_msg}")
                if self.on_error:
                    self.on_error(f"Invalid file: {error_msg}")
                return False
            
            # Get file information
            file_path_obj = Path(file_path)
            filename = file_path_obj.name
            file_size = file_path_obj.stat().st_size
            
            # Calculate file hash
            self.logger.info(f"Calculating hash for {filename}...")
            file_hash = calculate_file_hash(file_path)
            
            if not file_hash:
                self.logger.error("Failed to calculate file hash")
                if self.on_error:
                    self.on_error("Failed to calculate file hash")
                return False
            
            # Send file metadata
            metadata = {
                "type": "file_metadata",
                "filename": filename,
                "size": file_size,
                "hash": file_hash
            }
            self._send_message(metadata)
            
            # Wait for server ready signal
            ready_response = self._receive_message()
            if not ready_response or ready_response.get("type") != "ready_for_transfer":
                error_msg = ready_response.get("message", "Server not ready") if ready_response else "No response"
                self.logger.error(f"Server not ready: {error_msg}")
                if self.on_error:
                    self.on_error(f"Server error: {error_msg}")
                return False
            
            # Send file data
            self.logger.info(f"Starting file transfer: {filename} ({format_file_size(file_size)})")
            sent_size = 0
            
            with open(file_path, 'rb') as f:
                while sent_size < file_size:
                    # Calculate chunk size
                    remaining = file_size - sent_size
                    chunk_size = min(CHUNK_SIZE, remaining)
                    
                    # Read and send chunk
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    
                    self.client_socket.send(chunk)
                    sent_size += len(chunk)
                    
                    # Update progress
                    if self.on_transfer_progress:
                        progress = (sent_size / file_size) * 100
                        self.on_transfer_progress(progress, sent_size, file_size)
            
            # Wait for transfer result
            result = self._receive_message()
            
            if result and result.get("type") == "transfer_success":
                self.logger.info(f"File sent successfully: {filename}")
                log_transfer(self.logger, filename, file_size, "SENT", "SUCCESS")
                
                if self.on_transfer_complete:
                    self.on_transfer_complete(filename, file_size, True)
                
                return True
            else:
                error_msg = result.get("message", "Transfer failed") if result else "No response"
                self.logger.error(f"File transfer failed: {error_msg}")
                log_transfer(self.logger, filename, file_size, "SENT", "FAILED")
                
                if self.on_transfer_complete:
                    self.on_transfer_complete(filename, file_size, False)
                
                if self.on_error:
                    self.on_error(f"Transfer failed: {error_msg}")
                
                return False
        
        except Exception as e:
            self.logger.error(f"Error sending file: {e}")
            if self.on_error:
                self.on_error(f"Send error: {e}")
            return False
    
    def _send_message(self, message: dict) -> None:
        """
        Send a JSON message to server
        
        Args:
            message (dict): Message to send
        """
        try:
            message_str = json.dumps(message)
            message_bytes = message_str.encode('utf-8')
            
            # Send message length first
            length = len(message_bytes)
            self.client_socket.send(length.to_bytes(4, byteorder='big'))
            
            # Send message
            self.client_socket.send(message_bytes)
            
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            raise
    
    def _receive_message(self) -> Optional[dict]:
        """
        Receive a JSON message from server
        
        Returns:
            Optional[dict]: Received message or None if error
        """
        try:
            # Receive message length
            length_bytes = self.client_socket.recv(4)
            if not length_bytes:
                return None
            
            length = int.from_bytes(length_bytes, byteorder='big')
            
            # Receive message
            message_bytes = b''
            while len(message_bytes) < length:
                chunk = self.client_socket.recv(min(length - len(message_bytes), BUFFER_SIZE))
                if not chunk:
                    return None
                message_bytes += chunk
            
            # Parse JSON message
            message_str = message_bytes.decode('utf-8')
            return json.loads(message_str)
            
        except Exception as e:
            self.logger.error(f"Error receiving message: {e}")
            return None
    
    def disconnect(self) -> None:
        """
        Disconnect from the server
        """
        if self.client_socket:
            try:
                self.client_socket.close()
                self.logger.info("Disconnected from server")
            except Exception as e:
                self.logger.error(f"Error closing connection: {e}")
            finally:
                self.client_socket = None


class FileTransferSession:
    """
    High-level interface for file transfer operations
    """
    
    def __init__(self, password: str = DEFAULT_PASSWORD):
        """
        Initialize the file transfer session
        
        Args:
            password (str): Pre-shared password for authentication
        """
        self.client = FileTransferClient(password)
        self.connected = False
    
    def connect_and_send_file(self, server_ip: str, server_port: int, 
                            file_path: str, timeout: int = 10) -> bool:
        """
        Connect to server and send a file in one operation
        
        Args:
            server_ip (str): Server IP address
            server_port (int): Server port
            file_path (str): Path to file to send
            timeout (int): Connection timeout
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Connect to server
            if not self.client.connect_to_server(server_ip, server_port, timeout):
                return False
            
            # Authenticate
            if not self.client.authenticate():
                return False
            
            # Send file
            success = self.client.send_file(file_path)
            
            return success
        
        except Exception as e:
            self.client.logger.error(f"Session error: {e}")
            return False
        
        finally:
            # Always disconnect
            self.client.disconnect()
    
    def set_callbacks(self, on_connected: Optional[Callable] = None,
                     on_progress: Optional[Callable] = None,
                     on_complete: Optional[Callable] = None,
                     on_error: Optional[Callable] = None) -> None:
        """
        Set callback functions for GUI updates
        
        Args:
            on_connected: Called when connected to server
            on_progress: Called with progress updates (progress, sent, total)
            on_complete: Called when transfer completes (filename, size, success)
            on_error: Called when an error occurs (error_message)
        """
        self.client.on_connected = on_connected
        self.client.on_transfer_progress = on_progress
        self.client.on_transfer_complete = on_complete
        self.client.on_error = on_error


# Convenience functions
def send_file_to_server(server_ip: str, server_port: int, file_path: str,
                       password: str = DEFAULT_PASSWORD) -> bool:
    """
    Convenience function to send a file to a server
    
    Args:
        server_ip (str): Server IP address
        server_port (int): Server port
        file_path (str): Path to file to send
        password (str): Authentication password
        
    Returns:
        bool: True if successful, False otherwise
    """
    session = FileTransferSession(password)
    return session.connect_and_send_file(server_ip, server_port, file_path)
