# tracker.py
from flask import Flask, request, jsonify

app = Flask(__name__)

# This dictionary will store peer lists.
# Key: file_name (acting as info_hash)
# Value: a set of "ip:port" strings for peers
torrents = {}

@app.route('/tracker', methods=['GET'])
def tracker_announce():
    # 1. Get arguments from the peer's request
    file_name = request.args.get('file_name')
    peer_port = request.args.get('port')
    peer_ip = request.remote_addr
    peer_addr = f"{peer_ip}:{peer_port}"

    if not file_name or not peer_port:
        return jsonify({'error': 'Missing required parameters'}), 400

    # 2. Get the current list of peers BEFORE adding the new one
    # This is so the new peer gets everyone else, but not itself
    if file_name in torrents:
        peer_list = list(torrents[file_name])
    else:
        peer_list = []
        torrents[file_name] = set()

    # 3. Add the new peer to the set (sets automatically handle duplicates)
    torrents[file_name].add(peer_addr)

    print(f"Announce from {peer_addr} for file '{file_name}'")
    print(f"Current peers for '{file_name}': {torrents[file_name]}")

    # 4. Return the list of other peers
    return jsonify({'peers': peer_list})

if __name__ == '__main__':
    # Run the tracker on localhost, port 5000
    app.run(host='0.0.0.0', port=5000)