# Platform Differences - Windows vs Mac

## ✅ **Good News: The System is Cross-Platform!**

Your LAN file transfer system is designed to work identically on **Windows, Mac, and Linux**. The core functionality is the same across all platforms.

## Platform-Specific Considerations

### **Mac (Current Platform)**
```bash
# All commands work the same
python main.py server-gui
python main.py client-gui
python main.py server-cli --port 8888
python main.py discover
```

**Mac-specific features:**
- ✅ **Tkinter GUI** works natively
- ✅ **Network discovery** works with UDP broadcasts
- ✅ **File paths** use forward slashes `/`
- ✅ **Permissions** handled automatically

### **Windows**
```cmd
# Same commands, but use cmd or PowerShell
python main.py server-gui
python main.py client-gui
python main.py server-cli --port 8888
python main.py discover
```

**Windows-specific considerations:**
- ✅ **Tkinter GUI** works (comes with Python)
- ✅ **Network discovery** works the same
- ⚠️ **File paths** can use backslashes `\` or forward slashes `/`
- ⚠️ **Firewall** might block ports (need to allow Python through firewall)
- ⚠️ **Antivirus** might scan transferred files

### **Linux**
```bash
# Identical to Mac
python3 main.py server-gui
python3 main.py client-gui
python3 main.py server-cli --port 8888
python3 main.py discover
```

## Network Differences

### **Local Network Discovery**
- **Mac/Linux**: UDP broadcasts work seamlessly
- **Windows**: May need firewall configuration for UDP broadcasts
- **All platforms**: Can use manual IP entry if discovery fails

### **File Transfer**
- **All platforms**: TCP file transfer works identically
- **All platforms**: MD5 hash verification works the same
- **All platforms**: Progress tracking works the same

## Testing on Different Platforms

### **Mac Testing (Current)**
```bash
# Test basic functionality
python test_system.py

# Test GUI
python main.py server-gui  # In one terminal
python main.py client-gui  # In another terminal

# Test CLI
python main.py server-cli --port 8888  # In one terminal
python main.py discover                # In another terminal
```

### **Windows Testing**
```cmd
# Same commands, but in Command Prompt or PowerShell
python test_system.py
python main.py server-gui
python main.py client-gui
python main.py server-cli --port 8888
python main.py discover
```

### **Cross-Platform Testing**
1. **Run server on Mac**: `python main.py server-cli --port 8888`
2. **Run client on Windows**: `python main.py client-cli --server [MAC_IP] --port 8888 --file test.txt`
3. **Verify file transfer** works between platforms

## Potential Issues & Solutions

### **Windows Firewall**
- **Problem**: Windows Firewall might block connections
- **Solution**: Allow Python through firewall or disable firewall for testing

### **Network Permissions**
- **Problem**: Some networks block UDP broadcasts
- **Solution**: Use manual IP entry instead of discovery

### **File Permissions**
- **Problem**: Different file permission systems
- **Solution**: System handles this automatically with safe filename creation

### **Path Differences**
- **Problem**: Windows uses `\` vs Mac/Linux using `/`
- **Solution**: Python's `pathlib` handles this automatically
