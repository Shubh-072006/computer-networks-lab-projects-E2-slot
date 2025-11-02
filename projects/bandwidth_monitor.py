
"""
Bandwidth Monitoring Module for Network Monitor
Handles real-time bandwidth tracking using psutil
"""

import psutil
import time
from datetime import datetime

class BandwidthMonitor:
    def __init__(self):
        self.prev_sent = 0
        self.prev_recv = 0
        self.start_time = time.time()
        self.total_sent_start = 0
        self.total_recv_start = 0

    def get_size(self, bytes_value):
        """Convert bytes to human readable format"""
        sizes = ['B', 'KB', 'MB', 'GB', 'TB']
        i = 0
        while bytes_value >= 1024 and i < len(sizes) - 1:
            bytes_value /= 1024.0
            i += 1
        return f"{bytes_value:.2f} {sizes[i]}"

    def get_current_stats(self):
        """Get current network I/O statistics"""
        try:
            net_io = psutil.net_io_counters()
            return {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            }
        except Exception as e:
            return None

    def calculate_speed(self, current_sent, current_recv, time_interval=1):
        """Calculate upload and download speeds"""
        if self.prev_sent == 0:
            # First run, initialize
            self.prev_sent = current_sent
            self.prev_recv = current_recv
            self.total_sent_start = current_sent
            self.total_recv_start = current_recv
            return 0, 0

        # Calculate speeds in KB/s
        upload_speed = (current_sent - self.prev_sent) / 1024 / time_interval
        download_speed = (current_recv - self.prev_recv) / 1024 / time_interval

        # Update previous values
        self.prev_sent = current_sent
        self.prev_recv = current_recv

        return upload_speed, download_speed

    def get_interface_stats(self):
        """Get statistics for all network interfaces"""
        try:
            interfaces = psutil.net_io_counters(pernic=True)
            interface_data = []

            for interface, stats in interfaces.items():
                interface_data.append({
                    'interface': interface,
                    'bytes_sent': self.get_size(stats.bytes_sent),
                    'bytes_recv': self.get_size(stats.bytes_recv),
                    'packets_sent': stats.packets_sent,
                    'packets_recv': stats.packets_recv
                })

            return interface_data
        except Exception:
            return []
