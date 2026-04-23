"""expire.py — Bulk expiration management for vault variables.

Provides utilities to list soon-to-expire or already-expired variables,
extend TTLs in bulk, and report on expiration status.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from envault.vault import load_vault, save_vault, VaultError
from envault.ttl import get_ttl, set_ttl, purge_expired


class ExpireError(Exception):
    """Raised when an expiration operation fails."""


@dataclass
class ExpirationStatus:
    key: str
    expires_at: Optional[float]  # Unix timestamp or None
    is_expired: bool
    seconds_remaining: Optional[float]  # None if no TTL set

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "expires_at": self.expires_at,
            "is_expired": self.is_expired,
            "seconds_remaining": self.seconds_remaining,
        }


def expiration_report(
    vault_path: Path, password: str, keys: Optional[list[str]] = None
) -> list[ExpirationStatus]:
    """Return expiration status for all (or specified) keys in the vault."""
    try:
        data = load_vault(vault_path, password)
    except VaultError as exc:
        raise ExpireError(str(exc)) from exc

    variables: dict = data.get("variables", {})
    target_keys = keys if keys else sorted(variables.keys())
    now = time.time()
    results: list[ExpirationStatus] = []

    for key in target_keys:
        if key not in variables:
            raise ExpireError(f"Key '{key}' not found in vault.")
        expires_at = get_ttl(data, key)
        if expires_at is None:
            results.append(ExpirationStatus(key, None, False, None))
        else:
            remaining = expires_at - now
            results.append(
                ExpirationStatus(key, expires_at, remaining <= 0, max(remaining, 0) if remaining > 0 else None)
            )

    return results


def extend_ttl_bulk(
    vault_path: Path, password: str, extra_seconds: int, keys: Optional[list[str]] = None
) -> list[str]:
    """Extend the TTL of all (or specified) keys that already have a TTL set.

    Returns a list of keys that were extended.
    """
    if extra_seconds <= 0:
        raise ExpireError("extra_seconds must be a positive integer.")
    try:
        data = load_vault(vault_path, password)
    except VaultError as exc:
        raise ExpireError(str(exc)) from exc

    variables: dict = data.get("variables", {})
    target_keys = keys if keys else sorted(variables.keys())
    now = time.time()
    extended: list[str] = []

    for key in target_keys:
        if key not in variables:
            raise ExpireError(f"Key '{key}' not found in vault.")
        current = get_ttl(data, key)
        if current is not None:
            new_expiry = max(current, now) + extra_seconds
            data = set_ttl(data, key, int(new_expiry - now))
            extended.append(key)

    save_vault(vault_path, password, data)
    return extended


def purge_and_report(vault_path: Path, password: str) -> list[str]:
    """Purge expired keys and return the list of removed key names."""
    try:
        data = load_vault(vault_path, password)
    except VaultError as exc:
        raise ExpireError(str(exc)) from exc

    before = set(data.get("variables", {}).keys())
    data = purge_expired(data)
    after = set(data.get("variables", {}).keys())
    removed = sorted(before - after)
    save_vault(vault_path, password, data)
    return removed
