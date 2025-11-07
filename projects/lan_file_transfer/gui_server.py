"""
GUI Server Interface for LAN File Transfer System
Tkinter-based interface for the file transfer server
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
from pathlib import Path
from typing import Optional

from server import FileTransferServer
from utils import get_local_ip, format_file_size, setup_logging


class ServerGUI:
    """
    GUI interface for the file transfer server
    """
    
    def __init__(self):
        """Initialize the server GUI"""
        self.root = tk.Tk()
        self.root.title("LAN File Transfer - Server")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # Server instance
        self.server: Optional[FileTransferServer] = None
        self.server_thread: Optional[threading.Thread] = None
        
        # GUI variables
        self.server_running = tk.BooleanVar(value=False)
        self.port_var = tk.StringVar(value="8888")
        self.password_var = tk.StringVar(value="lan_transfer_2024")
        self.receive_dir_var = tk.StringVar(value="received_files")
        self.discovery_enabled = tk.BooleanVar(value=True)
        
        # Status variables
        self.connected_clients = []
        self.transfer_log = []
        
        # Setup logging
        self.logger = setup_logging()
        
        # Create GUI
        self._create_widgets()
        self._setup_callbacks()
        
        # Update display
        self._update_status()
    
    def _create_widgets(self):
        """Create and arrange GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Server Configuration Section
        config_frame = ttk.LabelFrame(main_frame, text="Server Configuration", padding="10")
        config_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)
        
        # Port configuration
        ttk.Label(config_frame, text="Port:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        port_entry = ttk.Entry(config_frame, textvariable=self.port_var, width=10)
        port_entry.grid(row=0, column=1, sticky=tk.W)
        
        # Password configuration
        ttk.Label(config_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        password_entry = ttk.Entry(config_frame, textvariable=self.password_var, show="*", width=20)
        password_entry.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        # Receive directory configuration
        ttk.Label(config_frame, text="Receive Directory:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        dir_frame = ttk.Frame(config_frame)
        dir_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(5, 0))
        dir_frame.columnconfigure(0, weight=1)
        
        dir_entry = ttk.Entry(dir_frame, textvariable=self.receive_dir_var)
        dir_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        browse_btn = ttk.Button(dir_frame, text="Browse", command=self._browse_directory)
        browse_btn.grid(row=0, column=1)
        
        # Discovery option
        discovery_check = ttk.Checkbutton(config_frame, text="Enable Discovery Service", 
                                        variable=self.discovery_enabled)
        discovery_check.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        # Server Control Section
        control_frame = ttk.LabelFrame(main_frame, text="Server Control", padding="10")
        control_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Start/Stop button
        self.start_stop_btn = ttk.Button(control_frame, text="Start Server", 
                                        command=self._toggle_server)
        self.start_stop_btn.grid(row=0, column=0, padx=(0, 10))
        
        # Server status
        self.status_label = ttk.Label(control_frame, text="Server Status: Stopped", 
                                    foreground="red")
        self.status_label.grid(row=0, column=1, sticky=tk.W)
        
        # Server Information Section
        info_frame = ttk.LabelFrame(main_frame, text="Server Information", padding="10")
        info_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        info_frame.columnconfigure(1, weight=1)
        
        # Local IP
        ttk.Label(info_frame, text="Local IP:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.ip_label = ttk.Label(info_frame, text=get_local_ip())
        self.ip_label.grid(row=0, column=1, sticky=tk.W)
        
        # Server port
        ttk.Label(info_frame, text="Server Port:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.port_label = ttk.Label(info_frame, text="Not running")
        self.port_label.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        # Connected clients
        ttk.Label(info_frame, text="Connected Clients:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.clients_label = ttk.Label(info_frame, text="0")
        self.clients_label.grid(row=2, column=1, sticky=tk.W, pady=(5, 0))
        
        # Transfer Log Section
        log_frame = ttk.LabelFrame(main_frame, text="Transfer Log", padding="10")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=70)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Clear log button
        clear_log_btn = ttk.Button(log_frame, text="Clear Log", command=self._clear_log)
        clear_log_btn.grid(row=1, column=0, pady=(5, 0))
    
    def _setup_callbacks(self):
        """Setup server callbacks"""
        # These will be set when the server is created
        pass
    
    def _browse_directory(self):
        """Browse for receive directory"""
        directory = filedialog.askdirectory(title="Select Receive Directory")
        if directory:
            self.receive_dir_var.set(directory)
    
    def _toggle_server(self):
        """Start or stop the server"""
        if not self.server_running.get():
            self._start_server()
        else:
            self._stop_server()
    
    def _start_server(self):
        """Start the file transfer server"""
        try:
            # Validate inputs
            port = int(self.port_var.get())
            if port < 1 or port > 65535:
                messagebox.showerror("Error", "Port must be between 1 and 65535")
                return
            
            password = self.password_var.get().strip()
            if not password:
                messagebox.showerror("Error", "Password cannot be empty")
                return
            
            receive_dir = self.receive_dir_var.get().strip()
            if not receive_dir:
                messagebox.showerror("Error", "Receive directory cannot be empty")
                return
            
            # Create receive directory if it doesn't exist
            Path(receive_dir).mkdir(parents=True, exist_ok=True)
            
            # Create server instance
            self.server = FileTransferServer(port, password, receive_dir)
            
            # Setup callbacks
            self.server.on_client_connected = self._on_client_connected
            self.server.on_file_received = self._on_file_received
            self.server.on_transfer_progress = self._on_transfer_progress
            self.server.on_error = self._on_error
            
            # Start server in a separate thread
            self.server_thread = threading.Thread(target=self._run_server)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            # Update UI
            self.server_running.set(True)
            self.start_stop_btn.config(text="Stop Server")
            self.status_label.config(text="Server Status: Running", foreground="green")
            self.port_label.config(text=str(port))
            
            self._log_message("Server started successfully")
            
        except ValueError:
            messagebox.showerror("Error", "Invalid port number")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start server: {e}")
            self._log_message(f"Error starting server: {e}")
    
    def _run_server(self):
        """Run the server (called in separate thread)"""
        try:
            self.server.start_server(self.discovery_enabled.get())
        except Exception as e:
            self._log_message(f"Server error: {e}")
    
    def _stop_server(self):
        """Stop the file transfer server"""
        if self.server:
            self.server.stop_server()
            self.server = None
        
        # Update UI
        self.server_running.set(False)
        self.start_stop_btn.config(text="Start Server")
        self.status_label.config(text="Server Status: Stopped", foreground="red")
        self.port_label.config(text="Not running")
        self.clients_label.config(text="0")
        
        self._log_message("Server stopped")
    
    def _on_client_connected(self, client_ip: str):
        """Callback when a client connects"""
        self.connected_clients.append(client_ip)
        self._update_status()
        self._log_message(f"Client connected: {client_ip}")
    
    def _on_file_received(self, filename: str, size: int, file_path: Path):
        """Callback when a file is received"""
        size_str = format_file_size(size)
        self._log_message(f"File received: {filename} ({size_str})")
        self._update_status()
    
    def _on_transfer_progress(self, progress: float, received: int, total: int):
        """Callback for transfer progress updates"""
        # This could be used to update a progress bar in the future
        pass
    
    def _on_error(self, error_message: str):
        """Callback when an error occurs"""
        self._log_message(f"Error: {error_message}")
        messagebox.showerror("Server Error", error_message)
    
    def _update_status(self):
        """Update the status display"""
        self.clients_label.config(text=str(len(self.connected_clients)))
    
    def _log_message(self, message: str):
        """Add a message to the log"""
        import time
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
    
    def _clear_log(self):
        """Clear the transfer log"""
        self.log_text.delete(1.0, tk.END)
    
    def run(self):
        """Start the GUI main loop"""
        try:
            self.root.mainloop()
        finally:
            # Cleanup when closing
            if self.server:
                self.server.stop_server()


def main():
    """Main function to run the server GUI"""
    app = ServerGUI()
    app.run()


if __name__ == "__main__":
    main()
