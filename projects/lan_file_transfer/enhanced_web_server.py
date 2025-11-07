"""
Enhanced Web-based LAN File Transfer System
Supports multiple files to multiple users with batch operations
"""

import os
import json
import threading
import time
import shutil
import atexit
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
# Removed Flask-SocketIO dependency for 100% offline operation
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

# Import existing components
from server import FileTransferServer
from discovery import discover_servers
from utils import get_local_ip, format_file_size, setup_logging
from multi_transfer_manager import transfer_manager, TransferStatus

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = 'web_uploads'
app.config['RECEIVE_FOLDER'] = 'web_received'
app.config['SECRET_KEY'] = 'lan_transfer_web_2024'

# Simple polling-based chat system (100% offline, no external dependencies)

# Global variables
server_instance = None
transfer_logs = []
connected_clients = []

# Chat system variables
chat_room = "lan_transfer_chat"
connected_users = {}  # {session_id: {'username': str, 'ip': str, 'connected_at': str}}
chat_messages = []  # Store recent messages

# Create upload directory
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
Path(app.config['RECEIVE_FOLDER']).mkdir(exist_ok=True)

# Clean up any existing files on startup
def startup_cleanup():
    """Clean up any existing files when server starts"""
    try:
        print("🧹 Starting with clean directories...")
        
        # Clean upload directory
        upload_dir = Path(app.config['UPLOAD_FOLDER'])
        if upload_dir.exists():
            for file_path in upload_dir.iterdir():
                if file_path.is_file():
                    file_path.unlink()
        
        # Clean receive directory
        receive_dir = Path(app.config['RECEIVE_FOLDER'])
        if receive_dir.exists():
            for file_path in receive_dir.iterdir():
                if file_path.is_file():
                    file_path.unlink()
        
        print("✅ Startup cleanup completed")
        
    except Exception as e:
        print(f"❌ Error during startup cleanup: {e}")

# Run startup cleanup
startup_cleanup()

# Setup logging
logger = setup_logging()

# Start transfer manager
transfer_manager.start()


def cleanup_files():
    """Clean up all uploaded and received files when server shuts down"""
    try:
        print("\n🧹 Cleaning up files...")
        
        # Clean upload directory
        upload_dir = Path(app.config['UPLOAD_FOLDER'])
        if upload_dir.exists():
            for file_path in upload_dir.iterdir():
                if file_path.is_file():
                    file_path.unlink()
                    print(f"   Deleted: {file_path.name}")
        
        # Clean receive directory
        receive_dir = Path(app.config['RECEIVE_FOLDER'])
        if receive_dir.exists():
            for file_path in receive_dir.iterdir():
                if file_path.is_file():
                    file_path.unlink()
                    print(f"   Deleted: {file_path.name}")
        
        print("✅ File cleanup completed")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")


# Register cleanup function to run on exit
atexit.register(cleanup_files)


# Simple HTTP-based chat endpoints (100% offline)

