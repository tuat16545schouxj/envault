"""Access control for vault keys — define read/write permissions per key or pattern."""

from __future__ import annotations

import fnmatch
from typing import Optional

from envault.vault import VaultError, load_vault, save_vault

ACCESS_KEY = "__access_rules__"


class AccessError(Exception):
    """Raised when an access control operation fails."""


def _rules(vault: dict) -> dict:
    return vault.get(ACCESS_KEY, {})


def set_rule(vault_path: str, password: str, pattern: str, mode: str) -> None:
    """Set an access rule for keys matching *pattern*.

    Args:
        vault_path: Path to the vault file.
        password: Vault password.
        pattern: Glob-style key pattern (e.g. "DB_*", "SECRET").
        mode: One of "ro" (read-only), "rw" (read-write), or "none" (no access).
    """
    if mode not in ("ro", "rw", "none"):
        raise AccessError(f"Invalid mode '{mode}'. Must be 'ro', 'rw', or 'none'.")
    vault = load_vault(vault_path, password)
    rules = _rules(vault)
    rules[pattern] = mode
    vault[ACCESS_KEY] = rules
    save_vault(vault_path, password, vault)


def remove_rule(vault_path: str, password: str, pattern: str) -> None:
    """Remove the access rule for *pattern*."""
    vault = load_vault(vault_path, password)
    rules = _rules(vault)
    if pattern not in rules:
        raise AccessError(f"No access rule found for pattern '{pattern}'.")
    del rules[pattern]
    vault[ACCESS_KEY] = rules
    save_vault(vault_path, password, vault)


def list_rules(vault_path: str, password: str) -> list[dict]:
    """Return all access rules as a sorted list of dicts."""
    vault = load_vault(vault_path, password)
    rules = _rules(vault)
    return [{"pattern": p, "mode": m} for p, m in sorted(rules.items())]


def check_access(vault_path: str, password: str, key: str, required: str) -> bool:
    """Check whether *key* satisfies *required* access level.

    Rules are evaluated in insertion order; the first matching pattern wins.
    If no rule matches, access defaults to 'rw'.

    Args:
        required: "ro" or "rw".

    Returns:
        True if access is permitted, False otherwise.
    """
    if required not in ("ro", "rw"):
        raise AccessError(f"Invalid required mode '{required}'.")
    vault = load_vault(vault_path, password)
    rules = _rules(vault)
    for pattern, mode in rules.items():
        if fnmatch.fnmatch(key, pattern):
            if mode == "none":
                return False
            if mode == "ro":
                return required == "ro"
            return True  # rw satisfies both
    return True  # default: full access
