"""Encryption and decryption utilities for envault using AES-GCM."""

import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend

SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32  # 256-bit


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit key from a password using scrypt."""
    kdf = Scrypt(
        salt=salt,
        length=KEY_SIZE,
        n=2**14,
        r=8,
        p=1,
        backend=default_backend(),
    )
    return kdf.derive(password.encode())


def encrypt(plaintext: str, password: str) -> str:
    """Encrypt plaintext string with a password.

    Returns a base64-encoded string containing salt + nonce + ciphertext.
    """
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key(password, salt)

    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)

    payload = salt + nonce + ciphertext
    return base64.b64encode(payload).decode()


def decrypt(encoded_payload: str, password: str) -> str:
    """Decrypt a base64-encoded payload with a password.

    Raises ValueError if decryption fails (wrong password or corrupted data).
    """
    try:
        payload = base64.b64decode(encoded_payload.encode())
    except Exception as exc:
        raise ValueError("Invalid payload encoding.") from exc

    if len(payload) < SALT_SIZE + NONCE_SIZE + 1:
        raise ValueError("Payload is too short to be valid.")

    salt = payload[:SALT_SIZE]
    nonce = payload[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
    ciphertext = payload[SALT_SIZE + NONCE_SIZE:]

    key = derive_key(password, salt)
    aesgcm = AESGCM(key)

    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    except Exception as exc:
        raise ValueError("Decryption failed. Wrong password or corrupted data.") from exc

    return plaintext.decode()
