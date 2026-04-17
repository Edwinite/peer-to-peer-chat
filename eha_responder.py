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


def _send_line(f, payload):
    f.write((json.dumps(payload) + "\n").encode("utf-8"))
    f.flush()


def _recv_line(f):
    line = f.readline()
    if not line:
        return {}
    return json.loads(line.decode("utf-8"))


def chat_responder(app, listen_port=6001):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("", listen_port))
    server.listen()
    print(f"listening on port {listen_port}")

    while True:
        conn, addr = server.accept()
        # one thread per connection so a slow peer can't block the others
        threading.Thread(target=_handle, args=(conn, addr, app), daemon=True).start()


def _handle(conn, addr, app):
    peer_ip = addr[0]
    try:
        conn.settimeout(10)
        with conn:
            f = conn.makefile("rwb")
            first = _recv_line(f)
            if not first:
                return

            t = first.get("type")
            if t == "plaintext":
                sender = first.get("sender", peer_ip)
                text = first.get("message", "")
                app.master.after(0, app.display_chat_message, sender, text)
                app.master.after(0, app.store_message, sender, text)

            elif t == "handshake":
                sender = first.get("sender", peer_ip)
                peer_public = public_key_from_wire(first["public_key"])
                private_key, my_public_pem = generate_keypair()
                _send_line(f, {
                    "type": "handshake_ack",
                    "public_key": public_key_to_wire(my_public_pem),
                })
                key = derive_fernet_key(private_key, peer_public)

                ct = _recv_line(f)
                if ct.get("type") != "ciphertext":
                    return
                try:
                    plaintext = decrypt_message(key, ct["token"])
                except InvalidToken:
                    print(f"invalid token from {peer_ip}")
                    return

                app.master.after(0, app.display_chat_message, sender, plaintext)
                app.master.after(0, app.store_message, sender, "<Encrypted>")

            else:
                print(f"unknown message type from {peer_ip}: {first}")

    except (OSError, ValueError, json.JSONDecodeError, KeyError) as err:
        print(f"responder error from {peer_ip}: {err}")
