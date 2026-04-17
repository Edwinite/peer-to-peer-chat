import socket
import json
from encryption import decrypt_message
from logging_config import log_message

def chat_responder(app, listen_port=6001):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', listen_port))
    server_socket.listen()
    while True:
        conn, addr = server_socket.accept()
        with conn:
            data = conn.recv(1024)
            message = json.loads(data.decode('utf-8'))
            handle_incoming_message(addr, message, app)

def handle_incoming_message(addr, message, app):
    if 'encrypted message' in message:
        decrypted_message = decrypt_message(message['encrypted message'])
        print(f"Received encrypted message from {addr}: {decrypted_message}")
        log_message(addr[0], decrypted_message)
        app.display_chat_message(addr[0], decrypted_message)  # Update UI
    elif 'unencrypted message' in message:
        print(f"Received message from {addr}: {message['unencrypted message']}")
        log_message(addr[0], message['unencrypted message'])
        app.display_chat_message(addr[0], message['unencrypted message'])  # Update UI
