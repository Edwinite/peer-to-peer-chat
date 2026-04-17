"""
UDP peer discovery.

Listens on the broadcast port for announcements from other peers and keeps a
dictionary mapping peer-ip -> (username, status). Peers that haven't been heard
from for a while are marked "away"; new announcements flip them back to "active".

All UI updates go through `app.master.after(0, ...)` because this module runs
on a background thread and Tk widgets are only safe to touch from the main
thread.
"""

import json
import socket
import threading
import time

AWAY_AFTER_SECONDS = 15
SWEEP_INTERVAL_SECONDS = 5


def peer_discovery(app, listen_port=6000):
    listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("", listen_port))

    peers = {}       # ip -> (username, status)
    last_seen = {}   # ip -> timestamp
    lock = threading.Lock()

    def sweep_for_away_peers():
        while True:
            time.sleep(SWEEP_INTERVAL_SECONDS)
            now = time.time()
            with lock:
                for ip, seen in list(last_seen.items()):
                    if now - seen > AWAY_AFTER_SECONDS and ip in peers:
                        username, _ = peers[ip]
                        peers[ip] = (username, "away")
                snapshot = dict(peers)
            app.master.after(0, app.update_user_list, snapshot)

    threading.Thread(target=sweep_for_away_peers, daemon=True).start()

    while True:
        try:
            data, addr = listener.recvfrom(1024)
            info = json.loads(data.decode("utf-8"))
        except (OSError, ValueError, json.JSONDecodeError) as err:
            print(f"[discovery] ignoring malformed packet: {err}")
            continue

        username = info.get("username")
        if not username:
            continue

        ip = addr[0]
        with lock:
            peers[ip] = (username, info.get("status", "active"))
            last_seen[ip] = time.time()
            snapshot = dict(peers)

        app.master.after(0, app.update_user_list, snapshot)
