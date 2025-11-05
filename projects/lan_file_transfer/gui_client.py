"""
GUI Client Interface for LAN File Transfer System
Tkinter-based interface for the file transfer client
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
from pathlib import Path
from typing import Optional, List, Tuple

from client import FileTransferSession
from discovery import DiscoveryClient
from utils import format_file_size, setup_logging


class ClientGUI:
    """
    GUI interface for the file transfer client
    """
    
    def __init__(self):
        """Initialize the client GUI"""
        self.root = tk.Tk()
        self.root.title("LAN File Transfer - Client")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # Client session
        self.session: Optional[FileTransferSession] = None
        
        # GUI variables
        self.server_ip_var = tk.StringVar()
        self.server_port_var = tk.StringVar(value="8888")
        self.password_var = tk.StringVar(value="lan_transfer_2024")
        self.selected_file_var = tk.StringVar()
        
        # Transfer variables
        self.transfer_in_progress = tk.BooleanVar(value=False)
        self.progress_var = tk.DoubleVar(value=0.0)
        
        # Discovery variables
        self.discovered_servers = []
        
        # Setup logging
        self.logger = setup_logging()
        
        # Create GUI
        self._create_widgets()
        self._setup_callbacks()
    
    def _create_widgets(self):
        """Create and arrange GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Server Discovery Section
        discovery_frame = ttk.LabelFrame(main_frame, text="Server Discovery", padding="10")
        discovery_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        discovery_frame.columnconfigure(1, weight=1)
        
        # Discover button
        discover_btn = ttk.Button(discovery_frame, text="Discover Servers", 
                                 command=self._discover_servers)
        discover_btn.grid(row=0, column=0, padx=(0, 10))
        
        # Server list
        self.server_listbox = tk.Listbox(discovery_frame, height=4)
        self.server_listbox.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        self.server_listbox.bind('<<ListboxSelect>>', self._on_server_select)
        
        # Manual server entry
        ttk.Label(discovery_frame, text="Or enter manually:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        
        manual_frame = ttk.Frame(discovery_frame)
        manual_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(10, 0))
        manual_frame.columnconfigure(0, weight=1)
        
        ttk.Label(manual_frame, text="IP:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.ip_entry = ttk.Entry(manual_frame, textvariable=self.server_ip_var, width=15)
        self.ip_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        ttk.Label(manual_frame, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        port_entry = ttk.Entry(manual_frame, textvariable=self.server_port_var, width=8)
        port_entry.grid(row=0, column=3, sticky=tk.W)
        
        # Authentication Section
        auth_frame = ttk.LabelFrame(main_frame, text="Authentication", padding="10")
        auth_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        auth_frame.columnconfigure(1, weight=1)
        
        ttk.Label(auth_frame, text="Password:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        password_entry = ttk.Entry(auth_frame, textvariable=self.password_var, show="*", width=20)
        password_entry.grid(row=0, column=1, sticky=tk.W)
        
        # File Selection Section
        file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding="10")
        file_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        ttk.Label(file_frame, text="Selected File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        file_select_frame = ttk.Frame(file_frame)
        file_select_frame.grid(row=0, column=1, sticky=(tk.W, tk.E))
        file_select_frame.columnconfigure(0, weight=1)
        
        self.file_entry = ttk.Entry(file_select_frame, textvariable=self.selected_file_var, state="readonly")
        self.file_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        browse_btn = ttk.Button(file_select_frame, text="Browse", command=self._browse_file)
        browse_btn.grid(row=0, column=1)
        
        # File information
        self.file_info_label = ttk.Label(file_frame, text="No file selected")
        self.file_info_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        # Transfer Section
        transfer_frame = ttk.LabelFrame(main_frame, text="File Transfer", padding="10")
        transfer_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        transfer_frame.columnconfigure(0, weight=1)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(transfer_frame, variable=self.progress_var, 
                                          maximum=100, length=400)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Progress label
        self.progress_label = ttk.Label(transfer_frame, text="Ready to transfer")
        self.progress_label.grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        
        # Transfer button
        self.transfer_btn = ttk.Button(transfer_frame, text="Send File", 
                                      command=self._start_transfer, state="disabled")
        self.transfer_btn.grid(row=2, column=0, pady=(0, 10))
        
        # Transfer Log Section
        log_frame = ttk.LabelFrame(main_frame, text="Transfer Log", padding="10")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=70)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Clear log button
        clear_log_btn = ttk.Button(log_frame, text="Clear Log", command=self._clear_log)
        clear_log_btn.grid(row=1, column=0, pady=(5, 0))
    
    def _setup_callbacks(self):
        """Setup client callbacks"""
        # These will be set when creating a session
        pass
    
    def _discover_servers(self):
        """Discover available servers on the network"""
        self._log_message("Discovering servers...")
        
        # Disable discover button during discovery
        discover_btn = None
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.LabelFrame):
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, ttk.Button) and grandchild.cget("text") == "Discover Servers":
                                discover_btn = grandchild
                                break
        
        if discover_btn:
            discover_btn.config(state="disabled", text="Discovering...")
        
        # Run discovery in separate thread
        discovery_thread = threading.Thread(target=self._run_discovery)
        discovery_thread.daemon = True
        discovery_thread.start()
    
    def _run_discovery(self):
        """Run server discovery in separate thread"""
        try:
            discovery_client = DiscoveryClient()
            servers = discovery_client.find_servers()
            
            # Update UI in main thread
            self.root.after(0, self._update_discovered_servers, servers)
            
        except Exception as e:
            self.root.after(0, self._log_message, f"Discovery error: {e}")
        finally:
            # Re-enable discover button
            self.root.after(0, self._enable_discover_button)
    
    def _update_discovered_servers(self, servers: List[Tuple[str, int]]):
        """Update the discovered servers list"""
        self.discovered_servers = servers
        self.server_listbox.delete(0, tk.END)
        
        if servers:
            for ip, port in servers:
                self.server_listbox.insert(tk.END, f"{ip}:{port}")
            self._log_message(f"Found {len(servers)} server(s)")
        else:
            self.server_listbox.insert(tk.END, "No servers found")
            self._log_message("No servers found on the network")
    
    def _enable_discover_button(self):
        """Re-enable the discover button"""
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.LabelFrame):
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, ttk.Button) and "Discover" in grandchild.cget("text"):
                                grandchild.config(state="normal", text="Discover Servers")
                                break
    
    def _on_server_select(self, event):
        """Handle server selection from listbox"""
        selection = self.server_listbox.curselection()
        if selection:
            server_str = self.server_listbox.get(selection[0])
            if ":" in server_str:
                ip, port = server_str.split(":", 1)
                self.server_ip_var.set(ip)
                self.server_port_var.set(port)
                self._log_message(f"Selected server: {server_str}")
    
    def _browse_file(self):
        """Browse for file to send"""
        file_path = filedialog.askopenfilename(
            title="Select File to Send",
            filetypes=[("All Files", "*.*")]
        )
        
        if file_path:
            self.selected_file_var.set(file_path)
            self._update_file_info(file_path)
            self._check_transfer_ready()
    
    def _update_file_info(self, file_path: str):
        """Update file information display"""
        try:
            file_path_obj = Path(file_path)
            if file_path_obj.exists():
                size = file_path_obj.stat().st_size
                size_str = format_file_size(size)
                filename = file_path_obj.name
                self.file_info_label.config(text=f"File: {filename} ({size_str})")
            else:
                self.file_info_label.config(text="File not found")
        except Exception as e:
            self.file_info_label.config(text=f"Error: {e}")
    
    def _check_transfer_ready(self):
        """Check if transfer is ready and enable/disable transfer button"""
        has_file = bool(self.selected_file_var.get().strip())
        has_server = bool(self.server_ip_var.get().strip())
        has_password = bool(self.password_var.get().strip())
        not_transferring = not self.transfer_in_progress.get()
        
        ready = has_file and has_server and has_password and not_transferring
        self.transfer_btn.config(state="normal" if ready else "disabled")
    
    def _start_transfer(self):
        """Start file transfer"""
        if self.transfer_in_progress.get():
            return
        
        # Validate inputs
        server_ip = self.server_ip_var.get().strip()
        if not server_ip:
            messagebox.showerror("Error", "Please enter server IP address")
            return
        
        try:
            server_port = int(self.server_port_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid port number")
            return
        
        file_path = self.selected_file_var.get().strip()
        if not file_path:
            messagebox.showerror("Error", "Please select a file to send")
            return
        
        password = self.password_var.get().strip()
        if not password:
            messagebox.showerror("Error", "Please enter password")
            return
        
        # Start transfer in separate thread
        self.transfer_in_progress.set(True)
        self.transfer_btn.config(state="disabled", text="Transferring...")
        self.progress_var.set(0.0)
        self.progress_label.config(text="Connecting...")
        
        transfer_thread = threading.Thread(
            target=self._run_transfer,
            args=(server_ip, server_port, file_path, password)
        )
        transfer_thread.daemon = True
        transfer_thread.start()
    
    def _run_transfer(self, server_ip: str, server_port: int, file_path: str, password: str):
        """Run file transfer in separate thread"""
        try:
            # Create session with callbacks
            self.session = FileTransferSession(password)
            self.session.set_callbacks(
                on_connected=self._on_connected,
                on_progress=self._on_progress,
                on_complete=self._on_complete,
                on_error=self._on_error
            )
            
            # Perform transfer
            success = self.session.connect_and_send_file(server_ip, server_port, file_path)
            
            # Update UI in main thread
            self.root.after(0, self._transfer_complete, success)
            
        except Exception as e:
            self.root.after(0, self._on_error, f"Transfer error: {e}")
        finally:
            self.root.after(0, self._transfer_finished)
    
    def _on_connected(self, server_ip: str, server_port: int):
        """Callback when connected to server"""
        self.root.after(0, self.progress_label.config, {"text": "Connected, authenticating..."})
        self.root.after(0, self._log_message, f"Connected to {server_ip}:{server_port}")
    
    def _on_progress(self, progress: float, sent: int, total: int):
        """Callback for transfer progress updates"""
        def update_progress():
            self.progress_var.set(progress)
            sent_str = format_file_size(sent)
            total_str = format_file_size(total)
            self.progress_label.config(text=f"Transferring... {sent_str} / {total_str} ({progress:.1f}%)")
        
        self.root.after(0, update_progress)
    
    def _on_complete(self, filename: str, size: int, success: bool):
        """Callback when transfer completes"""
        def update_complete():
            if success:
                self.progress_label.config(text="Transfer completed successfully!")
                self._log_message(f"File sent successfully: {filename}")
                messagebox.showinfo("Success", f"File '{filename}' sent successfully!")
            else:
                self.progress_label.config(text="Transfer failed")
                self._log_message(f"File transfer failed: {filename}")
                messagebox.showerror("Error", f"Failed to send file '{filename}'")
        
        self.root.after(0, update_complete)
    
    def _on_error(self, error_message: str):
        """Callback when an error occurs"""
        self.root.after(0, self.progress_label.config, {"text": f"Error: {error_message}"})
        self.root.after(0, self._log_message, f"Error: {error_message}")
        self.root.after(0, messagebox.showerror, "Transfer Error", error_message)
    
    def _transfer_complete(self, success: bool):
        """Handle transfer completion"""
        if success:
            self.progress_var.set(100.0)
        else:
            self.progress_var.set(0.0)
    
    def _transfer_finished(self):
        """Clean up after transfer"""
        self.transfer_in_progress.set(False)
        self.transfer_btn.config(state="normal", text="Send File")
        self._check_transfer_ready()
    
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
            if self.session:
                self.session.client.disconnect()


def main():
    """Main function to run the client GUI"""
    app = ClientGUI()
    app.run()


if __name__ == "__main__":
    main()
