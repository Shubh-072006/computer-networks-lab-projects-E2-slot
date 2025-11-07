# Usage Guide - Multiple Ways to Use the System

## Method 1: GUI Interface (Easiest)

### Server GUI
```bash
python main.py server-gui
```
- **Visual interface** for server management
- **Real-time logs** and client connections
- **Easy configuration** of port, password, receive directory
- **Start/stop server** with buttons

### Client GUI
```bash
python main.py client-gui
```
- **Server discovery** with one click
- **File browser** to select files
- **Progress bar** showing transfer status
- **Transfer logs** and error messages

## Method 2: Command Line Interface

### Start Server
```bash
# Basic server
python main.py server-cli

# Custom configuration
python main.py server-cli --port 9999 --password mypassword --receive-dir /path/to/receive
```

### Send File
```bash
# Send to discovered server
python main.py client-cli --server 192.168.1.100 --port 8888 --file /path/to/file.txt

# With custom password
python main.py client-cli --server 192.168.1.100 --port 8888 --file /path/to/file.txt --password mypassword
```

### Discover Servers
```bash
python main.py discover
```

## Method 3: Programmatic API

### Server Example
```python
from server import FileTransferServer

# Create server
server = FileTransferServer(port=8888, password="mypassword", receive_dir="received")

# Set callbacks
def on_file_received(filename, size, file_path):
    print(f"Received: {filename} ({size} bytes)")

server.on_file_received = on_file_received

# Start server
server.start_server(enable_discovery=True)
```

### Client Example
```python
from client import FileTransferSession

# Create session
session = FileTransferSession("mypassword")

# Set callbacks
def on_progress(progress, sent, total):
    print(f"Progress: {progress:.1f}%")

session.set_callbacks(on_progress=on_progress)

# Send file
success = session.connect_and_send_file("192.168.1.100", 8888, "/path/to/file.txt")
```

## Method 4: Demo Script
```bash
python demo.py
```
- **Interactive demo** with options
- **Automatic testing** of server and client
- **Creates test files** and demonstrates functionality

## Method 5: Test Suite
```bash
python test_system.py
```
- **Automated testing** of all components
- **Creates temporary files** for testing
- **Verifies file integrity** and transfer success