@app.route('/api/chat/join', methods=['POST'])
def chat_join():
    """Join the chat room"""
    try:
        data = request.get_json()
        username = data.get('username', f'User_{len(connected_users) + 1}').strip()
        client_ip = request.environ.get('REMOTE_ADDR', 'Unknown')
        
        # Create user session
        session_id = f"user_{int(time.time() * 1000)}_{len(connected_users)}"
        connected_users[session_id] = {
            'username': username,
            'ip': client_ip,
            'connected_at': time.strftime('%H:%M:%S'),
            'last_seen': time.time()
        }
        
        # Add join message
        join_message = {
            'id': f"msg_{int(time.time() * 1000)}",
            'type': 'system',
            'message': f"{username} joined the chat",
            'timestamp': time.strftime('%H:%M:%S')
        }
        chat_messages.append(join_message)
        
        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'username': username,
            'messages': chat_messages[-50:],  # Last 50 messages
            'users': list(connected_users.values())
        })
        
    except Exception as e:
        logger.error(f"Chat join error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/chat/send', methods=['POST'])
def chat_send():
    """Send a chat message"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        message_text = data.get('message', '').strip()
        
        if not session_id or session_id not in connected_users:
            return jsonify({'status': 'error', 'message': 'Invalid session'}), 400
        
        if not message_text:
            return jsonify({'status': 'error', 'message': 'Empty message'}), 400
        
        username = connected_users[session_id]['username']
        
        # Create message
        message = {
            'id': f"msg_{int(time.time() * 1000)}",
            'type': 'user',
            'username': username,
            'message': message_text,
            'timestamp': time.strftime('%H:%M:%S'),
            'ip': connected_users[session_id]['ip']
        }
        
        # Add to chat history (keep last 100 messages)
        chat_messages.append(message)
        if len(chat_messages) > 100:
            chat_messages.pop(0)
        
        # Update user last seen
        connected_users[session_id]['last_seen'] = time.time()
        
        logger.info(f"Chat message from {username}: {message_text}")
        
        return jsonify({'status': 'success', 'message': message})
        
    except Exception as e:
        logger.error(f"Chat send error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/chat/messages')
def chat_messages_api():
    """Get recent chat messages"""
    try:
        since = request.args.get('since', 0, type=int)
        
        # Filter messages since the given timestamp
        recent_messages = []
        for msg in chat_messages:
            msg_id = int(msg['id'].split('_')[1])
            if msg_id > since:
                recent_messages.append(msg)
        
        return jsonify({
            'status': 'success',
            'messages': recent_messages,
            'users': list(connected_users.values())
        })
        
    except Exception as e:
        logger.error(f"Chat messages error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/chat/change-username', methods=['POST'])
def chat_change_username():
    """Change username"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        new_username = data.get('username', '').strip()
        
        if not session_id or session_id not in connected_users:
            return jsonify({'status': 'error', 'message': 'Invalid session'}), 400
        
        if not new_username:
            return jsonify({'status': 'error', 'message': 'Empty username'}), 400
        
        old_username = connected_users[session_id]['username']
        connected_users[session_id]['username'] = new_username
        connected_users[session_id]['last_seen'] = time.time()
        
        # Add username change message
        change_message = {
            'id': f"msg_{int(time.time() * 1000)}",
            'type': 'system',
            'message': f"{old_username} is now known as {new_username}",
            'timestamp': time.strftime('%H:%M:%S')
        }
        chat_messages.append(change_message)
        
        logger.info(f"Username changed: {old_username} -> {new_username}")
        
        return jsonify({'status': 'success', 'new_username': new_username})
        
    except Exception as e:
        logger.error(f"Chat change username error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/chat/leave', methods=['POST'])
def chat_leave():
    """Leave the chat room"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if session_id and session_id in connected_users:
            username = connected_users[session_id]['username']
            
            # Add leave message
            leave_message = {
                'id': f"msg_{int(time.time() * 1000)}",
                'type': 'system',
                'message': f"{username} left the chat",
                'timestamp': time.strftime('%H:%M:%S')
            }
            chat_messages.append(leave_message)
            
            # Remove user
            del connected_users[session_id]
            
            logger.info(f"Chat user left: {username}")
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        logger.error(f"Chat leave error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/')
def index():
    """Main page - enhanced interface for multi-file transfers"""
    return render_template('enhanced_index.html')


@app.route('/api/server/start', methods=['POST'])
def start_server():
    """Start the file transfer server"""
    global server_instance
    
    try:
        data = request.get_json()
        port = data.get('port', 8888)
        password = data.get('password', 'lan_transfer_2024')
        receive_dir = data.get('receive_dir', 'web_received')
        
        # Stop existing server if running
        if server_instance:
            server_instance.stop_server()
        
        # Create new server
        server_instance = FileTransferServer(port, password, receive_dir)
        
        # Set up callbacks for web updates
        def on_client_connected(client_ip):
            connected_clients.append({
                'ip': client_ip,
                'connected_at': time.strftime('%H:%M:%S'),
                'status': 'connected'
            })
            logger.info(f"Web client connected: {client_ip}")
        
        def on_file_received(filename, size, file_path):
            transfer_logs.append({
                'type': 'received',
                'filename': filename,
                'size': size,
                'size_formatted': format_file_size(size),
                'timestamp': time.strftime('%H:%M:%S'),
                'status': 'success'
            })
            logger.info(f"File received via web: {filename}")
        
        def on_error(error_message):
            transfer_logs.append({
                'type': 'error',
                'message': error_message,
                'timestamp': time.strftime('%H:%M:%S'),
                'status': 'error'
            })
            logger.error(f"Web server error: {error_message}")
        
        server_instance.on_client_connected = on_client_connected
        server_instance.on_file_received = on_file_received
        server_instance.on_error = on_error
        
        # Start server in separate thread
        server_start_success = threading.Event()
        server_start_error = None
        
        def run_server():
            nonlocal server_start_error
            try:
                success = server_instance.start_server(enable_discovery=True)
                if success:
                    server_start_success.set()
                else:
                    server_start_error = "Failed to start server"
            except Exception as e:
                server_start_error = str(e)
        
        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()
        
        # Wait for server to start (up to 5 seconds)
        if not server_start_success.wait(timeout=5):
            error_msg = server_start_error or "Server start timeout"
            logger.error(f"Server start failed: {error_msg}")
            return jsonify({
                'status': 'error',
                'message': f"Failed to start server: {error_msg}"
            }), 500
        
        return jsonify({
            'status': 'success',
            'message': f'Server started on port {port}',
            'server_ip': get_local_ip(),
            'port': port
        })
        
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/server/stop', methods=['POST'])
def stop_server():
    """Stop the file transfer server"""
    global server_instance
    
    try:
        if server_instance:
            server_instance.stop_server()
            server_instance = None
            connected_clients.clear()
            
        return jsonify({
            'status': 'success',
            'message': 'Server stopped'
        })
        
    except Exception as e:
        logger.error(f"Error stopping server: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/server/status')
def server_status():
    """Get server status and information"""
    global server_instance
    
    if server_instance:
        info = server_instance.get_server_info()
        return jsonify({
            'status': 'running',
            'info': info,
            'connected_clients': connected_clients,
            'transfer_logs': transfer_logs[-10:]  # Last 10 transfers
        })
    else:
        return jsonify({
            'status': 'stopped',
            'info': None,
            'connected_clients': [],
            'transfer_logs': transfer_logs[-10:]
        })


@app.route('/api/files/cleanup', methods=['POST'])
def cleanup_files_api():
    """Manually clean up all uploaded and received files"""
    try:
        cleanup_files()
        return jsonify({
            'status': 'success',
            'message': 'Files cleaned up successfully'
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up files: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/discover')
def discover_servers_api():
    """Discover available servers on the network"""
    try:
        servers = discover_servers(timeout=15)
        server_list = []
        
        for ip, port in servers:
            server_list.append({
                'ip': ip,
                'port': port,
                'display': f"{ip}:{port}"
            })
        
        return jsonify({
            'status': 'success',
            'servers': server_list,
            'count': len(server_list)
        })
        
    except Exception as e:
        logger.error(f"Discovery error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/upload/batch', methods=['POST'])
def upload_batch():
    """Handle batch file uploads to multiple servers"""
    try:
        # Get form data
        files = request.files.getlist('files')
        target_servers_json = request.form.get('target_servers', '[]')
        password = request.form.get('password', 'lan_transfer_2024').strip()
        batch_name = request.form.get('batch_name', f'Batch_{int(time.time())}')
        
        if not files or all(f.filename == '' for f in files):
            return jsonify({
                'status': 'error',
                'message': 'No files provided'
            }), 400
        
        # Parse target servers
        try:
            target_servers = json.loads(target_servers_json)
        except json.JSONDecodeError:
            return jsonify({
                'status': 'error',
                'message': 'Invalid target servers format'
            }), 400
        
        if not target_servers:
            return jsonify({
                'status': 'error',
                'message': 'No target servers specified'
            }), 400
        
        # Save uploaded files temporarily
        saved_files = []
        for file in files:
            if file.filename == '':
                continue
                
            filename = secure_filename(file.filename)
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{filename}")
            file.save(temp_path)
            saved_files.append(temp_path)
        
        # Add batch transfer
        batch_id = transfer_manager.add_batch_transfer(
            name=batch_name,
            files=saved_files,
            target_servers=target_servers,
            password=password
        )
        
        # Add to transfer logs
        for file_path in saved_files:
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            transfer_logs.append({
                'type': 'batch_upload',
                'filename': filename,
                'size': file_size,
                'size_formatted': format_file_size(file_size),
                'timestamp': time.strftime('%H:%M:%S'),
                'status': 'queued',
                'batch_id': batch_id,
                'target_servers': len(target_servers)
            })
        
        return jsonify({
            'status': 'success',
            'message': f'Batch upload started: {batch_name}',
            'batch_id': batch_id,
            'files_count': len(saved_files),
            'target_servers_count': len(target_servers)
        })
        
    except RequestEntityTooLarge:
        return jsonify({
            'status': 'error',
            'message': 'Files too large. Maximum size is 100MB per file.'
        }), 413
    except Exception as e:
        logger.error(f"Batch upload error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/upload/single', methods=['POST'])
def upload_single():
    """Handle single file upload to one server"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No file provided'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No file selected'
            }), 400
        
        # Get server information
        server_ip = request.form.get('server_ip', '').strip()
        server_port = int(request.form.get('server_port', 8888))
        password = request.form.get('password', 'lan_transfer_2024').strip()
        
        if not server_ip:
            return jsonify({
                'status': 'error',
                'message': 'Server IP address required'
            }), 400
        
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{filename}")
        file.save(temp_path)
        
        # Get file size
        file_size = os.path.getsize(temp_path)
        
        # Add single transfer
        task_id = transfer_manager.add_single_transfer(
            file_path=temp_path,
            target_server=server_ip,
            target_port=server_port,
            password=password
        )
        
        # Add to transfer logs
        transfer_logs.append({
            'type': 'single_upload',
            'filename': filename,
            'size': file_size,
            'size_formatted': format_file_size(file_size),
            'timestamp': time.strftime('%H:%M:%S'),
            'status': 'queued',
            'task_id': task_id,
            'target_server': f"{server_ip}:{server_port}"
        })
        
        return jsonify({
            'status': 'success',
            'message': f'Upload started for {filename}',
            'task_id': task_id,
            'filename': filename,
            'size': file_size,
            'size_formatted': format_file_size(file_size)
        })
        
    except RequestEntityTooLarge:
        return jsonify({
            'status': 'error',
            'message': 'File too large. Maximum size is 100MB.'
        }), 413
    except Exception as e:
        logger.error(f"Single upload error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/transfers/status')
def transfers_status():
    """Get status of all transfers"""
    try:
        status = transfer_manager.get_all_transfers()
        return jsonify({
            'status': 'success',
            'data': status
        })
        
    except Exception as e:
        logger.error(f"Transfer status error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/transfers/<task_id>/cancel', methods=['POST'])
def cancel_transfer(task_id):
    """Cancel a specific transfer"""
    try:
        success = transfer_manager.cancel_transfer(task_id)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Transfer {task_id} cancelled'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Transfer not found or cannot be cancelled'
            }), 404
            
    except Exception as e:
        logger.error(f"Cancel transfer error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/files')
def list_files():
    """List received files"""
    try:
        files = []
        upload_dir = Path(app.config['RECEIVE_FOLDER'])
        
        if upload_dir.exists():
            for file_path in upload_dir.iterdir():
                if file_path.is_file():
                    stat = file_path.stat()
                    files.append({
                        'name': file_path.name,
                        'size': stat.st_size,
                        'size_formatted': format_file_size(stat.st_size),
                        'modified': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime))
                    })
        
        return jsonify({
            'status': 'success',
            'files': files
        })
        
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/files/<filename>')
def download_file(filename):
    """Download a file"""
    try:
        file_path = Path(app.config['RECEIVE_FOLDER']) / secure_filename(filename)
        
        if not file_path.exists():
            return jsonify({
                'status': 'error',
                'message': 'File not found'
            }), 404
        
        return send_file(str(file_path), as_attachment=True)
        
    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/network/info')
