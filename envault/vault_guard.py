"""Vault guard: wraps set_var to enforce pin and lock constraints."""

from __future__ import annotations

from envault.lock import LockError, is_locked
from envault.pin import PinError, is_pinned
from envault.vault import VaultError, load_vault, save_vault


class GuardError(Exception):
    """Raised when a guarded write is rejected."""


def guarded_set(vault_path: str, password: str, key: str, value: str, force: bool = False) -> None:
    """Set *key* = *value* in the vault, respecting lock and pin guards.

    Parameters
    ----------
    vault_path:
        Path to the encrypted vault file.
    password:
        Vault decryption password.
    key:
        Variable name to set.
    value:
        Value to assign.
    force:
        If True, bypass pin guard (lock guard is never bypassable).
    """
    if is_locked(vault_path):
        raise GuardError(f"Vault '{vault_path}' is locked. Unlock it before making changes.")

    try:
        data = load_vault(vault_path, password)
    except VaultError:
        data = {"variables": {}}

    if not force and is_pinned(data, key):
        raise GuardError(
            f"Key '{key}' is pinned and cannot be overwritten. "
            "Use --force to override or unpin it first."
        )

    data.setdefault("variables", {})[key] = value
    save_vault(vault_path, password, data)


def guarded_delete(vault_path: str, password: str, key: str, force: bool = False) -> None:
    """Delete *key* from the vault, respecting lock and pin guards."""
    if is_locked(vault_path):
        raise GuardError(f"Vault '{vault_path}' is locked. Unlock it before making changes.")

    data = load_vault(vault_path, password)

    if not force and is_pinned(data, key):
        raise GuardError(
            f"Key '{key}' is pinned and cannot be deleted. "
            "Use --force to override or unpin it first."
        )

    variables = data.get("variables", {})
    if key not in variables:
        raise VaultError(f"Key '{key}' not found in vault.")

    del variables[key]
    save_vault(vault_path, password, data)
