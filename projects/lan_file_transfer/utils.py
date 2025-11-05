"""
Utility functions for the LAN File Transfer System
Contains helper functions for file operations, networking, and security
"""

import hashlib
import logging
import os
import socket
import time
from pathlib import Path
from typing import Optional, Tuple

from config import BUFFER_SIZE, LOG_FORMAT, LOG_FILE


def setup_logging() -> logging.Logger:
    """
    Set up logging configuration for the application
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger('lan_file_transfer')
    logger.setLevel(logging.INFO)
    
    # Create file handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.INFO)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def calculate_file_hash(file_path: str) -> str:
    """
    Calculate MD5 hash of a file for integrity verification
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: MD5 hash of the file
    """
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logging.error(f"Error calculating hash for {file_path}: {e}")
        return ""


def get_local_ip() -> str:
    """
    Get the local IP address of the machine
    
    Returns:
        str: Local IP address
    """
    try:
        # Connect to a remote address to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        return local_ip
    except Exception:
        # Fallback to localhost
        return "127.0.0.1"


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format
    
    Args:
        size_bytes (int): File size in bytes
        
    Returns:
        str: Formatted file size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def validate_file_path(file_path: str) -> Tuple[bool, str]:
    """
    Validate if a file path is accessible and safe
    
    Args:
        file_path (str): Path to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    try:
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            return False, "File does not exist"
        
        # Check if it's a file (not directory)
        if not path.is_file():
            return False, "Path is not a file"
        
        # Check if file is readable
        if not os.access(file_path, os.R_OK):
            return False, "File is not readable"
        
        return True, ""
    
    except Exception as e:
        return False, f"Error validating file: {str(e)}"


def create_safe_filename(filename: str) -> str:
    """
    Create a safe filename by removing or replacing invalid characters
    
    Args:
        filename (str): Original filename
        
    Returns:
        str: Safe filename
    """
    # Characters that are not allowed in filenames
    invalid_chars = '<>:"/\\|?*'
    
    # Replace invalid characters with underscores
    safe_filename = filename
    for char in invalid_chars:
        safe_filename = safe_filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    safe_filename = safe_filename.strip(' .')
    
    # Ensure filename is not empty
    if not safe_filename:
        safe_filename = "unnamed_file"
    
    return safe_filename


def get_available_port(start_port: int = 8888, max_attempts: int = 10) -> Optional[int]:
    """
    Find an available port starting from the given port
    
    Args:
        start_port (int): Starting port number
        max_attempts (int): Maximum number of ports to try
        
    Returns:
        Optional[int]: Available port number or None if none found
    """
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    
    return None


def log_transfer(logger: logging.Logger, filename: str, size: int, 
                direction: str, status: str, client_ip: str = "") -> None:
    """
    Log file transfer information
    
    Args:
        logger (logging.Logger): Logger instance
        filename (str): Name of the transferred file
        size (int): File size in bytes
        direction (str): "SENT" or "RECEIVED"
        status (str): Transfer status (SUCCESS, FAILED, etc.)
        client_ip (str): IP address of the client
    """
    size_str = format_file_size(size)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    log_message = f"{direction} {filename} ({size_str}) - {status}"
    if client_ip:
        log_message += f" from/to {client_ip}"
    
    logger.info(log_message)
