import json
import socket

from dh import (
    derive_fernet_key,
    generate_keypair,
    public_key_from_wire,
    public_key_to_wire,
)
from encryption import encrypt_message


def _send_line(f, payload):
    f.write((json.dumps(payload) + "\n").encode("utf-8"))
    f.flush()


def _recv_line(f):
    line = f.readline()
    if not line:
        raise ConnectionError("peer closed connection")
    return json.loads(line.decode("utf-8"))


def initiate_chat(app, username, peer_ip, message, port=6001, secure=False):
    try:
        with socket.create_connection((peer_ip, port), timeout=10) as sock:
            f = sock.makefile("rwb")
            if secure:
                # DH: send our public key, get theirs, derive shared key, encrypt.
                private_key, my_public_pem = generate_keypair()
                _send_line(f, {
                    "type": "handshake",
                    "sender": username,
                    "public_key": public_key_to_wire(my_public_pem),
                })
                ack = _recv_line(f)
                if ack.get("type") != "handshake_ack" or "public_key" not in ack:
                    raise ValueError(f"bad handshake reply: {ack}")
                key = derive_fernet_key(private_key, public_key_from_wire(ack["public_key"]))
                _send_line(f, {"type": "ciphertext", "token": encrypt_message(key, message)})
                print(f"sent encrypted message to {peer_ip}")
            else:
                _send_line(f, {"type": "plaintext", "sender": username, "message": message})
                print(f"sent plaintext message to {peer_ip}")
    except (OSError, ValueError, ConnectionError) as err:
        print(f"send to {peer_ip} failed: {err}")
        if hasattr(app, "master"):
            app.master.after(0, app.display_chat_message, "system", f"Could not reach {peer_ip}: {err}")
