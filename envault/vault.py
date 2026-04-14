"""Vault module for reading, writing, and managing encrypted .env vault files."""

import json
import os
from pathlib import Path
from typing import Dict, Optional

from envault.crypto import encrypt, decrypt

DEFAULT_VAULT_FILE = ".envault"


class VaultError(Exception):
    """Raised when a vault operation fails."""


def load_vault(password: str, vault_path: Optional[str] = None) -> Dict[str, str]:
    """Load and decrypt a vault file, returning a dict of env vars.

    Args:
        password: The password used to decrypt the vault.
        vault_path: Path to the vault file. Defaults to DEFAULT_VAULT_FILE.

    Returns:
        A dictionary of environment variable key-value pairs.

    Raises:
        VaultError: If the vault file does not exist or cannot be decrypted.
    """
    path = Path(vault_path or DEFAULT_VAULT_FILE)
    if not path.exists():
        raise VaultError(f"Vault file not found: {path}")

    try:
        ciphertext = path.read_text(encoding="utf-8").strip()
        plaintext = decrypt(ciphertext, password)
        return json.loads(plaintext)
    except (ValueError, json.JSONDecodeError) as exc:
        raise VaultError(f"Failed to load vault: {exc}") from exc


def save_vault(
    data: Dict[str, str], password: str, vault_path: Optional[str] = None
) -> None:
    """Encrypt and save a dict of env vars to a vault file.

    Args:
        data: A dictionary of environment variable key-value pairs.
        password: The password used to encrypt the vault.
        vault_path: Path to the vault file. Defaults to DEFAULT_VAULT_FILE.
    """
    path = Path(vault_path or DEFAULT_VAULT_FILE)
    plaintext = json.dumps(data, indent=2)
    ciphertext = encrypt(plaintext, password)
    path.write_text(ciphertext + "\n", encoding="utf-8")


def set_var(
    key: str, value: str, password: str, vault_path: Optional[str] = None
) -> None:
    """Add or update a single environment variable in the vault."""
    path = vault_path or DEFAULT_VAULT_FILE
    try:
        data = load_vault(password, path)
    except VaultError:
        data = {}
    data[key] = value
    save_vault(data, password, path)


def delete_var(key: str, password: str, vault_path: Optional[str] = None) -> None:
    """Remove a single environment variable from the vault.

    Raises:
        VaultError: If the key does not exist in the vault.
    """
    path = vault_path or DEFAULT_VAULT_FILE
    data = load_vault(password, path)
    if key not in data:
        raise VaultError(f"Key '{key}' not found in vault.")
    del data[key]
    save_vault(data, password, path)


def export_to_env(password: str, vault_path: Optional[str] = None) -> Dict[str, str]:
    """Load vault and inject all variables into the current process environment.

    Returns:
        The dict of variables that were exported.
    """
    data = load_vault(password, vault_path)
    os.environ.update(data)
    return data
