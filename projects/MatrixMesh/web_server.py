#!/usr/bin/env python3
"""
Deprecated wrapper: delegates to the updated web_server_simple implementation.
Use the VS Code task "Start Web Interface" which runs web_server_simple.py.
"""

from web_server_simple import app, socketio
import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '5050'))  # align with web_server_simple
    print("⚠️ 'web_server.py' is deprecated. Starting web_server_simple instead.")
    print("🌐 Starting web interface for Matrix Chat...")
    print("💡 Make sure the TCP chat server is running on localhost:12345")
    print(f"🚀 Web interface available at http://localhost:{port}")
    socketio.run(app, host='127.0.0.1', port=port, debug=True)
