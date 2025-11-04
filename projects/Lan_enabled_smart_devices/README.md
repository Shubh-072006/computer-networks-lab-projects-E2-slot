# Custom-Built Embedded Router for Decentralized, Privacy-Focused Smart Home Automation

## Project Overview

This repository contains a complete implementation of a decentralized IoT smart home automation system developed for the Computer Networks course at VIT Chennai (Fall 2025-26). The system uses a custom-built embedded router with a secure local network, ESP8266-based relay modules for appliance control, and a Flask web dashboard running on a Debian VM via QEMU/KVM.

**Key Principle**: Privacy-focused, offline-capable, zero cloud dependency.

### Team Members
- **Saikat De** -- 24BCE1172
- **Aditya Saxena** -- 24BCE1633
- **Rishav Kumar** -- 24BCE1666

**Faculty**: Dr. Amrit Pal | **Slot**: L27 + L28 | **Institution**: VIT Chennai

---

## 🎯 Project Features

✅ **Custom Embedded Router**: Acts as Access Point with DHCP, MAC filtering, firewall/NAT  
✅ **ESP8266 Relay Control**: Serial commands ("01"/"00"/"11"/"10") toggle appliances via GPIO D1/D2  
✅ **Flask Web Dashboard**: SQLite-backed app running on Debian VM (QEMU/KVM) at `http://<VM-IP>:5001`  
✅ **Network Security**: IPv4 forwarding, iptables-based MAC whitelisting, established/related inbound only  
✅ **Offline Operation**: Works without internet; all data local  
✅ **Auto-Reconnect**: Handles ESP8266 disconnect/reconnect within 5 seconds  

---

## 📦 Materials Required

| SL. | Component | Purpose | Cost |
|-----|-----------|---------|------|
| 1 | ESP8266 | Logic & serial control | — |
| 2 | Relay Module (2-channel) | Power switching (AC appliances) | Rs. 200.00 |
| 3 | WiFi USB Adapter | Create Access Point | Rs. 300.00 |
| 4 | Bulb + Holder | Demo (visual feedback) | Rs. 150.00 |
| 5 | Custom Router | Routing, DHCP, firewall | Rs. 800-1000 |
| 6 | Connecting Wires | Internal circuit connections | Rs. 150.00 |
| **Total** | | | **Rs. 1600-1800** |

---

## ⚙️ System Architecture

```
┌─────────────────────────────────────────────┐
│          Host Machine (Linux)                │
│  ┌────────────────────────────────────────┐  │
│  │  QEMU/KVM Virtualization               │  │
│  │  ┌──────────────────────────────────┐  │  │
│  │  │  Debian VM (2GB RAM, 20GB disk)  │  │  │
│  │  │  ┌────────────────────────────┐  │  │  │
│  │  │  │  Flask Web App             │  │  │  │
│  │  │  │  ├─ app.py (main)         │  │  │  │
│  │  │  │  ├─ arduino_controller.py │  │  │  │
│  │  │  │  ├─ dashboard.html        │  │  │  │
│  │  │  │  └─ dashboard.db (SQLite) │  │  │  │
│  │  │  └──────────┬─────────────────┘  │  │  │
│  │  └─────────────┼────────────────────┘  │  │
│  └────────────────┼──────────────────────┘  │
│                   │ USB Passthrough         │
│                   ▼                         │
│          Serial: /dev/ttyUSB0              │
└─────────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
    ┌─────────────┐       ┌──────────────┐
    │   ESP8266   │       │   Router     │
    │  D1: Relay0 │       │ (hostapd)    │
    │  D2: Relay1 │       │ (dnsmasq)    │
    │ (9600 baud) │       │ (iptables)   │
    └─────────────┘       └──────────────┘
         │                       │
    ┌────┴────┐            ┌─────┴──────┐
    │   Bulb  │            │   WiFi LAN │
    │   Fan   │            │ (isolated) │
    └─────────┘            └────────────┘
```

