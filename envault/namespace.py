"""Namespace support for grouping vault variables under logical prefixes."""

from __future__ import annotations

from typing import Dict, List, Optional

from envault.vault import VaultError, load_vault, save_vault


class NamespaceError(Exception):
    """Raised when a namespace operation fails."""


def _ns_prefix(namespace: str) -> str:
    """Return the canonical prefix string for a namespace."""
    ns = namespace.strip().upper()
    if not ns:
        raise NamespaceError("Namespace must not be empty.")
    return ns + "__"


def list_namespaces(vault_path: str, password: str) -> List[str]:
    """Return a sorted list of distinct namespaces found in the vault."""
    data = load_vault(vault_path, password)
    variables: Dict[str, str] = data.get("variables", {})
    seen: set[str] = set()
    for key in variables:
        if "__" in key:
            ns, _, _ = key.partition("__")
            seen.add(ns)
    return sorted(seen)


def get_namespace_vars(
    vault_path: str, password: str, namespace: str
) -> Dict[str, str]:
    """Return all variables belonging to *namespace* (without the prefix)."""
    prefix = _ns_prefix(namespace)
    data = load_vault(vault_path, password)
    variables: Dict[str, str] = data.get("variables", {})
    return {
        key[len(prefix):]: value
        for key, value in variables.items()
        if key.startswith(prefix)
    }


def move_to_namespace(
    vault_path: str,
    password: str,
    namespace: str,
    keys: Optional[List[str]] = None,
    overwrite: bool = False,
) -> List[str]:
    """Move *keys* (or all keys without a namespace) under *namespace*.

    Returns the list of new keys that were written.
    """
    prefix = _ns_prefix(namespace)
    data = load_vault(vault_path, password)
    variables: Dict[str, str] = data.setdefault("variables", {})

    candidates = [
        k for k in variables if "__" not in k
    ] if keys is None else list(keys)

    moved: List[str] = []
    for key in candidates:
        if key not in variables:
            raise NamespaceError(f"Key '{key}' not found in vault.")
        new_key = prefix + key
        if new_key in variables and not overwrite:
            raise NamespaceError(
                f"Key '{new_key}' already exists. Use overwrite=True to replace."
            )
        variables[new_key] = variables.pop(key)
        moved.append(new_key)

    save_vault(vault_path, password, data)
    return moved


def delete_namespace(vault_path: str, password: str, namespace: str) -> int:
    """Delete all variables that belong to *namespace*.

    Returns the number of deleted keys.
    """
    prefix = _ns_prefix(namespace)
    data = load_vault(vault_path, password)
    variables: Dict[str, str] = data.get("variables", {})
    to_delete = [k for k in variables if k.startswith(prefix)]
    for key in to_delete:
        del variables[key]
    save_vault(vault_path, password, data)
    return len(to_delete)
