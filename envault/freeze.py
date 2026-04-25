"""Freeze/unfreeze vault variables to prevent accidental modification."""

from __future__ import annotations

from typing import List

from envault.vault import VaultError, load_vault, save_vault

_FROZEN_KEY = "__frozen__"


class FreezeError(Exception):
    """Raised when a freeze/unfreeze operation fails."""


def _frozen_set(vault: dict) -> set:
    meta = vault.get("_meta", {})
    return set(meta.get(_FROZEN_KEY, []))


def freeze_var(vault_path: str, password: str, key: str) -> None:
    """Mark *key* as frozen so it cannot be modified or deleted."""
    vault = load_vault(vault_path, password)
    if key not in vault.get("variables", {}):
        raise FreezeError(f"Key '{key}' does not exist in the vault.")
    meta = vault.setdefault("_meta", {})
    frozen: list = meta.setdefault(_FROZEN_KEY, [])
    if key not in frozen:
        frozen.append(key)
        frozen.sort()
    save_vault(vault_path, password, vault)


def unfreeze_var(vault_path: str, password: str, key: str) -> None:
    """Remove the frozen flag from *key*."""
    vault = load_vault(vault_path, password)
    meta = vault.setdefault("_meta", {})
    frozen: list = meta.get(_FROZEN_KEY, [])
    if key not in frozen:
        raise FreezeError(f"Key '{key}' is not frozen.")
    frozen.remove(key)
    save_vault(vault_path, password, vault)


def list_frozen(vault_path: str, password: str) -> List[str]:
    """Return a sorted list of all frozen keys."""
    vault = load_vault(vault_path, password)
    return sorted(_frozen_set(vault))


def is_frozen(vault_path: str, password: str, key: str) -> bool:
    """Return True if *key* is currently frozen."""
    vault = load_vault(vault_path, password)
    return key in _frozen_set(vault)


def assert_not_frozen(vault_path: str, password: str, key: str) -> None:
    """Raise FreezeError if *key* is frozen; used by guarded operations."""
    if is_frozen(vault_path, password, key):
        raise FreezeError(
            f"Key '{key}' is frozen and cannot be modified or deleted. "
            "Run 'envault freeze unfreeze' first."
        )
