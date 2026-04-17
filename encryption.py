"""
Symmetric message encryption using Fernet, keyed by a Diffie-Hellman-derived
secret.

The previous version of this module generated a single Fernet key at import
time and shared it globally — meaning every peer needed the same key out-of-band,
which defeats the purpose of encryption over the network. This version takes
the key as an explicit argument so each conversation can use a fresh key
negotiated via Diffie-Hellman (see `dh.py`).
"""

from cryptography.fernet import Fernet, InvalidToken


def encrypt_message(key: bytes, plaintext: str) -> str:
    """
    Encrypt `plaintext` with the given Fernet key and return the token as a
    string (safe to stick inside JSON).
    """
    token = Fernet(key).encrypt(plaintext.encode("utf-8"))
    return token.decode("ascii")


def decrypt_message(key: bytes, token: str) -> str:
    """
    Decrypt the token produced by `encrypt_message`. Raises `InvalidToken`
    if the key is wrong or the token has been tampered with.
    """
    plaintext = Fernet(key).decrypt(token.encode("ascii"))
    return plaintext.decode("utf-8")


__all__ = ["encrypt_message", "decrypt_message", "InvalidToken"]
