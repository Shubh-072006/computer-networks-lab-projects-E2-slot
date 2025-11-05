"""
Main entry point for the LAN File Transfer System
Provides command-line interface to run server or client
"""

import argparse
import sys
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from gui_server import ServerGUI
from gui_client import ClientGUI
from server import FileTransferServer
from client import FileTransferSession
from discovery import discover_servers
from utils import setup_logging


def run_server_gui():
    """Run the server GUI"""
    print("Starting LAN File Transfer Server...")
    app = ServerGUI()
    app.run()


def run_client_gui():
    """Run the client GUI"""
    print("Starting LAN File Transfer Client...")
    app = ClientGUI()
    app.run()


def run_server_cli(port: int = 8888, password: str = "lan_transfer_2024", 
                   receive_dir: str = "received_files", enable_discovery: bool = True):
    """Run the server in command-line mode"""
    logger = setup_logging()
    
    print(f"Starting LAN File Transfer Server on port {port}")
    print(f"Receive directory: {receive_dir}")
    print(f"Discovery enabled: {enable_discovery}")
    print("Press Ctrl+C to stop the server")
    
    server = FileTransferServer(port, password, receive_dir)
    
    try:
        if server.start_server(enable_discovery):
            print("Server started successfully!")
            print("Waiting for connections...")
            
            # Keep the server running
            import time
            while True:
                time.sleep(1)
        else:
            print("Failed to start server")
            return 1
    
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.stop_server()
        print("Server stopped")
        return 0
    
    except Exception as e:
        print(f"Server error: {e}")
        server.stop_server()
        return 1


def run_client_cli(server_ip: str, server_port: int, file_path: str, 
                   password: str = "lan_transfer_2024"):
    """Run the client in command-line mode"""
    logger = setup_logging()
    
    print(f"Connecting to server {server_ip}:{server_port}")
    print(f"Sending file: {file_path}")
    
    session = FileTransferSession(password)
    
    # Set up progress callback
    def on_progress(progress, sent, total):
        print(f"\rProgress: {progress:.1f}% ({sent}/{total} bytes)", end="", flush=True)
    
    def on_complete(filename, size, success):
        if success:
            print(f"\nFile sent successfully: {filename}")
        else:
            print(f"\nFailed to send file: {filename}")
    
    def on_error(error_message):
        print(f"\nError: {error_message}")
    
    session.set_callbacks(on_progress=on_progress, on_complete=on_complete, on_error=on_error)
    
    success = session.connect_and_send_file(server_ip, server_port, file_path)
    return 0 if success else 1


def discover_servers_cli():
    """Discover and list available servers"""
    print("Discovering servers on the network...")
    
    servers = discover_servers()
    
    if servers:
        print(f"Found {len(servers)} server(s):")
        for i, (ip, port) in enumerate(servers, 1):
            print(f"  {i}. {ip}:{port}")
    else:
        print("No servers found on the network")
    
    return 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="LAN File Transfer System - Cross-platform file transfer for local networks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run server GUI
  python main.py server-gui
  
  # Run client GUI
  python main.py client-gui
  
  # Run server in CLI mode
  python main.py server-cli --port 8888 --password mypassword
  
  # Send file via CLI
  python main.py client-cli --server 192.168.1.100 --port 8888 --file /path/to/file.txt
  
  # Discover servers
  python main.py discover
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Server GUI command
    server_gui_parser = subparsers.add_parser('server-gui', help='Run server with GUI')
    
    # Client GUI command
    client_gui_parser = subparsers.add_parser('client-gui', help='Run client with GUI')
    
    # Server CLI command
    server_cli_parser = subparsers.add_parser('server-cli', help='Run server in command-line mode')
    server_cli_parser.add_argument('--port', type=int, default=8888, help='Server port (default: 8888)')
    server_cli_parser.add_argument('--password', default='lan_transfer_2024', help='Authentication password')
    server_cli_parser.add_argument('--receive-dir', default='received_files', help='Directory to save received files')
    server_cli_parser.add_argument('--no-discovery', action='store_true', help='Disable discovery service')
    
    # Client CLI command
    client_cli_parser = subparsers.add_parser('client-cli', help='Send file via command-line')
    client_cli_parser.add_argument('--server', required=True, help='Server IP address')
    client_cli_parser.add_argument('--port', type=int, default=8888, help='Server port (default: 8888)')
    client_cli_parser.add_argument('--file', required=True, help='File to send')
    client_cli_parser.add_argument('--password', default='lan_transfer_2024', help='Authentication password')
    
    # Discover command
    discover_parser = subparsers.add_parser('discover', help='Discover available servers')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == 'server-gui':
            return run_server_gui()
        elif args.command == 'client-gui':
            return run_client_gui()
        elif args.command == 'server-cli':
            return run_server_cli(
                port=args.port,
                password=args.password,
                receive_dir=args.receive_dir,
                enable_discovery=not args.no_discovery
            )
        elif args.command == 'client-cli':
            return run_client_cli(
                server_ip=args.server,
                server_port=args.port,
                file_path=args.file,
                password=args.password
            )
        elif args.command == 'discover':
            return discover_servers_cli()
        else:
            parser.print_help()
            return 1
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
