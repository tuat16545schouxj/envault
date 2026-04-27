"""Lifecycle hooks for vault keys: on_create, on_update, on_delete."""

from __future__ import annotations

from typing import Any

from envault.vault import load_vault, save_vault, VaultError

LIFECYCLE_KEY = "__lifecycle_hooks__"

VALID_EVENTS = {"on_create", "on_update", "on_delete"}


class LifecycleError(Exception):
    """Raised when a lifecycle operation fails."""


def _hooks(vault: dict) -> dict:
    return vault.setdefault(LIFECYCLE_KEY, {})


def set_hook(vault_path: str, password: str, key: str, event: str, command: str) -> None:
    """Register a shell command to run when *event* fires for *key*."""
    if event not in VALID_EVENTS:
        raise LifecycleError(
            f"Unknown event '{event}'. Valid events: {sorted(VALID_EVENTS)}"
        )
    vault = load_vault(vault_path, password)
    if key not in vault.get("vars", {}):
        raise LifecycleError(f"Key '{key}' not found in vault.")
    hooks = _hooks(vault)
    hooks.setdefault(key, {})[event] = command
    save_vault(vault_path, password, vault)


def remove_hook(vault_path: str, password: str, key: str, event: str) -> None:
    """Remove the hook for *event* on *key*."""
    vault = load_vault(vault_path, password)
    hooks = _hooks(vault)
    if key not in hooks or event not in hooks[key]:
        raise LifecycleError(f"No '{event}' hook found for key '{key}'.")
    del hooks[key][event]
    if not hooks[key]:
        del hooks[key]
    save_vault(vault_path, password, vault)


def list_hooks(vault_path: str, password: str, key: str | None = None) -> dict[str, Any]:
    """Return all hooks, optionally filtered by *key*."""
    vault = load_vault(vault_path, password)
    hooks = vault.get(LIFECYCLE_KEY, {})
    if key is not None:
        return {key: hooks.get(key, {})}
    return dict(hooks)


def get_hook(vault_path: str, password: str, key: str, event: str) -> str | None:
    """Return the command registered for *event* on *key*, or None."""
    vault = load_vault(vault_path, password)
    return vault.get(LIFECYCLE_KEY, {}).get(key, {}).get(event)
