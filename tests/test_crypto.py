"""Tests for envault.crypto encryption/decryption utilities."""

import pytest
from envault.crypto import encrypt, decrypt


PASSWORD = "super-secret-passphrase"
PLAINTEXT = "DATABASE_URL=postgres://user:pass@localhost/mydb"


def test_encrypt_returns_string():
    token = encrypt(PLAINTEXT, PASSWORD)
    assert isinstance(token, str)
    assert len(token) > 0


def test_encrypt_produces_different_ciphertexts():
    """Each encryption call should produce a unique ciphertext due to random salt/nonce."""
    token1 = encrypt(PLAINTEXT, PASSWORD)
    token2 = encrypt(PLAINTEXT, PASSWORD)
    assert token1 != token2


def test_decrypt_roundtrip():
    token = encrypt(PLAINTEXT, PASSWORD)
    result = decrypt(token, PASSWORD)
    assert result == PLAINTEXT


def test_decrypt_wrong_password_raises():
    token = encrypt(PLAINTEXT, PASSWORD)
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt(token, "wrong-password")


def test_decrypt_corrupted_payload_raises():
    token = encrypt(PLAINTEXT, PASSWORD)
    corrupted = token[:-4] + "XXXX"
    with pytest.raises(ValueError):
        decrypt(corrupted, PASSWORD)


def test_decrypt_invalid_base64_raises():
    with pytest.raises(ValueError, match="Invalid payload encoding"):
        decrypt("!!!not-base64!!!", PASSWORD)


def test_decrypt_too_short_payload_raises():
    import base64
    short_payload = base64.b64encode(b"tooshort").decode()
    with pytest.raises(ValueError, match="too short"):
        decrypt(short_payload, PASSWORD)


def test_encrypt_empty_string():
    token = encrypt("", PASSWORD)
    result = decrypt(token, PASSWORD)
    assert result == ""


def test_encrypt_unicode_content():
    unicode_text = "API_KEY=测试密鑰🔑"
    token = encrypt(unicode_text, PASSWORD)
    result = decrypt(token, PASSWORD)
    assert result == unicode_text


def test_encrypt_large_payload():
    """Encryption and decryption should work correctly for large inputs."""
    large_text = "SECRET=" + "x" * 10_000
    token = encrypt(large_text, PASSWORD)
    result = decrypt(token, PASSWORD)
    assert result == large_text
