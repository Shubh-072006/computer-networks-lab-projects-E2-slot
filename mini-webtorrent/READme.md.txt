# 🚀 Mini BitTorrent Project

This project is a **simplified BitTorrent-like system** built using **Python** and **Flask**.  
It allows users to **upload, share, and download files peer-to-peer (P2P)** across devices on the same network, simulating the real BitTorrent protocol in a minimal setup.

---

## 📂 Project Structure

.
├── web_torrent.py # Flask-based tracker + web interface
├── client.py # P2P client for uploading/downloading pieces
├── tracker.py # Standalone tracker version (for testing)
├── metainfo_generator.py # Script to generate .json metainfo manually
├── templates/
│ └── index.html # Web UI for uploading files
├── uploads/ # Uploaded files stored here
├── metainfos/ # Metainfo (.json) files stored here
└── README.md # Project documentation
## ⚙️ Features

- 🌐 Flask web interface for file uploads and downloads  
- 🧭 Tracker to maintain peer lists for each file  
- 🔄 Peer-to-peer (P2P) file transfers using Python sockets  
- 🧩 File split into small pieces (default: 256 KB)  
- 🧾 Metainfo file generation with piece hashes (like `.torrent` files)  
- ⚡ Seeder + Downloader functionality  
- 🖥️ Local web UI (supports expansion for drag & drop)

---

## 🚀 How It Works

1. **Tracker (`web_torrent.py`)**
   - Runs a Flask server to handle peer announcements (`/tracker`)  
   - Also serves as a simple web front-end for uploads and file sharing  

2. **Seeder (Device 1)**
   - Uploads a file through the web UI  
   - Flask generates a `.json` metainfo file (includes piece hashes, tracker URL, etc.)  
   - Seeder can serve file pieces to other peers via sockets  

3. **Downloader (Device 2 or others)**
   - Loads the `.json` metainfo file  
   - Contacts the tracker to get a list of peers  
   - Connects to seeders and downloads file pieces  
   - Verifies each piece’s SHA1 hash before saving  

---

## 🧑‍💻 How to Run

### 1️⃣ Start the Tracker (Device 1)
Run the Flask tracker + web UI:
```bash
python web_torrent.py
By default, it runs on port 5000:

cpp
Copy code
http://127.0.0.1:5000
If testing across devices, use your local network IP:

cpp
Copy code
http://192.168.x.x:5000
2️⃣ Upload a File (Seeder)
Open the tracker web page.

Upload a file (optionally specify a seeder port, e.g. 6881).

The server will:

Save the file in /uploads

Create a .json metainfo file in /metainfos

You’ll see links like:

Download URL: direct file download

Metainfo URL: for sharing with other peers

3️⃣ Share the Metainfo File
Download the .json file from the metainfo URL

Send this file to other devices (email, USB, etc.)

4️⃣ Run a Downloader (Device 2)
On another device, run:

bash
Copy code
python client.py <metainfo_file>.json --port 6882
This device will:

Contact the tracker

Discover available peers (seeders)

Download file pieces

Verify and assemble the complete file

🌍 Testing Across Two Devices
Device	Role	Command
Device 1	Tracker + Seeder	python web_torrent.py (upload via browser)
Device 2	Downloader	python client.py <metainfo.json> --port 6882

✅ Make sure both devices are on the same Wi-Fi / local network
✅ Use Device 1’s IP in the tracker_url (not 127.0.0.1)
✅ Allow the seeder ports (e.g., 6881, 6882) through firewall

🧱 Technical Details
Backend: Flask (Python)

Networking: TCP sockets

Piece hashing: SHA1

Piece size: 256 KB (default)

Data storage:

Uploaded files → /uploads

Metainfo files → /metainfos

🪄 Future Improvements
Add drag & drop upload support

Show seeder/downloader progress on the web UI

Display active peers and transfer rates

Add pause/resume functionality

Improve UI with CSS/JS animations (space-themed design 🌌)

🧠 Credits
Developed as a learning project to understand BitTorrent fundamentals, Flask web apps, and Python socket programming.

CREATED WITH LOVE 
SARANG G NAVATH
