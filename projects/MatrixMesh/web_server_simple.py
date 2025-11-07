#!/usr/bin/env python3
"""
Web Interface for TCP/IP Matrix Chat
Provides a browser-based UI that connects to the existing chat server
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import socket
import json
import threading
import os
from datetime import datetime
from typing import Any, cast

app = Flask(__name__)
app.config['SECRET_KEY'] = 'matrix_chat_secret_key'
# Use default threading async mode; sufficient for development
socketio = SocketIO(app, cors_allowed_origins="*")

class WebChatClient:
    def __init__(self, web_sid: str, chat_host='localhost', chat_port=12345):
        self.web_sid = web_sid  # Socket.IO session id for the browser client
        self.chat_host = chat_host
        self.chat_port = chat_port
        self.chat_socket = None
        self.connected = False
        self.username = None
        
    def connect_to_chat_server(self) -> bool:
        try:
            self.chat_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.chat_socket.connect((self.chat_host, self.chat_port))
            self.connected = True
            # Start listening thread to forward messages to this web client
            threading.Thread(target=self._listen_loop, daemon=True).start()
            return True
        except Exception as e:
            print(f"Failed to connect to chat server: {e}")
            return False
    
    def _listen_loop(self):
        buffer = ""
        decoder = json.JSONDecoder()
        while self.connected and self.chat_socket:
            try:
                data = self.chat_socket.recv(4096)
                if not data:
                    break
                buffer += data.decode('utf-8')
                # Stream-parse as many JSON objects as are fully available
                while True:
                    # Trim leading whitespace/newlines
                    tmp = buffer.lstrip()
                    if not tmp:
                        buffer = ""
                        break
                    consumed = len(buffer) - len(tmp)
                    buffer = tmp
                    try:
                        message, idx = decoder.raw_decode(buffer)
                    except json.JSONDecodeError:
                        # Not enough data for a full JSON object yet
                        break
                    # Forward message to the specific web client
                    socketio.emit('chat_message', message, to=self.web_sid)
                    # Remove the parsed JSON from the buffer and continue
                    buffer = buffer[idx:]
            except Exception as e:
                print(f"Error receiving from chat server: {e}")
                break
        self.connected = False
    
    def send_to_chat_server(self, message: dict) -> bool:
        if self.chat_socket and self.connected:
            try:
                # Send with newline delimiter
                self.chat_socket.send((json.dumps(message) + "\n").encode('utf-8'))
                return True
            except Exception as e:
                print(f"Error sending to chat server: {e}")
        return False
    
    def disconnect(self):
        self.connected = False
        if self.chat_socket:
            try:
                self.chat_socket.close()
            except Exception:
                pass
            self.chat_socket = None

# Map Socket.IO sid -> WebChatClient
web_clients = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_matrix_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    try:
        content = file.read().decode('utf-8')
        return jsonify({'content': content, 'filename': file.filename})
    except Exception as e:
        return jsonify({'error': f'Failed to read file: {str(e)}'}), 400

@socketio.on('connect')
def on_connect():
    sid = cast(Any, request).sid
    print(f"Web client connected: {sid}")
    emit('session_id', {'session_id': sid})

@socketio.on('disconnect')
def on_disconnect():
    sid = cast(Any, request).sid
    print(f"Web client disconnected: {sid}")
    client = web_clients.pop(sid, None)
    if client:
        client.disconnect()

@socketio.on('join_chat')
def on_join_chat(data):
    username = (data or {}).get('username', '').strip()
    if not username:
        emit('error', {'message': 'Username is required'})
        return
    sid = cast(Any, request).sid
    # Create client for this web socket
    client = WebChatClient(web_sid=sid)
    if not client.connect_to_chat_server():
        emit('error', {'message': 'Could not connect to chat server'})
        return
    # Send join to TCP chat
    if client.send_to_chat_server({'type': 'join', 'username': username}):
        client.username = username
        web_clients[sid] = client
        print(f"User {username} connected via web UI (sid={sid})")
    else:
        client.disconnect()
        emit('error', {'message': 'Failed to join chat'})

@socketio.on('send_message')
def on_send_message(data):
    sid = cast(Any, request).sid
    client = web_clients.get(sid)
    if not client:
        emit('error', {'message': 'Not connected to chat'})
        return
    text = (data or {}).get('message', '')
    if not client.send_to_chat_server({'type': 'chat', 'message': text}):
        emit('error', {'message': 'Failed to send message'})

@socketio.on('send_matrix_file')
def on_send_matrix_file(data):
    sid = cast(Any, request).sid
    client = web_clients.get(sid)
    if not client:
        emit('error', {'message': 'Not connected to chat'})
        return
    payload = {
        'type': 'matrix_file',
        'matrix_data': (data or {}).get('matrix_data', ''),
        'operation': (data or {}).get('operation', 'display'),
        'filename': (data or {}).get('filename', 'matrix.txt')
    }
    if not client.send_to_chat_server(payload):
        emit('error', {'message': 'Failed to send matrix file'})

@socketio.on('matrix_operation')
def on_matrix_operation(data):
    sid = cast(Any, request).sid
    client = web_clients.get(sid)
    if not client:
        emit('error', {'message': 'Not connected to chat'})
        return
    payload = {
        'type': 'matrix_operation',
        'operation': (data or {}).get('operation'),
        'matrices': (data or {}).get('matrices', [])
    }
    if not client.send_to_chat_server(payload):
        emit('error', {'message': 'Failed to perform matrix operation'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '5050'))  # Avoid macOS AirPlay on 5000
    print("🌐 Starting web interface for Matrix Chat...")
    print("💡 Make sure the TCP chat server is running on localhost:12345")
    print(f"🚀 Web interface available at http://localhost:{port}")
    socketio.run(app, host='127.0.0.1', port=port, debug=True)