def network_info():
    """Get network information"""
    try:
        local_ip = get_local_ip()
        return jsonify({
            'status': 'success',
            'local_ip': local_ip,
            'message': f'Access this interface from other devices using: http://{local_ip}:8080'
        })
        
    except Exception as e:
        logger.error(f"Network info error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# Set up transfer manager callbacks
def on_transfer_started(task):
    """Callback when transfer starts"""
    transfer_logs.append({
        'type': 'transfer_started',
        'filename': task.filename,
        'size': task.file_size,
        'size_formatted': format_file_size(task.file_size),
        'timestamp': time.strftime('%H:%M:%S'),
        'status': 'started',
        'target_server': f"{task.target_server}:{task.target_port}"
    })

def on_transfer_progress(task):
    """Callback for transfer progress updates"""
    # Update existing log entry
    for log in transfer_logs:
        if log.get('filename') == task.filename and log.get('status') in ['started', 'in_progress']:
            log['progress'] = task.progress
            log['sent_bytes'] = task.sent_bytes
            log['status'] = 'in_progress'
            break

def on_transfer_completed(task):
    """Callback when transfer completes"""
    status = 'success' if task.status == TransferStatus.COMPLETED else 'failed'
    
    transfer_logs.append({
        'type': 'transfer_completed',
        'filename': task.filename,
        'size': task.file_size,
        'size_formatted': format_file_size(task.file_size),
        'timestamp': time.strftime('%H:%M:%S'),
        'status': status,
        'target_server': f"{task.target_server}:{task.target_port}",
        'error_message': task.error_message
    })

def on_error(error_message):
    """Callback for errors"""
    transfer_logs.append({
        'type': 'error',
        'message': error_message,
        'timestamp': time.strftime('%H:%M:%S'),
        'status': 'error'
    })

# Set callbacks
transfer_manager.on_transfer_started = on_transfer_started
transfer_manager.on_transfer_progress = on_transfer_progress
transfer_manager.on_transfer_completed = on_transfer_completed
transfer_manager.on_error = on_error


if __name__ == '__main__':
    print("🌐 Enhanced LAN File Transfer - Multi-File, Multi-User System")
    print("=" * 60)
    print(f"Local access: http://localhost:8080")
    print(f"Network access: http://{get_local_ip()}:8080")
    print("=" * 60)
    print("📱 Works on any device with a web browser!")
    print("🖥️  Windows, Mac, Linux, iPhone, Android, iPad")
    print("🚀 Supports multiple files to multiple users!")
    print("=" * 60)
    
    try:
        # Get local IP address
        local_ip = get_local_ip()
        print(f"🌐 Server accessible at:")
        print(f"   Local: http://localhost:8080")
        print(f"   Network: http://{local_ip}:8080")
        print(f"   Other devices: http://{local_ip}:8080")
        print("=" * 60)
        
        # Run Flask app (100% offline, no external dependencies)
        app.run(
            host='0.0.0.0',  # Allow access from other devices
            port=8080,  # Changed to port 8080
            debug=False,  # Disable debug for better network access
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user (Ctrl+C)")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
    finally:
        # Cleanup
        print("\n🧹 Shutting down and cleaning up...")
        transfer_manager.stop()
        cleanup_files()  # Clean up files on shutdown
        print("✅ Server shutdown complete")
