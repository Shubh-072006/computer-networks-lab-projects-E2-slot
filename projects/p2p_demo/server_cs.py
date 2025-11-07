import socket, sys, struct
file_path = sys.argv[1]
port = int(sys.argv[2]) if len(sys.argv)>2 else 5000
s = socket.socket()
s.bind(('', port))
s.listen(5)
print("Server listening on port", port, "serving", file_path)
while True:
    conn, addr = s.accept()
    print("Connection from", addr)
    with open(file_path,'rb') as f:
        data = f.read()
    conn.sendall(struct.pack('!Q', len(data)))
    conn.sendall(data)
    conn.close()
