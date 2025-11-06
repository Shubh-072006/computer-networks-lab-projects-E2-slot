#!/usr/bin/env python3
"""
TCP/IP Chat Server with Matrix Operations
Handles multiple clients, message broadcasting, and matrix file processing
"""

import socket
import threading
import json
import os
from datetime import datetime
from matrix_operations import MatrixProcessor
import numpy as np

class ChatServer:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.clients = {}  # {socket: {'username': str, 'address': tuple}}
        self.matrix_processor = MatrixProcessor()
        self.server_socket = None
        
    def start_server(self):
        """Start the TCP server and listen for connections"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            print(f"🚀 Chat server started on {self.host}:{self.port}")
            print("Waiting for clients to connect...")
            
            while True:
                client_socket, client_address = self.server_socket.accept()
                print(f"📱 New connection from {client_address}")
                
                # Start a new thread for each client
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address)
                )
                client_thread.daemon = True
                client_thread.start()
                
        except Exception as e:
            print(f"❌ Server error: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
    
    def handle_client(self, client_socket, client_address):
        """Handle individual client connections"""
        username = None
        buffer = ""
        try:
            while True:
                # Receive data from client (may contain partial or multiple JSON messages)
                chunk = client_socket.recv(4096).decode('utf-8')
                if not chunk:
                    break
                buffer += chunk

                # Process complete lines (newline-delimited JSON)
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if not line.strip():
                        continue
                    try:
                        message = json.loads(line)
                    except json.JSONDecodeError:
                        # Incomplete JSON, wait for more data
                        buffer = line + "\n" + buffer
                        break

                    message_type = message.get('type')
                    if message_type == 'join':
                        username = message.get('username')
                        if self.handle_user_join(client_socket, client_address, username):
                            self.broadcast_message({
                                'type': 'system',
                                'message': f"👋 {username} joined the chat",
                                'timestamp': datetime.now().strftime('%H:%M:%S')
                            }, exclude_client=client_socket)

                    elif message_type == 'chat':
                        if client_socket in self.clients:
                            self.handle_chat_message(client_socket, message)

                    elif message_type == 'matrix_file':
                        if client_socket in self.clients:
                            self.handle_matrix_file(client_socket, message)

                    elif message_type == 'matrix_operation':
                        if client_socket in self.clients:
                            self.handle_matrix_operation(client_socket, message)
        except Exception as e:
            print(f"❌ Error handling client {client_address}: {e}")
        finally:
            self.disconnect_client(client_socket, username)
    
    def handle_user_join(self, client_socket, client_address, username):
        """Handle user joining the chat"""
        if not username:
            self.send_to_client(client_socket, {
                'type': 'error',
                'message': 'Username is required'
            })
            return False
        
        # Check if username is already taken
        for client_info in self.clients.values():
            if client_info['username'] == username:
                self.send_to_client(client_socket, {
                    'type': 'error',
                    'message': 'Username already taken'
                })
                return False
        
        # Add client to the list
        self.clients[client_socket] = {
            'username': username,
            'address': client_address
        }
        
        # Send welcome message
        self.send_to_client(client_socket, {
            'type': 'system',
            'message': f'Welcome to the chat, {username}! 🎉',
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })
        
        # Send user list
        user_list = [client_info['username'] for client_info in self.clients.values()]
        self.send_to_client(client_socket, {
            'type': 'user_list',
            'users': user_list
        })
        
        print(f"✅ {username} ({client_address}) joined the chat")
        return True
    
    def handle_chat_message(self, client_socket, message):
        """Handle regular chat messages"""
        username = self.clients[client_socket]['username']
        chat_message = {
            'type': 'chat',
            'username': username,
            'message': message.get('message', ''),
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }
        self.broadcast_message(chat_message)
        print(f"💬 {username}: {message.get('message', '')}")
    
    def handle_matrix_file(self, client_socket, message):
        """Handle matrix file uploads and processing"""
        username = self.clients[client_socket]['username']
        matrix_data = message.get('matrix_data')
        operation = message.get('operation', 'display')
        
        try:
            result = self.matrix_processor.process_matrix_data(matrix_data, operation)
            
            response = {
                'type': 'matrix_result',
                'username': username,
                'operation': operation,
                'result': result,
                'timestamp': datetime.now().strftime('%H:%M:%S')
            }
            
            self.broadcast_message(response)
            print(f"🔢 {username} performed matrix operation: {operation}")
            
        except Exception as e:
            error_response = {
                'type': 'error',
                'message': f'Matrix operation failed: {str(e)}'
            }
            self.send_to_client(client_socket, error_response)
    
    def handle_matrix_operation(self, client_socket, message):
        """Handle specific matrix operations requested by users"""
        username = self.clients[client_socket]['username']
        operation = message.get('operation')
        matrices = message.get('matrices', [])
        matrix_data_text = message.get('matrix_data')
        
        # If no explicit list provided but text is, parse it
        if (not matrices or len(matrices) == 0) and matrix_data_text:
            try:
                matrices = self.matrix_processor.parse_matrix_data(matrix_data_text)
            except Exception as e:
                self.send_to_client(client_socket, {
                    'type': 'error',
                    'message': f'Failed to parse matrices: {e}'
                })
                return
        
        # Debug: incoming types
        try:
            print(f"🔎 Received op='{operation}' with matrix types: {[type(m).__name__ for m in matrices]}")
        except Exception:
            pass
        
        # Coerce incoming lists/arrays to NumPy arrays for safety
        try:
            matrices_np = [m if isinstance(m, np.ndarray) else np.array(m) for m in matrices]
        except Exception:
            matrices_np = matrices
        
        # Debug: coerced types and shapes
        try:
            shapes = []
            for m in matrices_np:
                try:
                    shapes.append(getattr(m, 'shape', None))
                except Exception:
                    shapes.append(None)
            print(f"🔧 Coerced matrix types: {[type(m).__name__ for m in matrices_np]} shapes={shapes}")
        except Exception:
            pass
        
        try:
            result = self.matrix_processor.perform_operation(operation, matrices_np)
            
            response = {
                'type': 'matrix_result',
                'username': username,
                'operation': operation,
                'result': result,
                'timestamp': datetime.now().strftime('%H:%M:%S')
            }
            
            self.broadcast_message(response)
            print(f"🔢 {username} performed operation: {operation}")
            
        except Exception as e:
            error_response = {
                'type': 'error',
                'message': f'Operation failed: {str(e)}'
            }
            self.send_to_client(client_socket, error_response)
    
    def send_to_client(self, client_socket, message):
        """Send message to a specific client"""
        try:
            # Delimit JSON messages with a newline for safe streaming
            client_socket.send((json.dumps(message) + "\n").encode('utf-8'))
        except Exception as e:
            print(f"❌ Failed to send message to client: {e}")
    
    def broadcast_message(self, message, exclude_client=None):
        """Broadcast message to all connected clients"""
        disconnected_clients = []
        
        for client_socket in list(self.clients.keys()):
            if client_socket != exclude_client:
                try:
                    self.send_to_client(client_socket, message)
                except Exception as e:
                    print(f"❌ Failed to send to client: {e}")
                    disconnected_clients.append(client_socket)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            self.disconnect_client(client, None)
    
    def disconnect_client(self, client_socket, username=None):
        """Handle client disconnection"""
        if client_socket in self.clients:
            if not username:
                username = self.clients[client_socket]['username']
            
            del self.clients[client_socket]
            
            # Notify other clients
            self.broadcast_message({
                'type': 'system',
                'message': f"👋 {username} left the chat",
                'timestamp': datetime.now().strftime('%H:%M:%S')
            })
            
            print(f"📤 {username} disconnected")
        
        try:
            client_socket.close()
        except:
            pass

def main():
    server = ChatServer()
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\n🛑 Server shutting down...")
    finally:
        if server.server_socket:
            server.server_socket.close()

if __name__ == "__main__":
    main()
