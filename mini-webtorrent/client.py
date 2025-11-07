import socket
import json
import requests
import hashlib
import threading
import time
import os
import argparse

# ---------------- Uploader ----------------
def run_uploader(port, file_path, piece_size):
    """Listens for connections and uploads requested pieces."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', port))
    server_socket.listen(5)
    print(f"[Uploader] Listening on port {port}...")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"[Uploader] Accepted connection from {addr}")
        try:
            # Protocol: Client sends "GET_PIECE:<index>"
            message = client_socket.recv(1024).decode()
            if message.startswith("GET_PIECE:"):
                piece_index = int(message.split(':')[1])
                print(f"[Uploader] Peer requested piece {piece_index}")
                
                with open(file_path, 'rb') as f:
                    f.seek(piece_index * piece_size)
                    piece_data = f.read(piece_size)
                    client_socket.sendall(piece_data)
        except Exception as e:
            print(f"[Uploader] Error: {e}")
        finally:
            client_socket.close()

# ---------------- Downloader ----------------
def run_downloader(metainfo, my_port, is_seeder):
    file_name = metainfo['file_name']
    file_size = metainfo['file_size']
    piece_size = metainfo['piece_size']
    piece_hashes = metainfo['piece_hashes']
    num_pieces = len(piece_hashes)
    
    # Create an empty file of the correct size if not a seeder
    if not is_seeder:
        if not os.path.exists(file_name):
            with open(file_name, 'wb') as f:
                f.truncate(file_size)
    
    # Track which pieces we have
    my_pieces = [is_seeder] * num_pieces
    
    while True:
        # If we have all pieces, we are done downloading
        if all(my_pieces):
            print("[Downloader] All pieces downloaded! Now only seeding.")
            time.sleep(60)  # Keep seeding (you can reduce this for faster testing)
            continue
            
        print("[Downloader] Announcing to tracker...")
        try:
            params = {'file_name': file_name, 'port': my_port}
            response = requests.get(metainfo['tracker_url'], params=params)
            peers = response.json()['peers']
            print(f"[Downloader] Got peers: {peers}")
        except Exception as e:
            print(f"[Downloader] Error contacting tracker: {e}")
            time.sleep(30)
            continue
            
        # Try to download missing pieces from peers
        for piece_index in range(num_pieces):
            if not my_pieces[piece_index]:
                for peer_addr in peers:
                    try:
                        print(f"[Downloader] Trying to download piece {piece_index} from {peer_addr}")
                        peer_ip, peer_port = peer_addr.split(':')
                        
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.connect((peer_ip, int(peer_port)))
                        s.sendall(f"GET_PIECE:{piece_index}".encode())
                        
                        # Receive the piece data
                        piece_data = b''
                        while len(piece_data) < piece_size:
                            chunk = s.recv(piece_size - len(piece_data))
                            if not chunk:
                                break
                            piece_data += chunk
                        s.close()

                        # Verify and save the piece
                        if hashlib.sha1(piece_data).hexdigest() == piece_hashes[piece_index]:
                            with open(file_name, 'r+b') as f:
                                f.seek(piece_index * piece_size)
                                f.write(piece_data)
                            my_pieces[piece_index] = True
                            print(f"[Downloader] Successfully downloaded and verified piece {piece_index}!")
                            break  # Move to next piece
                        else:
                            print(f"[Downloader] Piece {piece_index} verification failed.")
                    except Exception as e:
                        print(f"[Downloader] Error with peer {peer_addr}: {e}")
                
        time.sleep(20)  # Wait before contacting tracker again

# ---------------- Main ----------------
def main():
    parser = argparse.ArgumentParser(description="A simple BitTorrent client.")
    parser.add_argument('metainfo_file', type=str, help='Path to the .json metainfo file')
    parser.add_argument('--port', type=int, required=True, help='Port for this client to listen on')
    parser.add_argument('--seeder', action='store_true', help='Flag to indicate this client is the initial seeder')
    args = parser.parse_args()

    with open(args.metainfo_file, 'r') as f:
        metainfo = json.load(f)

    # ✅ Correct: use the file_name key from JSON
    file_path_to_share = metainfo['file_name']

    # Start uploader thread
    uploader_thread = threading.Thread(
        target=run_uploader,
        args=(args.port, file_path_to_share, metainfo['piece_size'])
    )
    uploader_thread.daemon = True
    uploader_thread.start()

    # Run downloader
    run_downloader(metainfo, args.port, args.seeder)


if __name__ == '__main__':
    main()
