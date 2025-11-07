import socket
import threading
import os
import sys
import time

def handle_client(conn, addr, chunks_folder):
    """Handle incoming requests from another peer"""
    try:
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break
            cmd, chunk_name = data.strip().split()
            if cmd == "GET":
                chunk_path = os.path.join(chunks_folder, chunk_name)
                if os.path.exists(chunk_path):
                    with open(chunk_path, "rb") as f:
                        filedata = f.read()
                    conn.sendall(filedata)
                    print(f"[SENT] {chunk_name} to {addr}")
                else:
                    conn.sendall(b"NOCHUNK")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

def server_thread(port, chunks_folder):
    """Start peer server to listen for chunk requests"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("", port))
    s.listen(5)
    print(f"[LISTENING] Peer server on port {port}")
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn, addr, chunks_folder)).start()

def request_chunk(peer_ip, peer_port, chunk_name, chunks_folder):
    """Request a chunk from another peer"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((peer_ip, peer_port))
        s.sendall(f"GET {chunk_name}".encode())
        data = s.recv(4096)
        if data != b"NOCHUNK":
            with open(os.path.join(chunks_folder, chunk_name), "wb") as f:
                f.write(data)
            print(f"[RECEIVED] {chunk_name} from {peer_ip}:{peer_port}")
        s.close()
    except Exception as e:
        print(f"Failed to get {chunk_name} from {peer_ip}:{peer_port} -> {e}")

def peer_main(my_port, other_peer, chunks_folder):
    peer_ip, peer_port = other_peer.split(":")
    peer_port = int(peer_port)

    # Start server in background
    threading.Thread(target=server_thread, args=(my_port, chunks_folder), daemon=True).start()

    time.sleep(2)  # Give the server a moment to start

    # Get list of chunks
    needed_chunks = ["chunk1", "chunk2"]

    start_time = time.time()
    while True:
        have_chunks = os.listdir(chunks_folder)
        missing = [c for c in needed_chunks if c not in have_chunks]
        if not missing:
            break
        for c in missing:
            request_chunk(peer_ip, peer_port, c, chunks_folder)
        time.sleep(1)

    end_time = time.time()
    print(f"[DONE] P2P finished in {end_time - start_time:.2f} seconds. Final chunks: {os.listdir(chunks_folder)}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python p2p_peer.py <my_port> <other_ip:other_port> <chunks_folder>")
        sys.exit(1)

    my_port = int(sys.argv[1])
    other_peer = sys.argv[2]
    chunks_folder = sys.argv[3]

    peer_main(my_port, other_peer, chunks_folder)
