"""
Inbound side of a chat: listens on port 6001 for TCP connections from peers
and handles each incoming message. Supports plaintext messages as well as
the per-message Diffie-Hellman handshake defined in `eha_initiator.py`.

Every incoming connection is handled on its own thread so that one slow
peer cannot block delivery of messages from other peers.
"""

import json
import socket
import threading

from dh import (
    derive_fernet_key,
    generate_keypair,
    public_key_from_wire,
    public_key_to_wire,
)
from encryption import decrypt_message, InvalidToken


def _send_line(sock_file, payload: dict) -> None:
    sock_file.write((json.dumps(payload) + "\n").encode("utf-8"))
    sock_file.flush()


def _recv_line(sock_file) -> dict:
    line = sock_file.readline()
    if not line:
        return {}
    return json.loads(line.decode("utf-8"))


def chat_responder(app, listen_port=6001):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("", listen_port))
    server_socket.listen()
    print(f"[responder] listening on port {listen_port}")

    while True:
        conn, addr = server_socket.accept()
        threading.Thread(
            target=_handle_connection,
            args=(conn, addr, app),
            daemon=True,
        ).start()


def _handle_connection(conn, addr, app):
    peer_ip = addr[0]
    try:
        conn.settimeout(10)
        with conn:
            sock_file = conn.makefile("rwb")
            first = _recv_line(sock_file)
            if not first:
                return

            msg_type = first.get("type")
            if msg_type == "plaintext":
                sender = first.get("sender", peer_ip)
                text = first.get("message", "")
                print(f"[responder] plaintext from {sender}@{peer_ip}: {text}")
                app.master.after(0, app.display_chat_message, sender, text)
                app.master.after(0, app.store_message, sender, text)

            elif msg_type == "handshake":
                sender = first.get("sender", peer_ip)
                peer_public_pem = public_key_from_wire(first["public_key"])

                private_key, my_public_pem = generate_keypair()
                _send_line(sock_file, {
                    "type": "handshake_ack",
                    "public_key": public_key_to_wire(my_public_pem),
                })

                key = derive_fernet_key(private_key, peer_public_pem)

                ciphertext_msg = _recv_line(sock_file)
                if ciphertext_msg.get("type") != "ciphertext":
                    print(f"[responder] unexpected message after handshake: {ciphertext_msg}")
                    return

                try:
                    plaintext = decrypt_message(key, ciphertext_msg["token"])
                except InvalidToken:
                    print(f"[responder] bad token from {peer_ip} — key mismatch or tampering")
                    return

                print(f"[responder] encrypted from {sender}@{peer_ip}: {plaintext}")
                app.master.after(0, app.display_chat_message, sender, plaintext)
                app.master.after(0, app.store_message, sender, "<Encrypted>")

            else:
                print(f"[responder] unknown message type from {peer_ip}: {first}")
    except (OSError, ValueError, json.JSONDecodeError, KeyError) as err:
        print(f"[responder] error handling connection from {peer_ip}: {err}")
