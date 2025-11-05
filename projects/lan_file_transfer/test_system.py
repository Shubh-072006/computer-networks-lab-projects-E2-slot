"""
Test script for the LAN File Transfer System
Demonstrates basic functionality and creates test files
"""

import os
import tempfile
import time
import threading
from pathlib import Path

from server import FileTransferServer
from client import FileTransferSession
from discovery import DiscoveryService


def create_test_file(size_kb: int = 100) -> str:
    """
    Create a test file with specified size
    
    Args:
        size_kb (int): Size of test file in KB
        
    Returns:
        str: Path to created test file
    """
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
    
    # Write test data
    test_data = "This is test data for LAN file transfer system. " * 20
    data_size = len(test_data.encode('utf-8'))
    
    # Calculate how many repetitions needed
    repetitions = (size_kb * 1024) // data_size
    
    for _ in range(repetitions):
        temp_file.write(test_data.encode('utf-8'))
    
    temp_file.close()
    
    print(f"Created test file: {temp_file.name} ({size_kb}KB)")
    return temp_file.name


def test_server_client_transfer():
    """
    Test file transfer between server and client
    """
    print("=== LAN File Transfer System Test ===")
    print()
    
    # Create test file
    test_file = create_test_file(50)  # 50KB test file
    
    try:
        # Create server
        print("Starting test server...")
        server = FileTransferServer(port=8888, password="test_password", receive_dir="test_received")
        
        # Start server in separate thread
        server_thread = threading.Thread(target=server.start_server)
        server_thread.daemon = True
        server_thread.start()
        
        # Wait for server to start
        time.sleep(2)
        
        # Create client session
        print("Creating client session...")
        session = FileTransferSession("test_password")
        
        # Set up progress callback
        def on_progress(progress, sent, total):
            print(f"\rTransfer progress: {progress:.1f}%", end="", flush=True)
        
        def on_complete(filename, size, success):
            if success:
                print(f"\n✓ File transfer completed successfully!")
                print(f"  File: {filename}")
                print(f"  Size: {size} bytes")
            else:
                print(f"\n✗ File transfer failed!")
        
        def on_error(error_message):
            print(f"\n✗ Error: {error_message}")
        
        session.set_callbacks(on_progress=on_progress, on_complete=on_complete, on_error=on_error)
        
        # Send file
        print("Sending test file...")
        success = session.connect_and_send_file("127.0.0.1", 8888, test_file)
        
        if success:
            print("✓ Test completed successfully!")
            
            # Check if file was received
            received_file = Path("test_received") / Path(test_file).name
            if received_file.exists():
                print(f"✓ File received at: {received_file}")
                
                # Compare file sizes
                original_size = Path(test_file).stat().st_size
                received_size = received_file.stat().st_size
                
                if original_size == received_size:
                    print("✓ File sizes match - integrity verified!")
                else:
                    print(f"✗ File size mismatch: {original_size} vs {received_size}")
            else:
                print("✗ Received file not found")
        else:
            print("✗ Test failed!")
        
        # Stop server
        print("Stopping server...")
        server.stop_server()
        
    except Exception as e:
        print(f"✗ Test error: {e}")
    
    finally:
        # Cleanup
        try:
            os.unlink(test_file)
            print(f"Cleaned up test file: {test_file}")
        except:
            pass


def test_discovery():
    """
    Test server discovery functionality
    """
    print("\n=== Discovery Test ===")
    
    try:
        # Start discovery service
        print("Starting discovery service...")
        discovery_service = DiscoveryService(8888)
        discovery_service.start_server_discovery()
        
        # Wait a moment
        time.sleep(1)
        
        # Test discovery
        print("Testing discovery...")
        from discovery import discover_servers
        servers = discover_servers(timeout=3)
        
        if servers:
            print(f"✓ Found {len(servers)} server(s):")
            for ip, port in servers:
                print(f"  - {ip}:{port}")
        else:
            print("No servers found (expected in test environment)")
        
        # Stop discovery service
        discovery_service.stop_discovery_server()
        print("Discovery service stopped")
        
    except Exception as e:
        print(f"✗ Discovery test error: {e}")


def main():
    """
    Run all tests
    """
    print("LAN File Transfer System - Test Suite")
    print("=" * 50)
    
    # Test discovery
    test_discovery()
    
    # Test file transfer
    test_server_client_transfer()
    
    print("\n" + "=" * 50)
    print("Test suite completed!")


if __name__ == "__main__":
    main()
