"""
TCP Server for LAN File Transfer System
Handles file transfers with security, progress tracking, and integrity verification
"""

import hashlib
import json
import os
import socket
import threading
import time
from pathlib import Path
from typing import Optional, Callable

from config import (
    DEFAULT_PORT, BUFFER_SIZE, MAX_FILE_SIZE, CHUNK_SIZE,
    DEFAULT_PASSWORD, OVERWRITE_PROMPT
)
from utils import (
    setup_logging, calculate_file_hash, format_file_size,
    create_safe_filename, log_transfer, get_available_port
)
from discovery import DiscoveryService


class FileTransferServer:
    """
    TCP server for handling file transfers with security and integrity checks
    """
    
    def __init__(self, port: int = DEFAULT_PORT, password: str = DEFAULT_PASSWORD,
                 receive_dir: str = "received_files"):
        """
        Initialize the file transfer server
        
        Args:
            port (int): Port to listen on
            password (str): Pre-shared password for authentication
            receive_dir (str): Directory to save received files
        """
        self.port = port
        self.password = password
        self.receive_dir = Path(receive_dir)
        self.logger = setup_logging()
        self.server_socket = None
        self.running = False
        self.discovery_service = None
        
        # Create receive directory if it doesn't exist
        self.receive_dir.mkdir(exist_ok=True)
        
        # Callbacks for GUI updates
        self.on_client_connected: Optional[Callable] = None
        self.on_file_received: Optional[Callable] = None
        self.on_transfer_progress: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
    
    def start_server(self, enable_discovery: bool = True) -> bool:
        """
        Start the file transfer server
        
        Args:
            enable_discovery (bool): Whether to enable UDP discovery
            
        Returns:
            bool: True if started successfully, False otherwise
        """
        try:
            # Find available port if default is taken
            if not self._is_port_available(self.port):
                self.port = get_available_port(self.port)
                if not self.port:
                    self.logger.error("No available ports found")
                    return False
            
            # Create server socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('', self.port))
            self.server_socket.listen(5)
            
            self.running = True
            self.logger.info(f"File transfer server started on port {self.port}")
            
            # Start discovery service if enabled
            if enable_discovery:
                self.discovery_service = DiscoveryService(self.port)
                self.discovery_service.start_server_discovery()
                self.logger.info("Discovery service enabled")
            
            # Start accepting connections in a separate thread
            accept_thread = threading.Thread(target=self._accept_connections)
            accept_thread.daemon = True
            accept_thread.start()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            if self.on_error:
                self.on_error(f"Failed to start server: {e}")
            return False
    
    def _is_port_available(self, port: int) -> bool:
        """
        Check if a port is available
        
        Args:
            port (int): Port to check
            
        Returns:
            bool: True if port is available, False otherwise
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return True
        except OSError:
            return False
    
    def _accept_connections(self) -> None:
        """
        Accept incoming client connections
        """
        while self.running:
            try:
                client_socket, client_addr = self.server_socket.accept()
                self.logger.info(f"Client connected from {client_addr[0]}:{client_addr[1]}")
                
                if self.on_client_connected:
                    self.on_client_connected(client_addr[0])
                
                # Handle client in a separate thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, client_addr)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except Exception as e:
                if self.running:
                    self.logger.error(f"Error accepting connection: {e}")
    
    def _handle_client(self, client_socket: socket.socket, client_addr: tuple) -> None:
        """
        Handle a connected client
        
        Args:
            client_socket (socket.socket): Client socket
            client_addr (tuple): Client address
        """
        try:
            # Authenticate client
            if not self._authenticate_client(client_socket):
                self.logger.warning(f"Authentication failed for {client_addr[0]}")
                client_socket.close()
                return
            
            # Handle file transfer
            self._handle_file_transfer(client_socket, client_addr)
            
        except Exception as e:
            self.logger.error(f"Error handling client {client_addr[0]}: {e}")
            if self.on_error:
                self.on_error(f"Error handling client: {e}")
        finally:
            client_socket.close()
    
    def _authenticate_client(self, client_socket: socket.socket) -> bool:
        """
        Authenticate client using pre-shared password
        
        Args:
            client_socket (socket.socket): Client socket
            
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            # Send authentication request
            auth_request = {"type": "auth_request"}
            self._send_message(client_socket, auth_request)
            
            # Receive password from client
            auth_response = self._receive_message(client_socket)
            
            if auth_response and auth_response.get("type") == "auth_response":
                client_password = auth_response.get("password", "")
                
                if client_password == self.password:
                    # Send success response
                    success_response = {"type": "auth_success"}
                    self._send_message(client_socket, success_response)
                    return True
                else:
                    # Send failure response
                    failure_response = {"type": "auth_failure", "message": "Invalid password"}
                    self._send_message(client_socket, failure_response)
                    return False
            
            return False
            
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return False
    
    def _handle_file_transfer(self, client_socket: socket.socket, client_addr: tuple) -> None:
        """
        Handle file transfer from client
        
        Args:
            client_socket (socket.socket): Client socket
            client_addr (tuple): Client address
        """
        try:
            # Receive file metadata
            metadata = self._receive_message(client_socket)
            
            if not metadata or metadata.get("type") != "file_metadata":
                self.logger.error("Invalid file metadata received")
                return
            
            filename = metadata.get("filename", "")
            file_size = metadata.get("size", 0)
            file_hash = metadata.get("hash", "")
            
            # Validate file size
            if file_size > MAX_FILE_SIZE:
                error_response = {
                    "type": "transfer_error",
                    "message": f"File too large. Maximum size: {format_file_size(MAX_FILE_SIZE)}"
                }
                self._send_message(client_socket, error_response)
                return
            
            # Create safe filename
            safe_filename = create_safe_filename(filename)
            file_path = self.receive_dir / safe_filename
            
            # Check if file exists and handle overwrite
            if file_path.exists() and OVERWRITE_PROMPT:
                # For now, we'll overwrite by default
                # In GUI mode, this would prompt the user
                self.logger.info(f"Overwriting existing file: {safe_filename}")
            
            # Send ready signal
            ready_response = {"type": "ready_for_transfer"}
            self._send_message(client_socket, ready_response)
            
            # Receive file data
            received_size = 0
            hash_md5 = hashlib.md5()
            
            with open(file_path, 'wb') as f:
                while received_size < file_size:
                    # Calculate chunk size
                    remaining = file_size - received_size
                    chunk_size = min(CHUNK_SIZE, remaining)
                    
                    # Receive chunk
                    chunk = client_socket.recv(chunk_size)
                    if not chunk:
                        break
                    
                    # Write chunk to file
                    f.write(chunk)
                    received_size += len(chunk)
                    hash_md5.update(chunk)
                    
                    # Update progress
                    if self.on_transfer_progress:
                        progress = (received_size / file_size) * 100
                        self.on_transfer_progress(progress, received_size, file_size)
            
            # Verify file integrity
            received_hash = hash_md5.hexdigest()
            if received_hash == file_hash:
                # Transfer successful
                success_response = {"type": "transfer_success"}
                self._send_message(client_socket, success_response)
                
                self.logger.info(f"File received successfully: {safe_filename}")
                log_transfer(self.logger, safe_filename, file_size, "RECEIVED", "SUCCESS", client_addr[0])
                
                if self.on_file_received:
                    self.on_file_received(safe_filename, file_size, file_path)
            else:
                # Hash mismatch
                error_response = {
                    "type": "transfer_error",
                    "message": "File integrity check failed"
                }
                self._send_message(client_socket, error_response)
                
                # Remove corrupted file
                if file_path.exists():
                    file_path.unlink()
                
                self.logger.error(f"File integrity check failed for {safe_filename}")
                log_transfer(self.logger, safe_filename, file_size, "RECEIVED", "FAILED - INTEGRITY", client_addr[0])
        
        except Exception as e:
            self.logger.error(f"Error during file transfer: {e}")
            if self.on_error:
                self.on_error(f"File transfer error: {e}")
    
    def _send_message(self, client_socket: socket.socket, message: dict) -> None:
        """
        Send a JSON message to client
        
        Args:
            client_socket (socket.socket): Client socket
            message (dict): Message to send
        """
        try:
            message_str = json.dumps(message)
            message_bytes = message_str.encode('utf-8')
            
            # Send message length first
            length = len(message_bytes)
            client_socket.send(length.to_bytes(4, byteorder='big'))
            
            # Send message
            client_socket.send(message_bytes)
            
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            raise
    
    def _receive_message(self, client_socket: socket.socket) -> Optional[dict]:
        """
        Receive a JSON message from client
        
        Args:
            client_socket (socket.socket): Client socket
            
        Returns:
            Optional[dict]: Received message or None if error
        """
        try:
            # Receive message length
            length_bytes = client_socket.recv(4)
            if not length_bytes:
                return None
            
            length = int.from_bytes(length_bytes, byteorder='big')
            
            # Receive message
            message_bytes = b''
            while len(message_bytes) < length:
                chunk = client_socket.recv(min(length - len(message_bytes), BUFFER_SIZE))
                if not chunk:
                    return None
                message_bytes += chunk
            
            # Parse JSON message
            message_str = message_bytes.decode('utf-8')
            return json.loads(message_str)
            
        except Exception as e:
            self.logger.error(f"Error receiving message: {e}")
            return None
    
    def stop_server(self) -> None:
        """
        Stop the file transfer server
        """
        self.running = False
        
        # Stop discovery service
        if self.discovery_service:
            self.discovery_service.stop_discovery_server()
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                self.logger.error(f"Error closing server socket: {e}")
            finally:
                self.server_socket = None
        
        self.logger.info("File transfer server stopped")
    
    def get_server_info(self) -> dict:
        """
        Get server information
        
        Returns:
            dict: Server information
        """
        return {
            "port": self.port,
            "running": self.running,
            "receive_dir": str(self.receive_dir),
            "discovery_enabled": self.discovery_service is not None
        }
