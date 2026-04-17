import json
import socket
import time


def service_announcer(username, broadcast_port=6000, interval=8):
    broadcaster = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcaster.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    payload = json.dumps({"username": username, "status": "active"}).encode("utf-8")

    while True:
        try:
            broadcaster.sendto(payload, ("<broadcast>", broadcast_port))
        except OSError as err:
            print(f"broadcast failed: {err}")
        time.sleep(interval)
