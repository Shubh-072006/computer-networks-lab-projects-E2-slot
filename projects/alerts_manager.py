
"""
Alerts and Logging Module for Network Monitor
Handles system alerts, notifications, and logging
"""

import logging
import tkinter.messagebox as messagebox
from datetime import datetime
import threading
import queue

class AlertsManager:
    def __init__(self):
        self.setup_logging()
        self.alert_queue = queue.Queue()
        self.alert_handlers = []
        self.bandwidth_threshold = 1000  # KB/s
        self.alerts_enabled = True

    def setup_logging(self):
        """Setup logging configuration"""
        # Create logger
        self.logger = logging.getLogger('NetworkMonitor')
        self.logger.setLevel(logging.DEBUG)

        # Create file handler
        file_handler = logging.FileHandler('network_monitor.log')
        file_handler.setLevel(logging.INFO)

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def log(self, level, message):
        """Log message with specified level"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {level}: {message}"

        if level == "ERROR":
            self.logger.error(message)
        elif level == "WARNING":
            self.logger.warning(message)
        elif level == "INFO":
            self.logger.info(message)
        else:
            self.logger.debug(message)

        return formatted_message

    def check_bandwidth_alert(self, upload_speed, download_speed):
        """Check if bandwidth exceeds threshold"""
        if not self.alerts_enabled:
            return

        if upload_speed > self.bandwidth_threshold:
            alert_msg = f"High upload detected: {upload_speed:.2f} KB/s"
            self.trigger_alert("Bandwidth Alert", alert_msg, "WARNING")

        if download_speed > self.bandwidth_threshold:
            alert_msg = f"High download detected: {download_speed:.2f} KB/s"
            self.trigger_alert("Bandwidth Alert", alert_msg, "WARNING")

    def check_new_device_alert(self, new_devices):
        """Alert when new devices are detected"""
        if not self.alerts_enabled or not new_devices:
            return

        for device in new_devices:
            alert_msg = f"New device detected: {device['ip']} ({device['hostname']})"
            self.trigger_alert("New Device", alert_msg, "INFO")

    def trigger_alert(self, title, message, level="INFO"):
        """Trigger an alert with specified title and message"""
        # Log the alert
        log_msg = f"{title}: {message}"
        self.log(level, log_msg)

        # Show GUI alert (run in main thread)
        if level == "ERROR":
            threading.Thread(target=lambda: messagebox.showerror(title, message), daemon=True).start()
        elif level == "WARNING":
            threading.Thread(target=lambda: messagebox.showwarning(title, message), daemon=True).start()
        else:
            threading.Thread(target=lambda: messagebox.showinfo(title, message), daemon=True).start()

    def set_bandwidth_threshold(self, threshold):
        """Set bandwidth alert threshold"""
        try:
            self.bandwidth_threshold = float(threshold)
            self.log("INFO", f"Bandwidth threshold set to {threshold} KB/s")
        except ValueError:
            self.log("ERROR", f"Invalid threshold value: {threshold}")

    def enable_alerts(self, enabled=True):
        """Enable or disable alerts"""
        self.alerts_enabled = enabled
        status = "enabled" if enabled else "disabled"
        self.log("INFO", f"Alerts {status}")

    def get_log_summary(self):
        """Get summary of recent log entries"""
        try:
            with open('network_monitor.log', 'r') as f:
                lines = f.readlines()
                return lines[-50:]  # Return last 50 lines
        except FileNotFoundError:
            return ["Log file not found"]
        except Exception as e:
            return [f"Error reading log file: {e}"]
