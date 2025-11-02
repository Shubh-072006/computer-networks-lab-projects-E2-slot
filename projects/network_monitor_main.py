
"""
Network Monitoring Tool - Main Application
Integrates bandwidth monitoring, device scanning, topology visualization, and alerts
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from datetime import datetime
from packet_sniffer import PacketSniffer
# Import our custom modules
from bandwidth_monitor import BandwidthMonitor
from device_scanner import DeviceScanner
from network_topology import NetworkTopology
from alerts_manager import AlertsManager

class NetworkMonitoringTool:
    def __init__(self, root):
        self.root = root
        self.root.title("🌐 Network Monitoring Tool v2.0")
        self.root.geometry("1000x800")
        self.root.configure(bg="#f0f0f0")
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=10)

        # Initialize monitoring modules
        self.bandwidth_monitor = BandwidthMonitor()
        self.device_scanner = DeviceScanner()
        self.network_topology = NetworkTopology()
        self.alerts_manager = AlertsManager()
        self.packet_sniffer = PacketSniffer()
        self.create_sniffer_tab()

        # Initialize monitoring state
        self.monitoring_active = True
        self.last_devices = []

        
        # Setup GUI
        self.setup_gui()

        # Start monitoring loops
        self.start_monitoring()

        # Log startup
        self.log_message("Network monitoring tool started successfully", "INFO")

    def setup_gui(self):
        """Setup the main GUI interface"""
        # Title with status indicator
        title_frame = tk.Frame(self.root, bg="#f0f0f0")
        title_frame.pack(fill="x", pady=10)

        title_label = tk.Label(title_frame, text="🌐 Network Monitoring Tool v2.0", 
                              font=("Helvetica", 20, "bold"), bg="#f0f0f0", fg="#2c3e50")
        title_label.pack(side="left", padx=20)

        self.status_indicator = tk.Label(title_frame, text="🟢 ACTIVE", 
                                        font=("Arial", 12, "bold"), bg="#f0f0f0", fg="#27ae60")
        self.status_indicator.pack(side="right", padx=20)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=10)

        # Create all tabs
        self.create_dashboard_tab()
        self.create_bandwidth_tab()
        self.create_devices_tab()
        self.create_topology_tab()
        self.create_logs_tab()

        # Footer with additional info
        footer_frame = tk.Frame(self.root, bg="#f0f0f0")
        footer_frame.pack(fill="x", pady=5)

        footer_label = tk.Label(footer_frame, text="Developed by Team Shubh | Network Security & Monitoring", 
                               font=("Arial", 10), bg="#f0f0f0", fg="#7f8c8d")
        footer_label.pack(side="left", padx=20)

        time_label = tk.Label(footer_frame, text="", font=("Arial", 10), bg="#f0f0f0", fg="#7f8c8d")
        time_label.pack(side="right", padx=20)
        self.time_label = time_label

    def create_dashboard_tab(self):
        """Create dashboard overview tab"""
        self.dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dashboard_frame, text="📊 Dashboard")

        # Quick stats cards
        stats_frame = tk.Frame(self.dashboard_frame)
        stats_frame.pack(fill="x", padx=20, pady=20)

        # Network Status Card
        self.create_stat_card(stats_frame, "Network Status", "🌐", "#27ae60", 0, 0)
        self.network_status_value = tk.Label(stats_frame, text="Connected", font=("Arial", 14, "bold"))
        self.network_status_value.grid(row=1, column=0, padx=20, pady=5)

        # Active Devices Card
        self.create_stat_card(stats_frame, "Active Devices", "🖥️", "#3498db", 0, 1)
        self.devices_count_value = tk.Label(stats_frame, text="0", font=("Arial", 14, "bold"))
        self.devices_count_value.grid(row=1, column=1, padx=20, pady=5)

        # Current Speed Card
        self.create_stat_card(stats_frame, "Current Speed", "⚡", "#e74c3c", 0, 2)
        self.speed_value = tk.Label(stats_frame, text="0 KB/s", font=("Arial", 14, "bold"))
        self.speed_value.grid(row=1, column=2, padx=20, pady=5)

        # Alerts Today Card
        self.create_stat_card(stats_frame, "Alerts Today", "⚠️", "#f39c12", 0, 3)
        self.alerts_count_value = tk.Label(stats_frame, text="0", font=("Arial", 14, "bold"))
        self.alerts_count_value.grid(row=1, column=3, padx=20, pady=5)

        # Quick Actions
        actions_frame = ttk.LabelFrame(self.dashboard_frame, text="Quick Actions", padding=15)
        actions_frame.pack(fill="x", padx=20, pady=10)

        tk.Button(actions_frame, text="🔍 Quick Scan", command=self.quick_scan,
                 bg="#3498db", fg="white", font=("Arial", 11, "bold"), width=15).pack(side="left", padx=10)
        tk.Button(actions_frame, text="📊 Generate Report", command=self.generate_report,
                 bg="#9b59b6", fg="white", font=("Arial", 11, "bold"), width=15).pack(side="left", padx=10)
        tk.Button(actions_frame, text="⚠️ Test Alert", command=self.test_alert,
                 bg="#e74c3c", fg="white", font=("Arial", 11, "bold"), width=15).pack(side="left", padx=10)

        # Recent Activity
        activity_frame = ttk.LabelFrame(self.dashboard_frame, text="Recent Activity", padding=10)
        activity_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.activity_text = scrolledtext.ScrolledText(activity_frame, height=12, wrap=tk.WORD,
                                                      font=("Consolas", 10))
        self.activity_text.pack(fill="both", expand=True)

    def create_stat_card(self, parent, title, icon, color, row, col):
        """Create a statistics card"""
        card_frame = tk.Frame(parent, bg=color, relief="raised", bd=2)
        card_frame.grid(row=row, column=col, padx=15, pady=10, sticky="ew")
        parent.grid_columnconfigure(col, weight=1)

        icon_label = tk.Label(card_frame, text=icon, font=("Arial", 24), bg=color, fg="white")
        icon_label.pack(pady=(10, 0))

        title_label = tk.Label(card_frame, text=title, font=("Arial", 12, "bold"), bg=color, fg="white")
        title_label.pack(pady=(0, 10))

    def create_bandwidth_tab(self):
        """Create enhanced bandwidth monitoring tab"""
        self.bandwidth_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.bandwidth_frame, text="📶 Bandwidth Monitor")

        # Real-time stats
        stats_frame = ttk.LabelFrame(self.bandwidth_frame, text="Real-time Network Statistics", padding=15)
        stats_frame.pack(fill="x", padx=20, pady=10)

        # Speed indicators
        speed_frame = tk.Frame(stats_frame)
        speed_frame.pack(fill="x", pady=10)

        self.upload_label = tk.Label(speed_frame, text="↑ Upload: 0 KB/s", 
                                    font=("Arial", 16, "bold"), fg="#e74c3c")
        self.upload_label.pack(side="left", padx=30)

        self.download_label = tk.Label(speed_frame, text="↓ Download: 0 KB/s", 
                                      font=("Arial", 16, "bold"), fg="#3498db")
        self.download_label.pack(side="right", padx=30)

        # Total statistics
        total_frame = tk.Frame(stats_frame)
        total_frame.pack(fill="x", pady=10)

        self.total_sent_label = tk.Label(total_frame, text="📤 Total Sent: 0 MB", font=("Arial", 12))
        self.total_sent_label.pack(side="left", padx=30)

        self.total_recv_label = tk.Label(total_frame, text="📥 Total Received: 0 MB", font=("Arial", 12))
        self.total_recv_label.pack(side="right", padx=30)

        # Interface statistics
        interface_frame = ttk.LabelFrame(self.bandwidth_frame, text="Network Interfaces", padding=10)
        interface_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.interface_tree = ttk.Treeview(interface_frame, 
                                          columns=("Interface", "Sent", "Received", "Packets Out", "Packets In"), 
                                          show="headings", height=6)

        for col in self.interface_tree["columns"]:
            self.interface_tree.heading(col, text=col)
            self.interface_tree.column(col, width=120)

        interface_scrollbar = ttk.Scrollbar(interface_frame, orient="vertical", command=self.interface_tree.yview)
        self.interface_tree.configure(yscrollcommand=interface_scrollbar.set)

        self.interface_tree.pack(side="left", fill="both", expand=True)
        interface_scrollbar.pack(side="right", fill="y")

        # Controls
        control_frame = tk.Frame(self.bandwidth_frame)
        control_frame.pack(fill="x", padx=20, pady=10)

        self.monitor_button = tk.Button(control_frame, text="⏸️ Pause Monitoring", 
                                       command=self.toggle_monitoring,
                                       bg="#f39c12", fg="white", font=("Arial", 11, "bold"))
        self.monitor_button.pack(side="left", padx=10)

        tk.Button(control_frame, text="🔄 Refresh Interfaces", command=self.refresh_interfaces,
                 bg="#95a5a6", fg="white", font=("Arial", 11, "bold")).pack(side="left", padx=10)
        

    def create_sniffer_tab(self):
        self.sniffer_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.sniffer_tab, text="Packet Sniffer")
        stats_frame = ttk.LabelFrame(self.sniffer_tab, text="TCP/UDP Packets", padding=10)
        stats_frame.pack(fill="x", padx=10, pady=10)

        self.tcp_label = tk.Label(stats_frame, text="TCP Packets: 0", font=("Arial", 14))
        self.tcp_label.grid(row=0, column=0, padx=20)
        self.udp_label = tk.Label(stats_frame, text="UDP Packets: 0", font=("Arial", 14))
        self.udp_label.grid(row=0, column=1, padx=20)

        self.sniff_button = tk.Button(stats_frame, text="Start Sniffing", command=self.start_sniffing)
        self.sniff_button.grid(row=1, column=0, padx=20)
        self.stop_button = tk.Button(stats_frame, text="Stop Sniffing", command=self.stop_sniffing)
        self.stop_button.grid(row=1, column=1, padx=20)

    def update_sniffer_stats(self, tcp, udp):
        self.tcp_label.config(text=f"TCP Packets: {tcp}")
        self.udp_label.config(text=f"UDP Packets: {udp}")

    def start_sniffing(self):
        self.packet_sniffer.sniff_packets(update_callback=self.update_sniffer_stats)

    def stop_sniffing(self):
        self.packet_sniffer.stop_sniffing()





    def create_devices_tab(self):
        """Create enhanced devices discovery tab"""
        self.devices_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.devices_frame, text="🖥️ Device Scanner")

        # Scan controls
        control_frame = tk.Frame(self.devices_frame)
        control_frame.pack(fill="x", padx=20, pady=15)

        tk.Button(control_frame, text="🔍 Full Network Scan", command=self.full_network_scan,
                 bg="#27ae60", fg="white", font=("Arial", 12, "bold")).pack(side="left", padx=10)

        tk.Button(control_frame, text="⚡ Quick Scan", command=self.quick_scan,
                 bg="#3498db", fg="white", font=("Arial", 12, "bold")).pack(side="left", padx=10)

        self.scan_status = tk.Label(control_frame, text="Ready to scan", font=("Arial", 11))
        self.scan_status.pack(side="left", padx=30)

        # Scan progress
        self.scan_progress = ttk.Progressbar(control_frame, mode='indeterminate')
        self.scan_progress.pack(side="right", padx=20)

        # Devices table
        devices_frame = ttk.LabelFrame(self.devices_frame, text="Discovered Devices", padding=10)
        devices_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.device_tree = ttk.Treeview(devices_frame, 
                                       columns=("IP", "MAC", "Hostname", "Vendor", "Status", "Response"), 
                                       show="headings")

        # Configure columns
        columns_config = {
            "IP": 120, "MAC": 140, "Hostname": 150, 
            "Vendor": 150, "Status": 80, "Response": 80
        }

        for col, width in columns_config.items():
            self.device_tree.heading(col, text=col)
            self.device_tree.column(col, width=width)

        devices_scrollbar = ttk.Scrollbar(devices_frame, orient="vertical", command=self.device_tree.yview)
        self.device_tree.configure(yscrollcommand=devices_scrollbar.set)

        self.device_tree.pack(side="left", fill="both", expand=True)
        devices_scrollbar.pack(side="right", fill="y")

        # Device details
        details_frame = ttk.LabelFrame(self.devices_frame, text="Device Details", padding=10)
        details_frame.pack(fill="x", padx=20, pady=10)

        self.device_details = tk.Text(details_frame, height=4, wrap=tk.WORD, font=("Consolas", 10))
        self.device_details.pack(fill="x")

        # Bind selection event
        self.device_tree.bind('<<TreeviewSelect>>', self.on_device_select)

    def create_topology_tab(self):
        """Create network topology visualization tab"""
        self.topology_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.topology_frame, text="🗺️ Network Topology")

        # Controls
        control_frame = tk.Frame(self.topology_frame)
        control_frame.pack(fill="x", padx=20, pady=15)

        tk.Button(control_frame, text="🎨 Generate Topology", command=self.generate_topology,
                 bg="#8e44ad", fg="white", font=("Arial", 12, "bold")).pack(side="left", padx=10)

        tk.Label(control_frame, text="Layout:", font=("Arial", 11)).pack(side="left", padx=(30, 5))

        self.layout_var = tk.StringVar(value="spring")
        layout_combo = ttk.Combobox(control_frame, textvariable=self.layout_var, 
                                   values=["spring", "circular", "shell", "random"], width=12)
        layout_combo.pack(side="left", padx=5)

        tk.Button(control_frame, text="💾 Save Image", command=self.save_topology,
                 bg="#95a5a6", fg="white", font=("Arial", 11, "bold")).pack(side="right", padx=10)

        # Topology display area
        self.topology_canvas_frame = tk.Frame(self.topology_frame, bg="white", relief="sunken", bd=2)
        self.topology_canvas_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Network statistics
        stats_frame = ttk.LabelFrame(self.topology_frame, text="Network Statistics", padding=10)
        stats_frame.pack(fill="x", padx=20, pady=10)

        self.topology_stats = tk.Label(stats_frame, text="Generate topology to view statistics", 
                                      font=("Arial", 11))
        self.topology_stats.pack()

    def create_logs_tab(self):
        """Create logs and alerts management tab"""
        self.logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.logs_frame, text="📋 Logs & Alerts")

        # Alert configuration
        config_frame = ttk.LabelFrame(self.logs_frame, text="Alert Configuration", padding=15)
        config_frame.pack(fill="x", padx=20, pady=10)

        # Bandwidth threshold
        tk.Label(config_frame, text="Bandwidth Threshold (KB/s):").grid(row=0, column=0, sticky="w", padx=5)
        self.threshold_entry = tk.Entry(config_frame, width=12)
        self.threshold_entry.insert(0, "1000")
        self.threshold_entry.grid(row=0, column=1, padx=10)

        tk.Button(config_frame, text="Apply", command=self.apply_threshold,
                 bg="#3498db", fg="white", font=("Arial", 10, "bold")).grid(row=0, column=2, padx=10)

        # Alert toggles
        self.alerts_enabled = tk.BooleanVar(value=True)
        tk.Checkbutton(config_frame, text="Enable Bandwidth Alerts", 
                      variable=self.alerts_enabled).grid(row=1, column=0, columnspan=2, sticky="w", pady=10)

        self.device_alerts_enabled = tk.BooleanVar(value=True)
        tk.Checkbutton(config_frame, text="Enable New Device Alerts", 
                      variable=self.device_alerts_enabled).grid(row=1, column=2, sticky="w", pady=10)

        # Logs display
        logs_display_frame = ttk.LabelFrame(self.logs_frame, text="System Logs", padding=10)
        logs_display_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Log controls
        log_control_frame = tk.Frame(logs_display_frame)
        log_control_frame.pack(fill="x", pady=(0, 10))

        tk.Button(log_control_frame, text="🔄 Refresh", command=self.refresh_logs,
                 bg="#3498db", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(log_control_frame, text="🗑️ Clear", command=self.clear_logs,
                 bg="#e74c3c", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(log_control_frame, text="💾 Export", command=self.export_logs,
                 bg="#95a5a6", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)

        # Filter
        tk.Label(log_control_frame, text="Filter:", font=("Arial", 10)).pack(side="right", padx=(20, 5))
        self.log_filter = ttk.Combobox(log_control_frame, values=["All", "INFO", "WARNING", "ERROR"], 
                                      width=10)
        self.log_filter.set("All")
        self.log_filter.pack(side="right", padx=5)

        self.log_text = scrolledtext.ScrolledText(logs_display_frame, height=18, wrap=tk.WORD, 
                                                 font=("Consolas", 10))
        self.log_text.pack(fill="both", expand=True)

    # Event handlers and core functionality
    def start_monitoring(self):
        """Start all monitoring loops"""
        self.monitoring_active = True
        self.update_dashboard()
        self.monitor_bandwidth()
        self.update_time()

    def monitor_bandwidth(self):
        """Monitor bandwidth and update displays"""
        if self.monitoring_active:
            # Get current stats
            stats = self.bandwidth_monitor.get_current_stats()
            if stats:
                # Calculate speeds
                upload_speed, download_speed = self.bandwidth_monitor.calculate_speed(
                    stats['bytes_sent'], stats['bytes_recv']
                )

                # Update GUI
                self.upload_label.config(text=f"↑ Upload: {upload_speed:.1f} KB/s")
                self.download_label.config(text=f"↓ Download: {download_speed:.1f} KB/s")
                self.total_sent_label.config(text=f"📤 Total Sent: {self.bandwidth_monitor.get_size(stats['bytes_sent'])}")
                self.total_recv_label.config(text=f"📥 Total Received: {self.bandwidth_monitor.get_size(stats['bytes_recv'])}")

                # Update dashboard
                self.speed_value.config(text=f"{max(upload_speed, download_speed):.1f} KB/s")

                # Check for alerts
                if self.alerts_enabled.get():
                    self.alerts_manager.check_bandwidth_alert(upload_speed, download_speed)

        # Schedule next update
        self.root.after(1000, self.monitor_bandwidth)

    def update_dashboard(self):
        """Update dashboard statistics"""
        # Update device count
        device_count = len(self.device_scanner.discovered_devices)
        self.devices_count_value.config(text=str(device_count))

        # Update network status (simplified)
        self.network_status_value.config(text="Connected" if device_count > 0 else "Checking...")

        # Schedule next update
        self.root.after(5000, self.update_dashboard)

    def update_time(self):
        """Update time display"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)

    def full_network_scan(self):
        """Perform full network scan"""
        self.scan_status.config(text="Scanning network...")
        self.scan_progress.start()

        def scan_thread():
            try:
                devices = self.device_scanner.scan_network_range(
                    callback=lambda msg: self.root.after(0, lambda: self.scan_status.config(text=msg))
                )

                # Update GUI in main thread
                self.root.after(0, lambda: self.update_device_tree(devices))
                self.root.after(0, lambda: self.scan_progress.stop())

                # Check for new devices
                new_devices = [d for d in devices if d not in self.last_devices]
                if new_devices and self.device_alerts_enabled.get():
                    self.alerts_manager.check_new_device_alert(new_devices)

                self.last_devices = devices.copy()

            except Exception as e:
                self.root.after(0, lambda: self.scan_status.config(text=f"Scan failed: {str(e)}"))
                self.root.after(0, lambda: self.scan_progress.stop())

        threading.Thread(target=scan_thread, daemon=True).start()

    def quick_scan(self):
        """Perform quick scan (placeholder - same as full scan for now)"""
        self.full_network_scan()

    def update_device_tree(self, devices):
        """Update device tree with scan results"""
        # Clear existing items
        for item in self.device_tree.get_children():
            self.device_tree.delete(item)

        # Add discovered devices
        for device in devices:
            self.device_tree.insert("", "end", values=(
                device['ip'],
                device['mac'],
                device['hostname'],
                device['vendor'],
                device.get('status', 'Active'),
                device.get('response_time', 'N/A')
            ))

        self.log_message(f"Device scan completed. Found {len(devices)} devices", "INFO")

    def on_device_select(self, event):
        """Handle device selection in tree"""
        selection = self.device_tree.selection()
        if selection:
            item = self.device_tree.item(selection[0])
            values = item['values']

            details = f"IP Address: {values[0]}\n"
            details += f"MAC Address: {values[1]}\n"
            details += f"Hostname: {values[2]}\n"
            details += f"Vendor: {values[3]}"

            self.device_details.delete(1.0, tk.END)
            self.device_details.insert(1.0, details)

    def generate_topology(self):
        """Generate network topology visualization"""
        devices = self.device_scanner.discovered_devices
        if not devices:
            messagebox.showwarning("No Data", "Please scan network first to discover devices")
            return

        try:
            # Clear previous topology
            for widget in self.topology_canvas_frame.winfo_children():
                widget.destroy()

            # Create topology
            self.network_topology.create_topology_from_devices(devices)
            fig = self.network_topology.create_matplotlib_figure(
                layout_type=self.layout_var.get(),
                figsize=(12, 8)
            )

            if fig:
                # Embed in tkinter
                from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
                canvas = FigureCanvasTkAgg(fig, self.topology_canvas_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill="both", expand=True)

                # Update statistics
                stats = self.network_topology.get_network_stats()
                stats_text = f"Devices: {stats.get('total_devices', 0)} | "
                stats_text += f"Connections: {stats.get('total_connections', 0)} | "
                stats_text += f"Density: {stats.get('network_density', 0):.3f}"
                self.topology_stats.config(text=stats_text)

                self.log_message("Network topology generated successfully", "INFO")

        except Exception as e:
            error_msg = f"Failed to generate topology: {str(e)}"
            messagebox.showerror("Topology Error", error_msg)
            self.log_message(error_msg, "ERROR")

    def save_topology(self):
        """Save topology as image (placeholder)"""
        messagebox.showinfo("Save Topology", "Topology save feature will be implemented")

    def toggle_monitoring(self):
        """Toggle bandwidth monitoring"""
        self.monitoring_active = not self.monitoring_active
        if self.monitoring_active:
            self.monitor_button.config(text="⏸️ Pause Monitoring", bg="#f39c12")
            self.status_indicator.config(text="🟢 ACTIVE", fg="#27ae60")
            self.log_message("Monitoring resumed", "INFO")
        else:
            self.monitor_button.config(text="▶️ Resume Monitoring", bg="#27ae60")
            self.status_indicator.config(text="🟡 PAUSED", fg="#f39c12")
            self.log_message("Monitoring paused", "INFO")

    def refresh_interfaces(self):
        """Refresh network interface statistics"""
        # Clear existing interface data
        for item in self.interface_tree.get_children():
            self.interface_tree.delete(item)

        # Get interface stats
        interfaces = self.bandwidth_monitor.get_interface_stats()
        for interface in interfaces:
            self.interface_tree.insert("", "end", values=(
                interface['interface'],
                interface['bytes_sent'],
                interface['bytes_recv'],
                interface['packets_sent'],
                interface['packets_recv']
            ))

    def apply_threshold(self):
        """Apply bandwidth threshold setting"""
        try:
            threshold = float(self.threshold_entry.get())
            self.alerts_manager.set_bandwidth_threshold(threshold)
            self.log_message(f"Bandwidth threshold set to {threshold} KB/s", "INFO")
            messagebox.showinfo("Settings", f"Bandwidth threshold updated to {threshold} KB/s")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for threshold")

    def log_message(self, message, level="INFO"):
        """Add message to logs"""
        formatted_message = self.alerts_manager.log(level, message)

        # Add to activity feed
        self.activity_text.insert(tk.END, formatted_message + "\n")
        self.activity_text.see(tk.END)

        # Add to main log display
        self.log_text.insert(tk.END, formatted_message + "\n")
        self.log_text.see(tk.END)

        # Keep only last 100 lines in GUI
        lines = self.log_text.get("1.0", tk.END).split("\n")
        if len(lines) > 100:
            self.log_text.delete("1.0", f"{len(lines)-100}.0")

    def clear_logs(self):
        """Clear log display"""
        self.log_text.delete(1.0, tk.END)
        self.activity_text.delete(1.0, tk.END)
        self.log_message("Log display cleared", "INFO")

    def refresh_logs(self):
        """Refresh logs from file"""
        try:
            log_lines = self.alerts_manager.get_log_summary()
            self.log_text.delete(1.0, tk.END)
            for line in log_lines:
                self.log_text.insert(tk.END, line)
            self.log_text.see(tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh logs: {str(e)}")

    def export_logs(self):
        """Export logs to file (placeholder)"""
        messagebox.showinfo("Export Logs", "Log export feature will be implemented")

    def generate_report(self):
        """Generate monitoring report (placeholder)"""
        messagebox.showinfo("Generate Report", "Report generation feature will be implemented")

    def test_alert(self):
        """Test alert system"""
        self.alerts_manager.trigger_alert("Test Alert", "This is a test alert to verify the system is working", "INFO")

    def on_closing(self):
        """Handle application closing"""
        self.log_message("Application shutting down", "INFO")
        self.root.destroy()


def main():
    """Main function to start the application"""
    try:
        root = tk.Tk()
        app = NetworkMonitoringTool(root)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        root.mainloop()
    except ImportError as e:
        print(f"Error: Missing required module - {e}")
        print("Please install required packages with: pip install -r requirements.txt")
    except Exception as e:
        print(f"Error starting application: {e}")


if __name__ == "__main__":
    main()
