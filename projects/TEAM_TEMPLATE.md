# Team Information

## Team Name: CN_E2_TEAM

## Team Members:

| S.No | Name         | Registration Number | Email                             |
|------|--------------|---------------------|-----------------------------------|
| 1    |Sukrati Verma |24BCE5573            | sukrati.verma2024@vitstudent.ac.in|
| 2    |Chenna Asrith |24BCE5269            | asrith.chenna2024@vitstudent.ac.in|

## Project Title
Real-time Multiuser Collaborative Whiteboard with in-built Chat using TCP & UDP

## Project Description
This project is a real-time collaborative whiteboard application that allows multiple users to draw, chat, and share ideas live over a local network. It uses a client-server architecture where one computer runs the server (handling connections and data synchronization), and other clients connect to it using a simple Windows executable (.exe) file — no need for Python installation on the client side.

## Technology Stack
-Programming Language: Python
-GUI Library: Tkinter
-Networking: Socket Programming (TCP & UDP)
-Packaging: PyInstaller (.exe generation)

## Setup Instructions

Server Setup

Keep all files in one folder.
Open CMD in that folder → run:
python whiteboard_server.py
Note your IPv4 address using ipconfig.
Ensure Wi-Fi is Private and allow ports 5000 (TCP) & 6000 (UDP) through Firewall (run CMD as admin).

Client Setup

Copy whiteboard_client.exe to each client PC.
Double-click it → enter Server IP (from step 3) & username.
The shared whiteboard will open — draw, chat, erase, and clear together in real time.
