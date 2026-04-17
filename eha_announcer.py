import socket
import json
import time

def service_announcer(username, broadcast_port=6000, interval=8):
    broadcaster = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcaster.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    message = json.dumps({'username': username, 'status': 'active'}).encode('utf-8')
    while True:
        broadcaster.sendto(message, ('<broadcast>', broadcast_port))
        print(f"Broadcasting presence: {message}")
        time.sleep(interval)
