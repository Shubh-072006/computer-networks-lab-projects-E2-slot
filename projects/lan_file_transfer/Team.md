# Team Information

## Team Name: Lan file sharing

## Team Members:

| S.No | Name                 | Registration Number | Email |
|------|----------------------|---------------------|-------|
| 1    | Paarth Khushalani    | 24BCE5473           | -     |
| 2    | Harshika Triphati    | 24BCE1627           | -     |
| 3    | -                    | -                   | -     |
| 4    | -                    | -                   | -     |

## Project Title
LAN File Transfer System 

## Project Description
Cross‑platform LAN file sharing application supporting multi‑file, multi‑target transfers with
password authentication, integrity verification, automatic discovery, and real‑time progress. It
offers a modern web interface (Flask), command‑line utilities, and desktop GUIs for flexibility.

## Technology Stack
- Programming Language: Python 3.12
- Frameworks/Libraries: Flask 2.3, Werkzeug, Tkinter
- Networking: TCP (file transfer), UDP (discovery)
- Tools: Markdown, Logging utilities

## Setup Instructions
1. Open a terminal in `lan_file_transfer`.
2. (Optional) Create and activate a virtual environment:
   - Windows:
     ```bash
     python -m venv venv
     venv\Scripts\activate
     ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the web interface (recommended):
   ```bash
   python enhanced_web_server.py
   ```
   Access: `http://localhost:8080` or `http://YOUR_IP:8080`.
5. CLI alternatives:
   - Start server:
     ```bash
     python main.py server-cli
     ```
   - Send a file:
     ```bash
     python main.py client-cli --server <SERVER_IP> --file <PATH_TO_FILE>
     ```


