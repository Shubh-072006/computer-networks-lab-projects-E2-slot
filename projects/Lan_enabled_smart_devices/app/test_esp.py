# test_esp8266.py
import serial
import time

PORT = '/dev/ttyUSB0'  # Your confirmed port
BAUDRATE = 9600

try:
    print(f"Opening {PORT} at {BAUDRATE} baud...")
    ser = serial.Serial(PORT, BAUDRATE, timeout=1)
    time.sleep(3)  # Wait for ESP8266 reset (critical!)
    
    print("✅ Port opened successfully!")
    print("Waiting for welcome messages (should see 'ESP8266 Relay Controller Ready')...")
    
    # Read initial messages (up to 5 seconds)
    start_time = time.time()
    while time.time() - start_time < 5:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='ignore').rstrip('\r\n')
            if line:
                print(f"  ESP8266: {line}")
        time.sleep(0.1)
    
    # Send test commands (matches your ESP8266 sketch)
    print("\n🧪 Testing commands (watch for relay clicks and responses)...")
    commands = [
        ('01', 'Relay 0 ON'),
        ('00', 'Relay 0 OFF'),
        ('11', 'Relay 1 ON'),
        ('10', 'Relay 1 OFF')
    ]
    
    for cmd, expected in commands:
        print(f"\n   📤 Sending: '{cmd}'")
        full_cmd = f"{cmd}\n"
        ser.write(full_cmd.encode('utf-8'))
        ser.flush()
        time.sleep(0.5)  # Wait for processing
        
        # Read responses
        responses = []
        while ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='ignore').rstrip('\r\n')
            if line:
                responses.append(line)
                print(f"      📥 Response: {line}")
        
        # Check for expected response
        if expected in ' '.join(responses):
            print(f"      ✅ Success: {expected} confirmed")
        else:
            print(f"      ⚠️ Expected: {expected} (got: {responses})")
    
    ser.close()
    print("\n🎉 Test completed! If responses match and relays click, hardware + code are working.")
    print("   If no responses: Check ESP8266 sketch upload, baud rate, or wiring.")
    
except PermissionError as e:
    print(f"❌ Permission denied: {e}")
    print("\n🔧 Fix: Log out and log back in (after 'sudo usermod -a -G dialout $USER')")
    print("   Or try: newgrp dialout")
    exit(1)
    
except serial.SerialException as e:
    print(f"❌ Serial error: {e}")
    print("\n🔧 Troubleshoot:")
    print("   - Is Arduino IDE Serial Monitor open? Close it!")
    print("   - Kill processes: sudo lsof /dev/ttyUSB0 | grep python && sudo kill <PID>")
    print("   - Unplug/replug ESP8266 and re-run dmesg | tail -10")
    exit(1)
    
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    exit(1)
