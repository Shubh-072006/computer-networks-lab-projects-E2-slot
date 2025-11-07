"""
Demo script for the LAN File Transfer System
Shows how to use the system programmatically
"""

import time
import threading
from pathlib import Path

from server import FileTransferServer
from client import FileTransferSession
from discovery import discover_servers


def demo_server():
    """
    Demonstrate server functionality
    """
    print("=== Server Demo ===")
    
    # Create server with custom settings
    server = FileTransferServer(
        port=8888,
        password="demo_password",
        receive_dir="demo_received"
    )
    
    # Set up callbacks for monitoring
    def on_client_connected(client_ip):
        print(f"📱 Client connected: {client_ip}")
    
    def on_file_received(filename, size, file_path):
        print(f"📁 File received: {filename} ({size} bytes)")
        print(f"   Saved to: {file_path}")
    
    def on_error(error_message):
        print(f"❌ Error: {error_message}")
    
    server.on_client_connected = on_client_connected
    server.on_file_received = on_file_received
    server.on_error = on_error
    
    # Start server
    print("🚀 Starting server on port 8888...")
    print("   Password: demo_password")
    print("   Receive directory: demo_received")
    
    if server.start_server(enable_discovery=True):
        print("✅ Server started successfully!")
        print("   Discovery service enabled")
        print("   Waiting for connections...")
        
        try:
            # Keep server running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping server...")
            server.stop_server()
            print("✅ Server stopped")
    else:
        print("❌ Failed to start server")


def demo_client():
    """
    Demonstrate client functionality
    """
    print("=== Client Demo ===")
    
    # Discover servers
    print("🔍 Discovering servers...")
    servers = discover_servers(timeout=3)
    
    if not servers:
        print("❌ No servers found. Make sure a server is running.")
        return
    
    print(f"✅ Found {len(servers)} server(s):")
    for i, (ip, port) in enumerate(servers, 1):
        print(f"   {i}. {ip}:{port}")
    
    # Use first server
    server_ip, server_port = servers[0]
    print(f"📡 Connecting to {server_ip}:{server_port}")
    
    # Create test file
    test_file = Path("demo_test.txt")
    test_content = "Hello from LAN File Transfer System!\n" * 100
    test_file.write_text(test_content)
    print(f"📄 Created test file: {test_file} ({test_file.stat().st_size} bytes)")
    
    # Create client session
    session = FileTransferSession("demo_password")
    
    # Set up progress tracking
    def on_connected(ip, port):
        print(f"🔗 Connected to {ip}:{port}")
    
    def on_progress(progress, sent, total):
        print(f"\r📊 Progress: {progress:.1f}% ({sent}/{total} bytes)", end="", flush=True)
    
    def on_complete(filename, size, success):
        if success:
            print(f"\n✅ Transfer completed: {filename}")
        else:
            print(f"\n❌ Transfer failed: {filename}")
    
    def on_error(error_message):
        print(f"\n❌ Error: {error_message}")
    
    session.set_callbacks(
        on_connected=on_connected,
        on_progress=on_progress,
        on_complete=on_complete,
        on_error=on_error
    )
    
    # Send file
    print("📤 Sending file...")
    success = session.connect_and_send_file(server_ip, server_port, str(test_file))
    
    if success:
        print("🎉 Demo completed successfully!")
    else:
        print("💥 Demo failed!")
    
    # Cleanup
    test_file.unlink()
    print(f"🧹 Cleaned up test file")


def main():
    """
    Main demo function
    """
    print("LAN File Transfer System - Demo")
    print("=" * 40)
    print()
    print("This demo shows how to use the system programmatically.")
    print("Choose an option:")
    print("1. Run server demo")
    print("2. Run client demo")
    print("3. Run both (server in background)")
    print()
    
    choice = input("Enter your choice (1-3): ").strip()
    
    if choice == "1":
        demo_server()
    elif choice == "2":
        demo_client()
    elif choice == "3":
        print("🚀 Starting server in background...")
        server_thread = threading.Thread(target=demo_server)
        server_thread.daemon = True
        server_thread.start()
        
        print("⏳ Waiting for server to start...")
        time.sleep(3)
        
        print("📱 Starting client demo...")
        demo_client()
        
        print("🛑 Stopping server...")
        # Server will stop when main thread exits
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    main()
