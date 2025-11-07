# metainfo_generator.py
import hashlib
import json
import os

# --- Configuration ---
FILE_TO_SHARE = 'my_project_file.txt' # The file you want to share
TRACKER_URL = 'http://127.0.0.1:5000/tracker' # Your tracker's address
PIECE_SIZE_KB = 256 # Size of each piece in Kilobytes

def create_metainfo():
    """Generates a metainfo .json file for the file to be shared."""
    piece_size = PIECE_SIZE_KB * 1024
    piece_hashes = []
    
    if not os.path.exists(FILE_TO_SHARE):
        print(f"Error: File '{FILE_TO_SHARE}' not found.")
        return

    file_size = os.path.getsize(FILE_TO_SHARE)
    print(f"Sharing file: {FILE_TO_SHARE} ({file_size} bytes)")
    print(f"Piece size: {piece_size / 1024} KB")

    with open(FILE_TO_SHARE, 'rb') as f:
        while True:
            piece = f.read(piece_size)
            if not piece:
                break
            piece_hashes.append(hashlib.sha1(piece).hexdigest())

    metainfo = {
        'tracker_url': TRACKER_URL,
        'file_name': os.path.basename(FILE_TO_SHARE),
        'file_size': file_size,
        'piece_size': piece_size,
        'piece_hashes': piece_hashes
    }
    
    metainfo_filename = f"{FILE_TO_SHARE}.json"
    with open(metainfo_filename, 'w') as f:
        json.dump(metainfo, f, indent=4)
        
    print(f"\nMetainfo file created: {metainfo_filename}")
    print(f"Total pieces: {len(piece_hashes)}")

if __name__ == '__main__':
    create_metainfo()