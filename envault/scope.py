"""Scope management for envault — restrict keys to named scopes (e.g. dev, staging, prod)."""

from __future__ import annotations

from typing import Dict, List

from envault.vault import VaultError, load_vault, save_vault

_SCOPE_KEY = "__scopes__"


class ScopeError(Exception):
    """Raised when a scope operation fails."""


def _scopes(data: dict) -> Dict[str, List[str]]:
    """Return the scopes mapping from vault data (key -> list of scope names)."""
    return data.get(_SCOPE_KEY, {})


def assign_scope(vault_path: str, password: str, key: str, scope: str) -> None:
    """Assign *key* to *scope*. Creates the scope entry if it does not exist."""
    data = load_vault(vault_path, password)
    if key not in data.get("vars", {}):
        raise ScopeError(f"Key '{key}' does not exist in the vault.")
    scope = scope.strip().lower()
    if not scope:
        raise ScopeError("Scope name must not be empty.")
    scopes: Dict[str, List[str]] = _scopes(data)
    assigned = scopes.get(key, [])
    if scope not in assigned:
        assigned.append(scope)
        assigned.sort()
    scopes[key] = assigned
    data[_SCOPE_KEY] = scopes
    save_vault(vault_path, password, data)


def remove_scope(vault_path: str, password: str, key: str, scope: str) -> None:
    """Remove *scope* from *key*. Raises ScopeError if the assignment does not exist."""
    data = load_vault(vault_path, password)
    scope = scope.strip().lower()
    scopes: Dict[str, List[str]] = _scopes(data)
    assigned = scopes.get(key, [])
    if scope not in assigned:
        raise ScopeError(f"Key '{key}' is not assigned to scope '{scope}'.")
    assigned.remove(scope)
    scopes[key] = assigned
    data[_SCOPE_KEY] = scopes
    save_vault(vault_path, password, data)


def list_scopes(vault_path: str, password: str) -> Dict[str, List[str]]:
    """Return a mapping of every key that has at least one scope assigned."""
    data = load_vault(vault_path, password)
    return {k: v for k, v in _scopes(data).items() if v}


def get_keys_for_scope(vault_path: str, password: str, scope: str) -> List[str]:
    """Return sorted list of keys assigned to *scope*."""
    scope = scope.strip().lower()
    data = load_vault(vault_path, password)
    return sorted(k for k, scopes in _scopes(data).items() if scope in scopes)
