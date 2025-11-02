
"""
Device Scanner Module for Network Monitor
Handles network device discovery using ARP scanning
"""

import scapy.all as scapy
import socket
import subprocess
import platform
import threading

class DeviceScanner:
    def __init__(self):
        self.discovered_devices = []
        self.scan_in_progress = False

    def get_local_network(self):
        """Get local network range"""
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            network_base = '.'.join(local_ip.split('.')[:-1]) + '.0/24'
            return network_base, local_ip
        except Exception:
            # Fallback to common network ranges
            return "192.168.1.0/24", "192.168.1.100"

    def arp_scan(self, ip_range):
        """Perform ARP scan to discover devices"""
        try:
            # Create ARP request
            arp_request = scapy.ARP(pdst=ip_range)
            broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
            arp_request_broadcast = broadcast / arp_request

            # Send request and get responses
            answered_list = scapy.srp(arp_request_broadcast, timeout=3, verbose=False)[0]

            devices = []
            for element in answered_list:
                device_info = {
                    'ip': element[1].psrc,
                    'mac': element[1].hwsrc,
                    'vendor': self.get_vendor_info(element[1].hwsrc),
                    'hostname': self.get_hostname(element[1].psrc)
                }
                devices.append(device_info)

            return devices
        except Exception as e:
            print(f"ARP scan failed: {e}")
            return []

    def get_vendor_info(self, mac_address):
        """Get vendor information from MAC address"""
        # Simplified vendor lookup (in real app, use proper OUI database)
        mac_prefixes = {
            "00:1B:44": "Cisco Systems",
            "00:50:56": "VMware",
            "08:00:27": "VirtualBox",
            "52:54:00": "QEMU Virtual NIC",
            "00:0C:29": "VMware",
            "00:15:5D": "Microsoft Corporation",
            "00:16:3E": "Xensource",
            "00:1C:14": "Cisco Systems",
            "D8:50:E6": "ASRock Incorporation",
            "B4:2E:99": "Apple Inc",
            "AC:BC:32": "Apple Inc",
            "F0:18:98": "Apple Inc"
        }

        mac_prefix = mac_address.upper()[:8]
        return mac_prefixes.get(mac_prefix, "Unknown Vendor")

    def get_hostname(self, ip_address):
        """Try to get hostname from IP address"""
        try:
            hostname = socket.gethostbyaddr(ip_address)[0]
            return hostname
        except:
            return "Unknown"

    def ping_host(self, host):
        """Ping a host to check if it's alive"""
        try:
            # Use platform-appropriate ping command
            param = "-n" if platform.system().lower() == "windows" else "-c"
            command = ["ping", param, "1", host]
            result = subprocess.run(command, capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False

    def scan_network_range(self, callback=None):
        """Scan network and return discovered devices"""
        self.scan_in_progress = True
        network_range, local_ip = self.get_local_network()

        if callback:
            callback(f"Scanning network: {network_range}")

        # Perform ARP scan
        devices = self.arp_scan(network_range)

        # Add additional information
        for device in devices:
            device['status'] = 'Active'
            device['response_time'] = self.ping_response_time(device['ip'])

        self.discovered_devices = devices
        self.scan_in_progress = False

        if callback:
            callback(f"Scan complete. Found {len(devices)} devices")

        return devices

    def ping_response_time(self, host):
        """Get ping response time"""
        try:
            param = "-n" if platform.system().lower() == "windows" else "-c"
            command = ["ping", param, "1", host]
            result = subprocess.run(command, capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                # Extract response time (simplified)
                output = result.stdout
                if "time=" in output:
                    time_str = output.split("time=")[1].split()[0]
                    return f"{time_str}ms"
            return "N/A"
        except:
            return "N/A"