**Data Flow**: 
1. Client connects to WiFi AP (SmartHomeAP)
2. Gets DHCP IP from router (192.168.100.x)
3. Accesses Flask dashboard at VM IP:5001
4. Clicks toggle → Flask sends serial command ("01") to ESP8266
5. ESP8266 switches relay → Appliance turns ON/OFF
6. Status syncs to SQLite, displayed on dashboard

---

## 📋 Prerequisites

### Host Machine (Router)
- Linux OS (Debian/Ubuntu recommended)
- Interfaces: 
  - **WAN**: `enp1s0` (Ethernet, DHCP from ISP)
  - **LAN**: `wlxd03745f84230` (WiFi USB adapter)
- Root/sudo access for network config

### Software (Host)
```bash
sudo apt update && sudo apt install \
  qemu-kvm libvirt-daemon-system libvirt-clients \
  virt-manager bridge-utils \
  hostapd dnsmasq iptables-persistent
```

### Hardware
- ESP8266 NodeMCU
- 2-channel relay module (5V)
- WiFi USB adapter (e.g., TP-Link Archer T2U Nano)
- Connecting wires, breadboard
- AC bulb + holder (or fan)

---

## 🚀 Quick Start

### 1. Router Setup (Host Machine)

#### Enable IPv4 Forwarding (CRITICAL)
```bash
echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward
echo "net.ipv4.ip_forward = 1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```
✅ **Verify**: `cat /proc/sys/net/ipv4/ip_forward` (should be 1)

#### Configure Hostapd
Copy/edit `hostapd.conf` to `/etc/hostapd/hostapd.conf`:
```ini
interface=wlxd03745f84230
ssid=SmartHomeAP
channel=6
hw_mode=g
wpa=2
wpa_passphrase=YourSecurePassword123
wpa_key_mgmt=WPA-PSK
wpa_pairwise=CCMP
```

Set static IP:
```bash
sudo ip addr add 192.168.100.1/24 dev wlxd03745f84230
sudo ip link set wlxd03745f84230 up
```

Start service:
```bash
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl start hostapd
```

#### Configure DHCP/DNS (dnsmasq)
Edit/append to `/etc/dnsmasq.conf`:
```ini
interface=wlxd03745f84230
dhcp-range=192.168.100.50,192.168.100.150,12h
dhcp-option=option:router,192.168.100.1
server=8.8.8.8
```

Start:
```bash
sudo systemctl enable dnsmasq
sudo systemctl start dnsmasq
```

#### Configure Firewall (iptables)
```bash
# Set up forwarding & NAT
sudo iptables -A FORWARD -i wlxd03745f84230 -o enp1s0 -j ACCEPT
sudo iptables -A FORWARD -i enp1s0 -o wlxd03745f84230 -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo iptables -t nat -A POSTROUTING -o enp1s0 -j MASQUERADE

# Save persistently
sudo netfilter-persistent save
```

✅ **Test WAN**: `ping 8.8.8.8` (from router)  
✅ **Test LAN**: Connect WiFi device, get DHCP IP, ping router (192.168.100.1)

---

### 2. ESP8266 Hardware & Code

#### Wiring
| ESP8266 | Relay Module |
|---------|--------------|
| D1 (GPIO5) | Relay 0 IN |
| D2 (GPIO4) | Relay 1 IN |
| 5V | VCC |
| GND | GND |

Connect relay NO/COM to bulb/fan and AC power.

#### Upload Arduino Code
1. Open Arduino IDE → **File → New**
2. Copy provided `esp8266_relay_controller.cpp` code (in project folder)
3. **Tools**:
   - Board: `NodeMCU 1.0 (ESP-12E Module)`
   - Port: `/dev/ttyUSB0`
   - Upload Speed: `115200`
   - Baud Rate: `9600` (sketch sets this)
4. Click **Upload**
5. Open **Serial Monitor** (9600 baud) → Should see: "ESP8266 Relay Controller Ready"
6. Test: Type `01` + Enter → "Relay 0 ON" (relay clicks, LED blinks)

---

