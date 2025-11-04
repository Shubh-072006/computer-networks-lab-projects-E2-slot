# whiteboard_server.py
import socket
import threading
import json

TCP_PORT = 5000
UDP_PORT = 6000
HOST = "0.0.0.0"

tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
tcp_server.bind((HOST, TCP_PORT))
tcp_server.listen()

udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
udp_server.bind((HOST, UDP_PORT))

tcp_clients = []        # list of TCP socket objects
udp_clients = set()     # set of (ip, port) tuples

print("Server starting...")
print(f"TCP (chat/control) on port {TCP_PORT}")
print(f"UDP (whiteboard) on port {UDP_PORT}")
print("Waiting for clients...")

# broadcast a TCP text message to all TCP clients (except optional sender)
def broadcast_tcp(message, sender_sock=None):
    dead = []
    for c in tcp_clients:
        if c is sender_sock:
            continue
        try:
            c.sendall(message.encode('utf-8'))
        except:
            dead.append(c)
    for d in dead:
        try: tcp_clients.remove(d)
        except: pass

# broadcast UDP bytes to all known UDP clients except optional sender
def broadcast_udp(data_bytes, sender_addr=None):
    dead = []
    for addr in list(udp_clients):
        if sender_addr and addr == sender_addr:
            continue
        try:
            udp_server.sendto(data_bytes, addr)
        except:
            dead.append(addr)
    for d in dead:
        try: udp_clients.remove(d)
        except: pass

def handle_tcp_client(conn, addr):
    try:
        # first message is username JSON: {"type":"hello","username":"Alice"}
        raw = conn.recv(4096)
        if not raw:
            conn.close()
            return
        try:
            obj = json.loads(raw.decode('utf-8'))
            username = obj.get("username", f"user_{addr[1]}")
        except:
            username = f"user_{addr[1]}"
        tcp_clients.append(conn)
        print(f"[TCP] {username} connected from {addr}")

        # notify others
        broadcast_tcp(json.dumps({"type":"system","msg":f"{username} joined."}))

        # keep receiving TCP messages (chat or control)
        while True:
            data = conn.recv(4096)
            if not data:
                break
            try:
                obj = json.loads(data.decode('utf-8'))
                t = obj.get("type")
                if t == "chat":
                    text = obj.get("msg","")
                    broadcast_tcp(json.dumps({"type":"chat","user":username,"msg":text}))
                elif t == "clear":
                    # tell everyone to clear via both TCP and UDP
                    broadcast_tcp(json.dumps({"type":"control","action":"clear"}))
                    broadcast_udp(b'{"type":"control","action":"clear"}')
            except Exception:
                # ignore malformed TCP payloads
                pass

    except Exception as e:
        print("TCP client error:", e)
    finally:
        try:
            conn.close()
        except:
            pass
        if conn in tcp_clients:
            tcp_clients.remove(conn)
        print(f"[TCP] {username} disconnected")
        broadcast_tcp(json.dumps({"type":"system","msg":f"{username} left."}))


# UDP loop: register UDP clients and broadcast drawing JSON messages
def udp_loop():
    while True:
        try:
            data, addr = udp_server.recvfrom(65535)
            # register sender so we can later forward to others
            udp_clients.add(addr)
            # broadcast drawing/control to other udp clients
            broadcast_udp(data, sender_addr=addr)
        except Exception as e:
            print("UDP error:", e)
            # continue


# start UDP thread
t_udp = threading.Thread(target=udp_loop, daemon=True)
t_udp.start()

# accept TCP clients
try:
    while True:
        conn, addr = tcp_server.accept()
        threading.Thread(target=handle_tcp_client, args=(conn, addr), daemon=True).start()
except KeyboardInterrupt:
    print("Server shutting down.")
finally:
    tcp_server.close()
    udp_server.close()
