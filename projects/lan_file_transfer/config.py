"""
Configuration settings for the LAN File Transfer System
Contains all configurable parameters for the application
"""

import os
from pathlib import Path

# Network Configuration
DEFAULT_PORT = 8888  # TCP port for file transfers
DISCOVERY_PORT = 8889  # UDP port for peer discovery
DISCOVERY_TIMEOUT = 5  # Seconds to wait for discovery responses
BUFFER_SIZE = 4096  # Buffer size for file transfers

# Security Configuration
DEFAULT_PASSWORD = "lan_transfer_2024"  # Default pre-shared password
PASSWORD_LENGTH = 20  # Maximum password length

# File Transfer Configuration
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB maximum file size
CHUNK_SIZE = 1024  # Size of each data chunk during transfer

# GUI Configuration
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 500
PROGRESS_BAR_LENGTH = 300

# Logging Configuration
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "transfer_log.txt"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# Create log directory if it doesn't exist
LOG_DIR.mkdir(exist_ok=True)

# File Overwrite Configuration
OVERWRITE_PROMPT = True  # Whether to prompt before overwriting files

# Discovery Configuration
DISCOVERY_MESSAGE = "LAN_FILE_TRANSFER_DISCOVERY"
DISCOVERY_RESPONSE = "LAN_FILE_TRANSFER_SERVER"
