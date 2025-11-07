# test_ports.py
import serial.tools.list_ports

ports = serial.tools.list_ports.comports()

if not ports:
    print("❌ NO SERIAL PORTS FOUND!")
    print("This means:")
    print("  - ESP8266 is not connected")
    print("  - USB cable is bad (try another)")
    print("  - Drivers not installed")
else:
    print(f"✅ Found {len(ports)} serial port(s):\n")
    for port in ports:
        print(f"Port: {port.device}")
        print(f"  Description: {port.description}")
        print(f"  Hardware ID: {port.hwid}")
        if port.vid and port.pid:
            print(f"  VID:PID: {port.vid:04x}:{port.pid:04x}")
        print()
