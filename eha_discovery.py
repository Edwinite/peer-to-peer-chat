import socket
import json
import time
import threading  # Import threading module

def peer_discovery(app, listen_port=6000):
    listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    listener.bind(('', listen_port))
    peers = {}
    last_seen = {}

    def mark_peers_away():
        while True:
            current_time = time.time()
            for ip, last_time in list(last_seen.items()):
                if current_time - last_time > 15:
                    peers[ip] = (peers[ip][0], "away")
                    last_seen.pop(ip, None)
            app.update_user_list(peers)
            time.sleep(5)

    threading.Thread(target=mark_peers_away, daemon=True).start()

    while True:
        data, addr = listener.recvfrom(1024)
        peer_info = json.loads(data.decode('utf-8'))
        peers[addr[0]] = (peer_info['username'], peer_info.get('status', 'active'))
        last_seen[addr[0]] = time.time()
        print(f"Detected {peer_info['username']} at {addr[0]}")
        print(f"Current peers: {peers}")
        app.update_user_list(peers)  # Update the UI with the list of peers
