import socket
import json
from encryption import encrypt_message
from logging_config import log_message

def initiate_chat(app, username, peer_ip, message, port=6001, secure=False):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((peer_ip, port))
        if secure:
            encrypted_message = encrypt_message(message)
            message_data = {'sender': username, 'encrypted message': encrypted_message.decode('utf-8')}
        else:
            message_data = {'sender': username, 'unencrypted message': message}
        json_message = json.dumps(message_data).encode('utf-8')  # Encode the JSON string to bytes
        print(f"Sending JSON message to {peer_ip}: {json_message}")  # Log sent message
        s.sendall(json_message)
        display_message = "<Encrypted>" if secure else message
        app.display_chat_message(username, display_message)  # Update UI with actual message content
        app.store_message(username, display_message)  # Store <Encrypted> in log if secure
