# arduino_controller.py - Fixed for ESP8266 relay control
import serial
import serial.tools.list_ports
import time
import logging
import threading

class ArduinoController:
    def __init__(self, port=None, baudrate=9600, auto_reconnect=True):
        self.baudrate = baudrate
        self.auto_reconnect = auto_reconnect
        self.serial = None
        self.connected = False
        self.last_port = port
        
        # Map device IDs to relay numbers (0 or 1)
        # Adjust this mapping based on which devices control which relays
        self.device_to_relay_map = {
            1: 0,  # Living Room Light -> Relay 0 (D1)
            2: 1,  # Bedroom Fan -> Relay 1 (D2)
            3: 0,  # Kitchen Outlet -> Relay 0 (D1) - shares with device 1
            4: 1   # Porch Light -> Relay 1 (D2) - shares with device 2
        }
        
        self.connect(port)
        
        if self.auto_reconnect:
            self.reconnect_thread = threading.Thread(target=self._reconnect_loop, daemon=True)
            self.reconnect_thread.start()
    
    def auto_detect_port(self):
        """Auto-detect Arduino/ESP8266 port"""
        ports = serial.tools.list_ports.comports()
        
        if not ports:
            logging.warning("⚠️ No serial ports found")
            return None
        
        logging.info(f"🔍 Scanning {len(ports)} serial ports...")
        
        for port in ports:
            logging.debug(f"   Checking: {port.device} - {port.description}")
            
            # Look for Arduino, ESP8266, CH340, FTDI, etc.
            if any(keyword in port.description.lower() for keyword in 
                   ['arduino', 'ch340', 'ch341', 'ftdi', 'cp210', 'usb serial', 'usb-serial', 'esp']):
                logging.info(f"✅ Found device: {port.device}")
                logging.info(f"   Description: {port.description}")
                return port.device
            
            # Check device path
            if 'ttyUSB' in port.device or 'ttyACM' in port.device:
                logging.info(f"✅ Found USB serial: {port.device}")
                return port.device
        
        logging.warning("❌ No Arduino/ESP8266 found")
        return None
    
    def connect(self, port=None):
        """Establish connection to Arduino/ESP8266"""
        if port is None:
            port = self.last_port or self.auto_detect_port()
        
        if port is None:
            logging.error("❌ No device port available")
            self.connected = False
            return False
        
        try:
            if self.serial and self.serial.is_open:
                self.serial.close()
            
            self.serial = serial.Serial(port, self.baudrate, timeout=1)
            time.sleep(2)  # Wait for ESP8266 to reset
            
            self.last_port = port
            self.connected = True
            
            logging.info(f"✅ Connected to device on {port}")
            
            # Read welcome messages
            time.sleep(0.5)
            while self.serial.in_waiting:
                response = self.serial.readline().decode('utf-8', errors='ignore').strip()
                if response:
                    logging.info(f"   Device: {response}")
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Connection failed: {e}")
            self.connected = False
            return False
    
    def _reconnect_loop(self):
        """Background reconnection thread"""
        while True:
            if not self.connected:
                logging.info("🔄 Attempting reconnect...")
                self.connect()
            time.sleep(5)
    
    def send_command(self, device_id, state):
        """
        Send relay command in format: "XY\n" where X=relay(0-1), Y=state(0-1)
        
        Examples:
            Device 1 ON  -> "01\n" (Relay 0, State 1)
            Device 1 OFF -> "00\n" (Relay 0, State 0)
            Device 2 ON  -> "11\n" (Relay 1, State 1)
            Device 2 OFF -> "10\n" (Relay 1, State 0)
        """
        if not self.connected:
            logging.warning("⚠️ Device not connected, reconnecting...")
            if not self.connect():
                logging.error("❌ Cannot send command")
                return False
        
        try:
            # Get relay number from device ID
            if device_id not in self.device_to_relay_map:
                logging.error(f"❌ Invalid device_id: {device_id}")
                return False
            
            relay_num = self.device_to_relay_map[device_id]
            state_value = 1 if state else 0
            
            # Format: "XY\n" where X=relay(0-1), Y=state(0-1)
            command = f"{relay_num}{state_value}\n"
            
            self.serial.write(command.encode('utf-8'))
            self.serial.flush()
            
            logging.info(f"📤 Sent: '{command.strip()}' (Device {device_id} → Relay {relay_num} → {'ON' if state_value else 'OFF'})")
            
            # Read response with timeout
            start_time = time.time()
            response_lines = []
            
            while time.time() - start_time < 0.5:  # 500ms timeout
                if self.serial.in_waiting:
                    line = self.serial.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        response_lines.append(line)
                        logging.info(f"📥 ESP8266: {line}")
                time.sleep(0.05)
            
            return True
            
        except serial.SerialException as e:
            logging.error(f"❌ Serial error: {e}")
            self.connected = False
            return False
        except Exception as e:
            logging.error(f"❌ Error: {e}")
            return False
    
    def is_connected(self):
        """Check connection status"""
        if self.serial is None:
            return False
        try:
            return self.serial.is_open and self.connected
        except:
            return False
    
    def get_status(self):
        """Get status info"""
        return {
            'connected': self.is_connected(),
            'port': self.last_port,
            'baudrate': self.baudrate
        }
    
    def disconnect(self):
        """Close connection"""
        self.connected = False
        if self.serial and self.serial.is_open:
            self.serial.close()
            logging.info("🔌 Disconnected")
    
    def __del__(self):
        self.disconnect()


_arduino = None

def get_arduino_controller(port=None, auto_reconnect=True):
    """Get singleton instance"""
    global _arduino
    if _arduino is None:
        _arduino = ArduinoController(port=port, auto_reconnect=auto_reconnect)
    return _arduino
