# CMP2204 - Peer-to-Peer Chat with Diffie-Hellman

A small peer-to-peer chat application for a local network, built for the
CMP2204 Computer Networks course. Peers discover each other via UDP
broadcast, then exchange messages over TCP. Each encrypted message is
protected by a fresh symmetric key derived from a Diffie-Hellman
exchange performed at the start of the connection.

## Features

- **Automatic peer discovery** over UDP broadcast (port 6000). Users who
  stop broadcasting are marked as *away* after 15 seconds.
- **TCP messaging** (port 6001) with both plaintext and encrypted modes.
- **Per-message Diffie-Hellman key exchange** (RFC 3526, 2048-bit MODP
  Group 14) with HKDF-SHA256 to derive a Fernet key. Every encrypted
  message negotiates its own key, so compromising one session does not
  leak any other.
- **Tkinter UI** with a dark theme and an online / active peer list.

## Architecture

```
+------------------+        UDP 6000        +------------------+
|   Announcer      | ---------------------> |   Discovery      |
|  (every 8s)      |                        |  (listens)       |
+------------------+                        +------------------+
                                                    |
                                                    v
                                            +------------------+
                                            |   ChatApp (UI)   |
                                            +------------------+
                                                    ^
+------------------+        TCP 6001               |
|   Initiator      | ---------------------> +------------------+
|  (per message)   |   DH handshake         |   Responder      |
|                  |   + ciphertext          |   (one thread    |
+------------------+                        |    per peer)     |
                                            +------------------+
```

| File | Role |
|------|------|
| `eha_app.py`        | Entry point — builds the UI, waits for a username, then starts the background services. |
| `eha_ui.py`         | Tkinter UI (`ChatApp`). All widget access happens on the main thread; workers update the UI via `master.after`. |
| `eha_announcer.py`  | UDP broadcaster that announces our username every 8 seconds. |
| `eha_discovery.py`  | UDP listener that tracks peers and marks them *away* after 15 s of silence. |
| `eha_initiator.py`  | Opens the outgoing TCP connection, performs the DH handshake if `Encrypt` is checked, and sends the message. |
| `eha_responder.py`  | Accepts incoming TCP connections on port 6001 and handles each one on its own thread. |
| `dh.py`             | Diffie-Hellman parameters, key generation, and HKDF key derivation. |
| `encryption.py`     | Fernet encrypt/decrypt helpers keyed by a DH-derived key. |

## Wire protocol

Every TCP connection on port 6001 is a single transaction carrying
newline-delimited JSON.

**Plaintext** (one line, initiator → responder):

```json
{"type": "plaintext", "sender": "alice", "message": "hi"}
```

**Encrypted** (three lines):

```
initiator -> responder: {"type": "handshake",     "sender": "alice", "public_key": "<base64 PEM>"}
responder -> initiator: {"type": "handshake_ack", "public_key": "<base64 PEM>"}
initiator -> responder: {"type": "ciphertext",    "token": "<base64 Fernet token>"}
```

Both sides feed their own private key and the peer's public key through
`derive_fernet_key` (HKDF-SHA256 on the DH shared secret) to produce the
same 32-byte symmetric key, which is used as a Fernet key for exactly
one message.

## Setup

### 1. Python

Python 3.9 or newer. On macOS we recommend the `python.org` installer or
Homebrew's `python@3.12` — they ship a working Tcl/Tk build that the
system Python often lacks.

### 2. Virtual environment

```bash
cd "CMP2204 Computer Network's Project"
python3 -m venv venv
source venv/bin/activate       # macOS / Linux
# .\venv\Scripts\activate      # Windows PowerShell
pip install -r requirements.txt
```

### 3. Run

```bash
python eha_app.py
```

Run the same command on a second machine (or a second terminal on the
same machine, although both peers must listen on port 6001 so you'll
need two different hosts for a real test). Set a username in each
window, wait a few seconds for discovery to kick in, select a peer from
**Users Online**, type a message, tick **Encrypt (DH)** if desired, and
hit *Send*.

### macOS notes

If the window does not appear, check the following:

- Make sure you launched with a Python that has Tk. `python3 -c "import
  tkinter; tkinter._test()"` should pop open a small demo window.
- The first time you run it, macOS may show an *"Incoming network
  connections"* firewall prompt. Allow it so peers can reach port 6001.
- The app calls `master.lift()` at startup to pull itself above the
  Terminal. If you run it from an IDE, you may still need to click the
  Dock icon.

### Linux notes

Install Tk if your distro doesn't ship it by default:

```bash
sudo apt install python3-tk           # Debian / Ubuntu
sudo pacman -S tk                     # Arch
```

### Windows notes

Tk ships with the standard Python installer; no extra setup needed.
Windows Defender may prompt you the first time you run it — allow it on
*Private networks*.

## Logs

Every sent and received message is appended to `chat.log` in the project
root. Encrypted messages are logged as the literal string `<Encrypted>`
so the plaintext never touches disk.

## Changes from the 2024 version

- Diffie-Hellman replaces the single shared Fernet key. Each encrypted
  message now negotiates a fresh key.
- macOS UI fixes: explicit window geometry, `lift()` + `-topmost`
  pulse, `selectcolor` matched to the background, and removal of the
  incorrect polling loop that opened a TCP connection to every peer
  every second.
- Proper newline-delimited framing on the TCP protocol so messages
  larger than 1024 bytes (like DH public keys) are not truncated.
- Thread safety: discovery's peer dict is now protected by a lock and
  all UI updates go through `master.after`.
- Dead code removed: the old `responder.py` was a duplicate of
  `eha_responder.py`.
- `requirements.txt` updated to modern versions; `paramiko` (which was
  never used) has been dropped.

## License

MIT - see `LICENSE` (or add one when pushing to GitHub).
