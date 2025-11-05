"""
UDP Peer Discovery System for LAN File Transfer
Handles automatic server discovery using UDP broadcasts
"""

import socket
import threading
import time
from typing import List, Tuple, Optional

from config import (
    DISCOVERY_PORT, DISCOVERY_TIMEOUT, DISCOVERY_MESSAGE, 
    DISCOVERY_RESPONSE, DEFAULT_PORT
)
from utils import get_local_ip, setup_logging


class DiscoveryService:
    """
    UDP discovery service for finding file transfer servers on the network
    """
    
    def __init__(self, server_port: int = DEFAULT_PORT):
        """
        Initialize the discovery service
        
        Args:
            server_port (int): Port number of the file transfer server
        """
        self.server_port = server_port
        self.logger = setup_logging()
        self.running = False
        self.discovery_socket = None
        self.server_socket = None
        
    def start_server_discovery(self) -> bool:
        """
        Start the discovery server to respond to discovery requests
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        try:
            # Create UDP socket for discovery responses
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.server_socket.bind(('', DISCOVERY_PORT))
            
            self.running = True
            self.logger.info(f"Discovery server started on port {DISCOVERY_PORT}")
            
            # Start listening for discovery requests in a separate thread
            discovery_thread = threading.Thread(target=self._listen_for_discovery)
            discovery_thread.daemon = True
            discovery_thread.start()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start discovery server: {e}")
            return False
    
    def _listen_for_discovery(self) -> None:
        """
        Listen for discovery requests and respond with server information
        """
        while self.running:
            try:
                # Receive discovery request
                data, addr = self.server_socket.recvfrom(1024)
                message = data.decode('utf-8')
                
                # Check if it's a discovery request
                if message == DISCOVERY_MESSAGE:
                    # Send response with server information
                    local_ip = get_local_ip()
                    response = f"{DISCOVERY_RESPONSE}:{local_ip}:{self.server_port}"
                    
                    self.server_socket.sendto(response.encode('utf-8'), addr)
                    self.logger.info(f"Responded to discovery request from {addr[0]}")
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:  # Only log if we're supposed to be running
                    self.logger.error(f"Error in discovery listener: {e}")
    
    def discover_servers(self, timeout: int = DISCOVERY_TIMEOUT) -> List[Tuple[str, int]]:
        """
        Discover available file transfer servers on the network
        
        Args:
            timeout (int): Timeout in seconds for discovery
            
        Returns:
            List[Tuple[str, int]]: List of (ip_address, port) tuples
        """
        servers = []
        
        try:
            # Create UDP socket for discovery requests
            self.discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.discovery_socket.settimeout(timeout)
            
            # Send discovery broadcast
            broadcast_addr = ('255.255.255.255', DISCOVERY_PORT)
            self.discovery_socket.sendto(DISCOVERY_MESSAGE.encode('utf-8'), broadcast_addr)
            
            self.logger.info("Sent discovery broadcast")
            
            # Listen for responses
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    data, addr = self.discovery_socket.recvfrom(1024)
                    message = data.decode('utf-8')
                    
                    # Parse server response
                    if message.startswith(DISCOVERY_RESPONSE):
                        parts = message.split(':')
                        if len(parts) >= 3:
                            server_ip = parts[1]
                            server_port = int(parts[2])
                            
                            # Add server to list (including local server for web interface)
                            servers.append((server_ip, server_port))
                            self.logger.info(f"Discovered server: {server_ip}:{server_port}")
                
                except socket.timeout:
                    break
                except Exception as e:
                    self.logger.error(f"Error receiving discovery response: {e}")
                    break
            
            self.logger.info(f"Discovery completed. Found {len(servers)} servers")
            
        except Exception as e:
            self.logger.error(f"Error during server discovery: {e}")
        
        finally:
            if self.discovery_socket:
                self.discovery_socket.close()
                self.discovery_socket = None
        
        return servers
    
    def stop_discovery_server(self) -> None:
        """
        Stop the discovery server
        """
        self.running = False
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                self.logger.error(f"Error closing discovery server socket: {e}")
            finally:
                self.server_socket = None
        
        self.logger.info("Discovery server stopped")


class DiscoveryClient:
    """
    Client for discovering file transfer servers
    """
    
    def __init__(self):
        """Initialize the discovery client"""
        self.logger = setup_logging()
    
    def find_servers(self, timeout: int = DISCOVERY_TIMEOUT) -> List[Tuple[str, int]]:
        """
        Find available file transfer servers
        
        Args:
            timeout (int): Timeout in seconds for discovery
            
        Returns:
            List[Tuple[str, int]]: List of (ip_address, port) tuples
        """
        discovery_service = DiscoveryService()
        return discovery_service.discover_servers(timeout)
    
    def get_server_list(self) -> List[str]:
        """
        Get a formatted list of discovered servers
        
        Returns:
            List[str]: List of formatted server strings
        """
        servers = self.find_servers()
        server_list = []
        
        for ip, port in servers:
            server_list.append(f"{ip}:{port}")
        
        return server_list


# Convenience functions for easy usage
def discover_servers(timeout: int = DISCOVERY_TIMEOUT) -> List[Tuple[str, int]]:
    """
    Convenience function to discover servers
    
    Args:
        timeout (int): Timeout in seconds
        
    Returns:
        List[Tuple[str, int]]: List of (ip_address, port) tuples
    """
    client = DiscoveryClient()
    return client.find_servers(timeout)


def start_discovery_server(server_port: int = DEFAULT_PORT) -> DiscoveryService:
    """
    Convenience function to start a discovery server
    
    Args:
        server_port (int): Port of the file transfer server
        
    Returns:
        DiscoveryService: Started discovery service
    """
    service = DiscoveryService(server_port)
    service.start_server_discovery()
    return service
