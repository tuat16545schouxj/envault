"""Pin management: lock a variable to a specific value, preventing overwrites."""

from __future__ import annotations

from typing import Optional

from envault.vault import VaultError, load_vault, save_vault

PINS_KEY = "__pins__"


class PinError(Exception):
    """Raised when a pin operation fails."""


def _pins(data: dict) -> dict:
    return data.setdefault(PINS_KEY, {})


def pin_var(vault_path: str, password: str, key: str, reason: str = "") -> None:
    """Pin *key* so that set_var will refuse to overwrite it."""
    data = load_vault(vault_path, password)
    if key not in data.get("variables", {}):
        raise PinError(f"Key '{key}' does not exist in the vault.")
    _pins(data)[key] = reason or ""
    save_vault(vault_path, password, data)


def unpin_var(vault_path: str, password: str, key: str) -> None:
    """Remove the pin from *key*."""
    data = load_vault(vault_path, password)
    pins = _pins(data)
    if key not in pins:
        raise PinError(f"Key '{key}' is not pinned.")
    del pins[key]
    save_vault(vault_path, password, data)


def is_pinned(data: dict, key: str) -> bool:
    """Return True if *key* is pinned in *data*."""
    return key in data.get(PINS_KEY, {})


def list_pins(vault_path: str, password: str) -> dict[str, str]:
    """Return a mapping of pinned key -> reason."""
    data = load_vault(vault_path, password)
    return dict(data.get(PINS_KEY, {}))


def get_pin_reason(vault_path: str, password: str, key: str) -> Optional[str]:
    """Return the pin reason for *key*, or None if not pinned."""
    data = load_vault(vault_path, password)
    return data.get(PINS_KEY, {}).get(key)
