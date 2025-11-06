# Team Information

## Team Name: MatrixMesh

## Team Members:

| S.No | Name | Registration Number | Email |
|------|------|---------------------|-------|
| 1 |Priyan G |24BCE1059            |priyan.2024@vitstudent.ac.in |
| 2 |N Aswin  |24BCE1139            |aswin.n2024@vitstudent.ac.in |
| 3 |Skanda S |24BCE5403            |skanda.s2024@vitstudent.ac.in|


## Project Title
TCP/IP matrix chat application

## Project Description
This project merges client–server communication (via TCP/IP sockets) with mathematical functionality, specifically, matrix operations like addition, subtraction, transpose, inverse, determinant, and more.

## Technology Stack
- Python
- Sockets
- Threading
- NumPy
- Asyncio
- Textual
- Flask
- Flask-SocketIO
- JSON
- VS Code
- Command-line/Terminal
- Google Chrome
- pip

## Setup Instructions
When a user sends a message or performs a matrix operation, the following steps occur:

The client socket connects to the server socket using an IP address and port number.

The server listens (listen()) for incoming connections from multiple clients.

Whenever a new user joins, the server creates a new thread to handle communication with that client independently.

Messages or matrix commands (like add, transpose, inverse, etc.) are sent as text data packets through the TCP connection.

The server interprets these commands, performs the requested matrix operation using a mathematical library (like NumPy), and then broadcasts the results to all connected users in real-time.

We used TCP (Transmission Control Protocol) because it ensures reliable and ordered delivery of data packets — meaning every message or result reaches all clients in the exact sequence it was sent.
While UDP is faster, it’s not reliable for such accuracy-dependent tasks, so TCP is preferred for correctness and consistency.
