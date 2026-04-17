from cryptography.fernet import Fernet, InvalidToken


def encrypt_message(key, plaintext):
    return Fernet(key).encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt_message(key, token):
    return Fernet(key).decrypt(token.encode("ascii")).decode("utf-8")


__all__ = ["encrypt_message", "decrypt_message", "InvalidToken"]
