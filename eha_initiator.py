"""
Outbound side of a chat: connects to the peer's listener on port 6001 and
either sends a plaintext message directly or performs a per-message Diffie-
Hellman handshake before sending an encrypted message.

Wire protocol (newline-delimited JSON; one transaction per TCP connection):

  Plaintext:
    --> {"type": "plaintext", "sender": "alice", "message": "hi"}

  Encrypted:
    --> {"type": "handshake", "sender": "alice", "public_key": "<b64 PEM>"}
    <-- {"type": "handshake_ack", "public_key": "<b64 PEM>"}
    --> {"type": "ciphertext", "token": "<b64 fernet token>"}
"""

import json
import socket

from dh import (
    derive_fernet_key,
    generate_keypair,
    public_key_from_wire,
    public_key_to_wire,
)
from encryption import encrypt_message


def _send_line(sock_file, payload: dict) -> None:
    sock_file.write((json.dumps(payload) + "\n").encode("utf-8"))
    sock_file.flush()


def _recv_line(sock_file) -> dict:
    line = sock_file.readline()
    if not line:
        raise ConnectionError("peer closed connection before sending a reply")
    return json.loads(line.decode("utf-8"))


def initiate_chat(app, username, peer_ip, message, port=6001, secure=False):
    """
    Send one message to a peer. Creates a new TCP connection, performs the DH
    handshake if `secure` is True, and closes the connection when done.

    The UI update (showing the sent message in the chat display) is done by
    the caller; this function only handles the network side.
    """
    try:
        with socket.create_connection((peer_ip, port), timeout=10) as sock:
            sock_file = sock.makefile("rwb")
            if secure:
                private_key, my_public_pem = generate_keypair()
                _send_line(sock_file, {
                    "type": "handshake",
                    "sender": username,
                    "public_key": public_key_to_wire(my_public_pem),
                })

                ack = _recv_line(sock_file)
                if ack.get("type") != "handshake_ack" or "public_key" not in ack:
                    raise ValueError(f"bad handshake reply from {peer_ip}: {ack}")

                peer_public_pem = public_key_from_wire(ack["public_key"])
                key = derive_fernet_key(private_key, peer_public_pem)

                token = encrypt_message(key, message)
                _send_line(sock_file, {"type": "ciphertext", "token": token})
                print(f"[initiator] sent encrypted message to {peer_ip}")
            else:
                _send_line(sock_file, {
                    "type": "plaintext",
                    "sender": username,
                    "message": message,
                })
                print(f"[initiator] sent plaintext message to {peer_ip}")
    except (OSError, ValueError, ConnectionError) as err:
        print(f"[initiator] failed to send to {peer_ip}: {err}")
        # Surface the error in the UI so the user knows the message didn't go out.
        if hasattr(app, "master"):
            app.master.after(
                0,
                app.display_chat_message,
                "system",
                f"Could not reach {peer_ip}: {err}",
            )
