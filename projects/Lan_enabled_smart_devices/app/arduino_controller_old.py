# arduino_controller.py - Enhanced with auto-reconnect
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
        self.last_port = port  # Remember last successful port
        
        # Try to connect
        self.connect(port)
        
        # Start reconnection thread if enabled
        if self.auto_reconnect:
            self.reconnect_thread = threading.Thread(target=self._reconnect_loop, daemon=True)
            self.reconnect_thread.start()
    
    def auto_detect_port(self):
        """Auto-detect Arduino port with detailed logging"""
        ports = serial.tools.list_ports.comports()
        
        if not ports:
            logging.warning("⚠️ No serial ports found")
            return None
        
        logging.info(f"🔍 Scanning {len(ports)} serial ports...")
        
        for port in ports:
            logging.debug(f"   Checking: {port.device} - {port.description}")
            
            # Check for Arduino, CH340, FTDI, or generic USB serial
            if any(keyword in port.description.lower() for keyword in 
                   ['arduino', 'ch340', 'ch341', 'ftdi', 'cp210', 'usb serial']):
                logging.info(f"✅ Found Arduino-like device: {port.device}")
                logging.info(f"   Description: {port.description}")
                logging.info(f"   VID:PID: {port.vid:04x}:{port.pid:04x}" if port.vid else "   No VID/PID")
                return port.device
            
            # Also check device path
            if 'ttyUSB' in port.device or 'ttyACM' in port.device:
                logging.info(f"✅ Found USB serial device: {port.device}")
                return port.device
        
        logging.warning("❌ No Arduino found")
        return None
    
    def connect(self, port=None):
        """Establish connection to Arduino"""
        # Auto-detect if no port specified
        if port is None:
            port = self.last_port or self.auto_detect_port()
        
        if port is None:
            logging.error("❌ No Arduino port available")
            self.connected = False
            return False
        
        try:
            # Close existing connection if any
            if self.serial and self.serial.is_open:
                self.serial.close()
            
            # Open new connection
            self.serial = serial.Serial(port, self.baudrate, timeout=1)
            time.sleep(2)  # Wait for Arduino to reset
            
            self.last_port = port  # Remember successful port
            self.connected = True
            
            logging.info(f"✅ Connected to Arduino on {port}")
            
            # Read welcome message
            if self.serial.in_waiting:
                response = self.serial.readline().decode('utf-8', errors='ignore').strip()
                logging.info(f"   Arduino says: {response}")
            
            return True
            
        except serial.SerialException as e:
            logging.error(f"❌ Failed to connect to Arduino on {port}: {e}")
            self.connected = False
            return False
        except Exception as e:
            logging.error(f"❌ Unexpected error connecting to Arduino: {e}")
            self.connected = False
            return False
    
    def _reconnect_loop(self):
        """Background thread to auto-reconnect when disconnected"""
        while True:
            if not self.connected:
                logging.info("🔄 Attempting to reconnect to Arduino...")
                self.connect()
            time.sleep(5)  # Check every 5 seconds
    
    def send_command(self, device_id, state):
        """
        Send command to Arduino with automatic reconnection
        
        Args:
            device_id (int): Device ID (1-4)
            state (int or bool): 1/True for ON, 0/False for OFF
        
        Returns:
            bool: True if command sent successfully
        """
        # Try to reconnect if not connected
        if not self.connected:
            logging.warning("⚠️ Arduino not connected, attempting reconnect...")
            if not self.connect():
                logging.error("❌ Cannot send command - Arduino not available")
                return False
        
        try:
            # Convert state to 1 or 0
            state_value = 1 if state else 0
            
            # Send command: "device_id state\n"
            command = f"{device_id} {state_value}\n"
            self.serial.write(command.encode('utf-8'))
            self.serial.flush()
            
            logging.info(f"📤 Sent to Arduino: Device {device_id} → {'ON' if state_value else 'OFF'}")
            
            # Wait for confirmation
            time.sleep(0.1)
            if self.serial.in_waiting:
                response = self.serial.readline().decode('utf-8', errors='ignore').strip()
                logging.info(f"📥 Arduino: {response}")
            
            return True
            
        except serial.SerialException as e:
            logging.error(f"❌ Serial error: {e}")
            self.connected = False  # Mark as disconnected
            return False
        except Exception as e:
            logging.error(f"❌ Error sending command: {e}")
            return False
    
    def is_connected(self):
        """Check if Arduino is connected"""
        if self.serial is None:
            return False
        
        try:
            return self.serial.is_open and self.connected
        except:
            return False
    
    def get_status(self):
        """Get connection status"""
        return {
            'connected': self.is_connected(),
            'port': self.last_port,
            'baudrate': self.baudrate
        }
    
    def disconnect(self):
        """Close serial connection"""
        self.connected = False
        if self.serial and self.serial.is_open:
            self.serial.close()
            logging.info("🔌 Disconnected from Arduino")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.disconnect()


# Singleton instance
_arduino = None

def get_arduino_controller(port=None, auto_reconnect=True):
    """Get singleton Arduino controller instance"""
    global _arduino
    if _arduino is None:
        _arduino = ArduinoController(port=port, auto_reconnect=auto_reconnect)
    return _arduino
