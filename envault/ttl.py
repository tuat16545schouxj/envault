"""TTL (time-to-live) support for vault variables."""
from __future__ import annotations

import time
from typing import Optional

from envault.vault import VaultError, load_vault, save_vault


class TTLError(Exception):
    pass


def set_ttl(vault_path: str, password: str, key: str, ttl_seconds: int) -> None:
    """Attach a TTL (expiry timestamp) to an existing variable."""
    data = load_vault(vault_path, password)
    if key not in data.get("vars", {}):
        raise TTLError(f"Key '{key}' not found in vault.")
    if ttl_seconds <= 0:
        raise TTLError("TTL must be a positive integer (seconds).")
    ttl_map = data.setdefault("ttl", {})
    ttl_map[key] = time.time() + ttl_seconds
    save_vault(vault_path, password, data)


def remove_ttl(vault_path: str, password: str, key: str) -> None:
    """Remove the TTL from a variable."""
    data = load_vault(vault_path, password)
    ttl_map = data.get("ttl", {})
    if key not in ttl_map:
        raise TTLError(f"No TTL set for key '{key}'.")
    del ttl_map[key]
    save_vault(vault_path, password, data)


def get_ttl(vault_path: str, password: str, key: str) -> Optional[float]:
    """Return the expiry timestamp for key, or None if no TTL is set."""
    data = load_vault(vault_path, password)
    return data.get("ttl", {}).get(key)


def purge_expired(vault_path: str, password: str) -> list[str]:
    """Delete all variables whose TTL has passed. Returns list of purged keys."""
    data = load_vault(vault_path, password)
    now = time.time()
    ttl_map = data.get("ttl", {})
    expired = [k for k, exp in ttl_map.items() if exp <= now]
    for key in expired:
        data["vars"].pop(key, None)
        del ttl_map[key]
    if expired:
        save_vault(vault_path, password, data)
    return expired


def list_ttls(vault_path: str, password: str) -> dict[str, float]:
    """Return a mapping of key -> expiry timestamp for all keys with a TTL."""
    data = load_vault(vault_path, password)
    return dict(data.get("ttl", {}))