### 3. Debian VM Setup (QEMU/KVM)

#### Create VM (via virt-manager GUI)
1. Open `virt-manager`
2. **File → New Virtual Machine**
3. **Local ISO install** → Select Debian 12+ ISO
4. **Memory**: 2GB, **CPUs**: 2
5. **Storage**: 20GB (qcow2 format)
6. **Networking**: NAT
7. **Finish** → Install Debian (follow prompts)

#### Inside VM: Install & Configure
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3-flask python3-sqlalchemy python3-serial git nano

# Add user to serial groups
sudo usermod -aG dialout,tty $USER

# Log out and log back in for permissions
exit
# (Reconnect SSH or open new console)
```

#### USB Passthrough Setup
Back in **virt-manager** (host):
1. Right-click Debian VM → **Show virtual hardware details**
2. Click **Add Hardware** (bottom-left)
3. Select **USB Host Device**
4. Find **Silicon Labs CP2102** or **ESP8266** (VID:PID 10c4:ea60)
5. Click **Finish**
6. Restart VM or unplug/replug ESP8266

**Verify** (inside VM):
```bash
lsusb  # Should see: ID 10c4:ea60 Silicon Labs CP210x
ls -l /dev/ttyUSB0  # Should exist
```

#### Upload Project Files
Copy to VM (via SCP, Git, or file transfer):
```bash
mkdir -p ~/app && cd ~/app

# Copy these files from your project:
# - app.py (Flask main app)
# - arduino_controller.py (serial handler)
# - test_esp.py (hardware test)
# - templates/dashboard.html (web UI)
```

Or clone from Git (if uploaded):
```bash
git clone <your-repo-url> ~/app
cd ~/app
```

#### Test Serial Connection
```bash
python3 test_esp.py
```

**Expected Output**:
```
Opening /dev/ttyUSB0 at 9600 baud...
✅ Port opened successfully!
Waiting for welcome messages...
   ESP8266: ESP8266 Relay Controller Ready
   ...
🧪 Testing commands...
   📤 Sending: '01'
      📥 Response: Relay 0 ON
   ✅ Success: Relay 0 ON confirmed
```

✅ Physical: Relays should click, LEDs blink

---

### 4. Launch Flask Dashboard

```bash
cd ~/app
python3 app.py
```

**Console Output**:
```
... - INFO - 🔌 Initializing Arduino controller...
... - INFO - ✅ Connected to device on /dev/ttyUSB0
... - INFO -    Device: ESP8266 Relay Controller Ready
...
🚀 STARTUP DIAGNOSTICS
Arduino Status: ✅ CONNECTED
Port: /dev/ttyUSB0
 * Running on http://0.0.0.0:5001
```

#### Access Dashboard
1. **Get VM IP** (inside VM):
   ```bash
   ip addr show | grep inet  # Find 192.168.x.x
   ```
2. **Open Browser** (from LAN client):
   ```
   http://192.168.100.x:5001  # Replace x with VM IP
   ```
3. **Toggle Devices**:
   - Click "Turn ON" for Living Room Light
   - Dashboard updates, relay switches, LED blinks
   - Serial log: `📤 Sent: '01' (Device 1 → Relay 0 → ON)`

---

## 🔧 Troubleshooting

### Internet Not Working (IPv4 Forwarding Issue)
**Symptom**: WiFi clients get IP but can't ping external IPs  
**Fix**:
```bash
echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward
echo "net.ipv4.ip_forward = 1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### Serial Port Not Found (Errno 5)
**Symptom**: `[Errno 5] Input/output error: '/dev/ttyUSB0'`  
**Fix**:
```bash
# Check if Arduino IDE is using the port
sudo lsof /dev/ttyUSB0
# Kill any process: sudo kill <PID>

# Add user to dialout group
sudo usermod -aG dialout $USER
# Log out/in

# Replug ESP8266 into different USB port
```

