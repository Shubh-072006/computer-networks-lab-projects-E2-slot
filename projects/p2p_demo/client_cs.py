import socket, sys, struct, time
server_ip = sys.argv[1]
port = int(sys.argv[2])
out_file = sys.argv[3] if len(sys.argv)>3 else "downloaded.txt"
s = socket.socket()
s.connect((server_ip, port))
size = struct.unpack('!Q', s.recv(8))[0]
start = time.time()
recv = b''
while len(recv) < size:
    data = s.recv(4096)
    if not data:
        break
    recv += data
with open(out_file,'wb') as f:
    f.write(recv)
s.close()
print("Downloaded in:", time.time()-start, "seconds")
