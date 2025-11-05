# 🖥️ **LAN File Transfer System - Windows Deployment Manual**

## **📋 Prerequisites for Windows**

### **System Requirements**
- **Operating System**: Windows 10, Windows 11, or Windows Server 2016+
- **Python**: Version 3.7 or higher
- **Network**: Local network access (WiFi/Ethernet)
- **Ports**: 8080 (web interface), 8888 (file transfer), 8889 (discovery)

### **Check Python Installation**
```cmd
python --version
```
If Python is not installed, download from [python.org](https://www.python.org/downloads/)

## **🚀 Installation Steps for Windows**

### **Step 1: Download/Extract the Project**
```cmd
# Navigate to your desired directory
cd C:\Users\%USERNAME%\Desktop

# If you have the files in a ZIP folder, extract them
# Create a folder called "lan_file_transfer" and extract all files there
```

### **Step 2: Open Command Prompt as Administrator**
```cmd
# Press Windows + R, type "cmd", press Ctrl + Shift + Enter
# Or right-click Start button → "Windows PowerShell (Admin)"
```

### **Step 3: Navigate to Project Directory**
```cmd
cd C:\Users\%USERNAME%\Desktop\lan_file_transfer
```

### **Step 4: Install Dependencies**
```cmd
# Install required Python packages
pip install Flask==2.3.3 Werkzeug==2.3.7

# Or if you have a requirements.txt file:
pip install -r requirements.txt
```

### **Step 5: Verify Installation**
```cmd
python main.py --help
```

## **🌐 Running the Web Interface (Recommended)**

### **Step 1: Start the Web Server**
```cmd
python web_server.py
```

**Expected Output:**
```
🌐 LAN File Transfer - Web Interface
==================================================
Local access: http://localhost:8080
Network access: http://192.168.1.100:8080
==================================================
📱 Works on any device with a web browser!
🖥️  Windows, Mac, Linux, iPhone, Android, iPad
==================================================
 * Serving Flask app 'web_server'
 * Debug mode: on
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8080
 * Running on http://192.168.1.100:8080
```

### **Step 2: Access the Interface**
- **Local access**: `http://localhost:8080`
- **Network access**: `http://YOUR_WINDOWS_IP:8080`
- **Mobile access**: `http://YOUR_WINDOWS_IP:8080` (works on any device)

### **Step 3: Start File Transfer Server**
1. Open the web interface in your browser
2. Click **"Start Server"** button
3. Wait for "Server Running" status
4. The system is now ready to receive files

## **🔧 Windows-Specific Configuration**

### **Find Your Windows IP Address**
```cmd
# Method 1: Using ipconfig
ipconfig

# Method 2: Using PowerShell
Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*" -or $_.IPAddress -like "172.*"}
```

### **Windows Firewall Configuration**
```cmd
# Allow required ports through Windows Firewall
netsh advfirewall firewall add rule name="LAN File Transfer Web" dir=in action=allow protocol=TCP localport=8080
netsh advfirewall firewall add rule name="LAN File Transfer Server" dir=in action=allow protocol=TCP localport=8888
netsh advfirewall firewall add rule name="LAN File Transfer Discovery" dir=in action=allow protocol=UDP localport=8889
```

**Alternative: GUI Method**
1. Open **Windows Defender Firewall**
2. Click **"Allow an app or feature through Windows Defender Firewall"**
3. Click **"Change settings"** → **"Allow another app..."**
4. Browse to your Python installation and add rules for ports 8080, 8888, 8889

## **🖥️ Alternative: Desktop GUI Applications**

### **Server GUI**
```cmd
python main.py server-gui
```

### **Client GUI**
```cmd
python main.py client-gui
```

## **⌨️ Alternative: Command Line Interface**

### **Start Server (CLI)**
```cmd
python main.py server-cli --port 8888 --password mypassword
```

### **Send File (CLI)**
```cmd
python main.py client-cli --server 192.168.1.100 --port 8888 --file "C:\Users\Username\Documents\file.txt"
```

### **Discover Servers**
```cmd
python main.py discover
```

## **🔒 Windows Security Considerations**

### **Antivirus Software**
- **Windows Defender**: May need to allow Python through firewall
- **Third-party antivirus**: May need to whitelist the project folder
- **Real-time protection**: May temporarily disable during first run

### **User Account Control (UAC)**
```cmd
# If you get permission errors, run Command Prompt as Administrator
# Right-click Command Prompt → "Run as administrator"
```

### **Windows Defender SmartScreen**
- If you get a warning about "Windows protected your PC", click **"More info"** → **"Run anyway"**

## **🚀 Production Deployment on Windows**

### **Using Waitress (Recommended for Windows)**
```cmd
# Install Waitress
pip install waitress

# Run with Waitress
waitress-serve --host=0.0.0.0 --port=8080 web_server:app
```

### **Windows Service (Advanced)**
```cmd
# Install pywin32
pip install pywin32

# Create a service script (service_installer.py)
python service_installer.py install
python service_installer.py start
```

### **Batch File for Easy Startup**
Create `start_server.bat`:
```batch
@echo off
cd /d "C:\Users\%USERNAME%\Desktop\lan_file_transfer"
python web_server.py
pause
```

## **🔍 Windows Troubleshooting**

### **Port Already in Use**
```cmd
# Check what's using the port
netstat -ano | findstr :8080

# Kill process using port (replace PID with actual process id)
taskkill /PID <PID> /F
```

### **Permission Denied**
```cmd
# Run Command Prompt as Administrator
# Right-click Command Prompt → "Run as administrator"
```

### **Python Not Found**
```cmd
# Add Python to PATH
# Go to System Properties → Environment Variables → PATH
# Add: C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python39\
# Or reinstall Python with "Add to PATH" option checked
```

### **Network Access Issues**
```cmd
# Check if server is accessible
curl http://localhost:8080

# Check Windows Firewall status
netsh advfirewall show allprofiles
```

### **File Transfer Failures**
```cmd
# Check server logs
type logs\transfer_log.txt

# Verify server is running
netstat -an | findstr 8888
```

## **📊 Windows Monitoring & Logs**

### **Log Files Location**
```cmd
# Main log file
type logs\transfer_log.txt

# Web server logs (console output)
# Check Command Prompt window where web_server.py is running
```

### **Server Status Check**
```cmd
# Check if server is running
curl http://localhost:8080/api/server/status

# Check network info
curl http://localhost:8080/api/network/info
```

## **🔄 Windows Backup & Recovery**

### **Backup Configuration**
```cmd
# Backup important files
copy config.py config.py.backup
xcopy logs logs_backup /E /I
```

### **Recovery**
```cmd
# Restore configuration
copy config.py.backup config.py

# Restore logs
xcopy logs_backup logs /E /I
```

## **📈 Windows Performance Optimization**

### **Large File Transfers**
```python
# In config.py, adjust buffer sizes
BUFFER_SIZE = 8192  # Increase for faster transfers
CHUNK_SIZE = 2048   # Increase chunk size
```

### **Windows Defender Exclusions**
1. Open **Windows Security**
2. Go to **Virus & threat protection**
3. Click **"Manage settings"** under Virus & threat protection settings
4. Click **"Add or remove exclusions"**
5. Add your project folder to exclusions

## **🎯 Windows Quick Start Checklist**

- [ ] Install Python 3.7+ from python.org
- [ ] Extract project files to a folder
- [ ] Open Command Prompt as Administrator
- [ ] Navigate to project directory: `cd C:\path\to\lan_file_transfer`
- [ ] Install dependencies: `pip install Flask Werkzeug`
- [ ] Configure Windows Firewall for ports 8080, 8888, 8889
- [ ] Run: `python web_server.py`
- [ ] Access: `http://YOUR_WINDOWS_IP:8080`
- [ ] Click "Start Server" in web interface
- [ ] Test file transfer from another device
- [ ] Add project folder to Windows Defender exclusions

## **📞 Windows Support**

### **Common Windows Issues**
1. **Port conflicts**: Change ports in config.py
2. **Permission denied**: Run Command Prompt as Administrator
3. **Network access**: Check Windows Firewall and IP address
4. **File transfer fails**: Verify server is running and password is correct
5. **Antivirus blocking**: Add project folder to exclusions

### **Windows Log Analysis**
```cmd
# Check for errors
findstr /i "error" logs\transfer_log.txt

# Check successful transfers
findstr /i "success" logs\transfer_log.txt
```

### **Windows Network Diagnostics**
```cmd
# Test network connectivity
ping 192.168.1.100

# Check port availability
telnet 192.168.1.100 8080
```

## **🔄 Windows Startup Scripts**

### **Create Desktop Shortcut**
1. Right-click on desktop → **"New"** → **"Shortcut"**
2. Enter: `cmd /c "cd /d C:\path\to\lan_file_transfer && python web_server.py"`
3. Name it: "LAN File Transfer Server"

### **Windows Startup Folder**
1. Press **Windows + R**, type `shell:startup`
2. Create a batch file with the startup command
3. The server will start automatically when Windows boots

## **📱 Client Access (Any Device)**

### **Desktop Browsers**
- **Windows**: Chrome, Firefox, Edge, Safari
- **macOS**: Safari, Chrome, Firefox
- **Linux**: Chrome, Firefox, Opera

### **Mobile Browsers**
- **iPhone**: Safari, Chrome, Firefox
- **Android**: Chrome, Firefox, Samsung Internet
- **iPad**: Safari, Chrome, Firefox

### **Access URL**
```
http://YOUR_WINDOWS_IP:8080
```

## **🔒 Security Features**

### **Password Authentication**
- Default password: `lan_transfer_2024`
- Change in `config.py` or via command line
- Required for all file transfers

### **File Integrity Verification**
- MD5 hash verification ensures file integrity
- Automatic corruption detection
- Failed transfers are logged and reported

### **Safe Filename Handling**
- Prevents path traversal attacks
- Sanitizes filenames automatically
- Removes invalid characters

## **📊 System Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                    LAN File Transfer System                     │
├─────────────────────────────────────────────────────────────────┤
│  Interface Layer: CLI, GUI, Web                                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │    CLI      │ │    GUI      │ │    Web      │              │
│  │ (main.py)   │ │(gui_*.py)   │ │(web_server) │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
├─────────────────────────────────────────────────────────────────┤
│  Core Logic Layer: Server, Client, Discovery                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │   Server    │ │   Client    │ │ Discovery   │              │
│  │(server.py)  │ │(client.py)  │ │(discovery)  │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
├─────────────────────────────────────────────────────────────────┤
│  Support Layer: Utils, Config                                  │
│  ┌─────────────┐ ┌─────────────┐                              │
│  │   Utils     │ │   Config    │                              │
│  │(utils.py)   │ │(config.py)  │                              │
│  └─────────────┘ └─────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```

## **🌍 Cross-Platform Compatibility**

### **Server Platforms**
- ✅ **Windows**: Full support via Python
- ✅ **macOS**: Full support via Python  
- ✅ **Linux**: Full support via Python

### **Client Platforms**
- ✅ **Windows**: Web interface, GUI, CLI
- ✅ **macOS**: Web interface, GUI, CLI
- ✅ **Linux**: Web interface, GUI, CLI
- ✅ **iPhone/Android**: Web interface (mobile-optimized)
- ✅ **iPad/Tablets**: Web interface (touch-optimized)

## **📈 Performance Specifications**

### **File Transfer Limits**
- **Maximum file size**: 100MB (configurable)
- **Concurrent transfers**: Multiple clients supported
- **Transfer speed**: Limited by network bandwidth
- **Buffer size**: 4KB default (configurable)

### **Network Requirements**
- **TCP Port 8888**: File transfer protocol
- **UDP Port 8889**: Server discovery
- **HTTP Port 8080**: Web interface
- **Local network**: WiFi or Ethernet connection

## **🔄 File Transfer Process**

### **Complete Workflow**
1. **Server Setup**: Start web server and file transfer server
2. **Client Discovery**: Automatic server discovery via UDP broadcast
3. **Authentication**: Password-based security verification
4. **File Transfer**: TCP-based file transfer with progress tracking
5. **Integrity Check**: MD5 hash verification
6. **Completion**: Success/failure notification and logging

### **Security Protocol**
```
1. Client → Server: TCP connection
2. Server → Client: {"type": "auth_request"}
3. Client → Server: {"type": "auth_response", "password": "..."}
4. Server → Client: {"type": "auth_success"} or {"type": "auth_failure"}
5. Client → Server: {"type": "file_metadata", "filename": "...", "size": 123, "hash": "..."}
6. Server → Client: {"type": "ready_for_transfer"}
7. Client → Server: [File data in chunks]
8. Server → Client: {"type": "transfer_success"} or {"type": "transfer_error"}
```

## **📞 Technical Support**

### **System Requirements Verification**
```cmd
# Check Python version
python --version

# Check network connectivity
ping 8.8.8.8

# Check port availability
netstat -an | findstr :8080
```

### **Common Error Messages**
- **"Port already in use"**: Another service is using the port
- **"Permission denied"**: Run as Administrator
- **"Python not found"**: Add Python to system PATH
- **"Authentication failed"**: Check password configuration
- **"File transfer failed"**: Verify server is running and network connectivity

### **Log File Locations**
- **Main log**: `logs/transfer_log.txt`
- **Console output**: Command Prompt window
- **Web server logs**: Flask debug output

---

**This manual provides everything needed to deploy and run the LAN File Transfer System on Windows, from basic setup to production deployment with proper security configurations.**