### Relays Don't Click
**Symptom**: Serial commands send OK, but physical relays don't switch  
**Fix**:
- Verify wiring: D1→Relay0 IN, D2→Relay1 IN, VCC/GND correct
- Check relay power: Use dedicated 5V adapter (USB may be insufficient)
- Re-upload Arduino sketch (verify RELAY_ACTIVE_LOW setting)
- Test with multimeter: GPIO D1/D2 output HIGH when relay ON

### WiFi AP Not Broadcasting
**Symptom**: Can't connect to SmartHomeAP SSID  
**Fix**:
```bash
# Check hostapd status
sudo systemctl status hostapd

# Restart
sudo systemctl restart hostapd

# Check logs
sudo journalctl -u hostapd | tail -20
```

### Dashboard Access Denied / Timeout
**Symptom**: Browser can't connect to `http://<VM-IP>:5001`  
**Fix**:
- Verify VM IP: `ip addr show` inside VM
- Check Flask running: `ps aux | grep python3`
- Test from VM itself: `curl http://localhost:5001` (inside VM)
- Verify VM can ping router: `ping 192.168.100.1`
- Check firewall allows port 5001 (shouldn't be blocked in VM)

### Hostapd Config Errors
**Symptom**: `systemctl start hostapd` fails  
**Fix**:
```bash
# Test config syntax
sudo hostapd -t /etc/hostapd/hostapd.conf

# Common issues:
# - Interface name typo (should match: ip link show)
# - Passphrase < 8 chars (WPA2 requires min 8)
# - Missing newline at EOF in config file
```

---

## 📁 Project Structure

```
smart-home-relay-project/
├── README.md                          # This file
├── app.py                             # Flask main application
├── arduino_controller.py              # Serial communication handler
├── test_esp.py                        # Hardware test script
├── esp8266_relay_controller.cpp       # Arduino sketch for ESP8266
├── hostapd.conf                       # WiFi AP configuration
├── templates/
│   └── dashboard.html                 # Web UI template
├── dashboard.db                       # SQLite database (auto-created)
└── app.log                            # Application logs (auto-created)
```

---

## 🎓 Learning Outcomes

- **Networking**: Router config (DHCP, AP, firewall), IPv4 forwarding, iptables, NAT
- **IoT**: ESP8266 programming, relay circuits, serial communication (9600 baud)
- **Web Development**: Flask framework, RESTful API design, SQLite database
- **Linux/VM**: Debian system admin, QEMU/KVM virtualization, USB passthrough
- **Security**: MAC filtering, local-only operation, privacy-first architecture

---

## 🚀 Future Enhancements

### Phase 1: Advanced Firewall
- Selective port opening for specific services
- Rate limiting and DDoS protection
- Application-layer filtering

### Phase 2: Secure VPN
- OpenVPN/WireGuard integration
- Remote access from anywhere (encrypted)
- Mobile app development

### Phase 3: Scaling & Refinement
- Support more relay channels (up to 8)
- Sensor integration (temperature, motion)
- UI improvements (React/Vue.js)
- Energy monitoring
- Long-term stability testing

---

## 📝 Notes

- **Security**: System assumes LAN is trusted. External firewall rules prevent unsolicited inbound; only established/related connections allowed.
- **Offline**: System works without internet. DNS fails offline, but direct IP control still works.
- **Scalability**: Can add more relay modules/devices by updating device-to-relay mapping in `arduino_controller.py`.
- **Data**: All device states stored locally in SQLite; no cloud uploads.

---

## 📞 Contact & Support

**Project Team**: Saikat De, Aditya Saxena, Rishav Kumar  
**Faculty**: Dr. Amrit Pal  
**Institution**: VIT Chennai, Computer Networks Lab  
**Course**: Computer Networks Project, Fall 2025-26  

For issues or questions, refer to troubleshooting section above or contact faculty.

---

## 📜 License

This project is created for educational purposes at VIT Chennai. Feel free to use, modify, and adapt for your own smart home or IoT projects.

---

**Last Updated**: November 03, 2025  
**Version**: 1.0  
**Status**: ✅ Fully Functional