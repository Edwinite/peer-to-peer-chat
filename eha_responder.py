import socket
import json
from encryption import decrypt_message

def chat_responder(app, listen_port=6001):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', listen_port))
    server_socket.listen()
    while True:
        conn, addr = server_socket.accept()
        with conn:
            data = conn.recv(1024)
            print(f"Received data from {addr}: {data}")  # Log received data
            try:
                message = json.loads(data.decode('utf-8'))
                handle_incoming_message(addr, message, app)
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                print(f"Received invalid JSON data: {data}")

def handle_incoming_message(addr, message, app):
    sender = message.get('sender', addr[0])  # Default to IP address if sender is not provided
    if 'encrypted message' in message:
        decrypted_message = decrypt_message(message['encrypted message'])
        print(f"Received encrypted message from {sender}: {decrypted_message}")
        app.master.after(0, app.display_chat_message, sender, decrypted_message)  # Update UI
        app.master.after(0, app.store_message, sender, "<Encrypted>")  # Store <Encrypted> in log
    elif 'unencrypted message' in message:
        unencrypted_message = message['unencrypted message']
        print(f"Received message from {sender}: {unencrypted_message}")
        app.master.after(0, app.display_chat_message, sender, unencrypted_message)  # Update UI
        app.master.after(0, app.store_message, sender, unencrypted_message)  # Store message in log
