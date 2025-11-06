import asyncio
import json
import os
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Input, Static, Log
from textual.reactive import var

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5000


class ChatClient:
    def __init__(self, ui_app):
        self.ui = ui_app
        self.reader = None
        self.writer = None

    async def connect(self):
        try:
            self.reader, self.writer = await asyncio.open_connection(SERVER_HOST, SERVER_PORT)
            self.ui.write_system("✅ Connected to MatrixMesh server.")
            asyncio.create_task(self.listen_for_messages())
        except Exception as e:
            self.ui.write_system(f"❌ Connection failed: {e}")

    async def listen_for_messages(self):
        try:
            while True:
                data = await self.reader.readline() # type: ignore
                if not data:
                    self.ui.write_system("⚠️ Server disconnected.")
                    break
                message = data.decode().strip()
                self.ui.write_server(message)
        except Exception as e:
            self.ui.write_system(f"⚠️ Error receiving data: {e}")

    def send_message(self, message_dict):
        """Send JSON-encoded message to server"""
        if not self.writer:
            self.ui.write_system("⚠️ Not connected to server.")
            return
        try:
            json_msg = json.dumps(message_dict) + "\n"
            self.writer.write(json_msg.encode())
        except Exception as e:
            self.ui.write_system(f"❌ Send failed: {e}")

    def send_chat_message(self, text):
        """Send a plain chat message"""
        message = {'type': 'chat', 'text': text}
        self.send_message(message)

    def send_matrix_file(self, file_path, operation='display'):
        """Send a matrix file to the server"""
        if not os.path.exists(file_path):
            self.ui.write_system(f"❌ File not found: {file_path}")
            return

        try:
            with open(file_path, 'r') as file:
                matrix_data = file.read()

            message = {
                'type': 'matrix_file',
                'matrix_data': str(matrix_data),  # send as string
                'operation': operation,
                'filename': os.path.basename(file_path)
            }

            self.send_message(message)
            self.ui.write_system(f"📁 Sent matrix file: {file_path} (operation: {operation})")

        except Exception as e:
            self.ui.write_system(f"❌ Failed to send matrix file: {e}")

    def request_matrix_operation(self, operation, matrices_text):
        """Request a specific matrix operation"""
        try:
            matrices_text = matrices_text.strip()
            message = {
                'type': 'matrix_operation',
                'operation': operation,
                'matrix_data': matrices_text  # send as string, not list
            }
            self.send_message(message)
            self.ui.write_system(f"🔢 Requested operation: {operation}")
        except Exception as e:
            self.ui.write_system(f"❌ Failed to request operation: {e}")


class ChatApp(App):
    CSS_PATH = None
    BINDINGS = [("ctrl+c", "quit", "Quit")]
    chat_history = var([])

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("🧮 MatrixMesh Chat", id="header"),
            Log(id="chat", highlight=True),
            Input(placeholder="Type a message or command...", id="msg_input"),
        )

    async def on_mount(self):
        self.chat_box = self.query_one("#chat", Log)
        self.msg_input = self.query_one("#msg_input", Input)
        self.client = ChatClient(self)
        await self.client.connect()
        self.write_system("💡 Commands: /sendfile <path> [operation], /op <operation> <matrix text>")

    def write_system(self, text):
        self.chat_box.write(f"[green]{text}[/green]")

    def write_server(self, text):
        self.chat_box.write(f"[yellow]Server:[/yellow] {text}")

    def write_user(self, text):
        self.chat_box.write(f"[cyan]You:[/cyan] {text}")

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        text = message.value.strip()
        if not text:
            return
        self.write_user(text)

        if text.startswith("/sendfile"):
            parts = text.split(maxsplit=2)
            if len(parts) < 2:
                self.write_system("⚠️ Usage: /sendfile <path> [operation]")
            else:
                file_path = parts[1]
                operation = parts[2] if len(parts) > 2 else "display"
                self.client.send_matrix_file(file_path, operation)

        elif text.startswith("/op"):
            parts = text.split(maxsplit=2)
            if len(parts) < 3:
                self.write_system("⚠️ Usage: /op <operation> <matrix data>")
            else:
                operation = parts[1]
                matrix_data = parts[2]
                self.client.request_matrix_operation(operation, matrix_data)

        else:
            self.client.send_chat_message(text)

        message.input.value = ""


if __name__ == "__main__":
    app = ChatApp()
    app.run()