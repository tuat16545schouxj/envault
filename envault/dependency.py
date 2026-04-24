"""Dependency tracking between vault variables."""
from __future__ import annotations

from typing import Dict, List, Optional

from envault.vault import VaultError, load_vault, save_vault


class DependencyError(Exception):
    """Raised when a dependency operation fails."""


_DEP_KEY = "__dependencies__"


def _deps(data: dict) -> dict:
    return data.get(_DEP_KEY, {})


def add_dependency(vault_path: str, password: str, key: str, depends_on: str) -> None:
    """Record that *key* depends on *depends_on*."""
    data = load_vault(vault_path, password)
    vars_ = data.get("vars", {})
    if key not in vars_:
        raise DependencyError(f"Key not found: {key!r}")
    if depends_on not in vars_:
        raise DependencyError(f"Key not found: {depends_on!r}")
    if key == depends_on:
        raise DependencyError("A key cannot depend on itself.")
    deps = _deps(data)
    deps.setdefault(key, [])
    if depends_on not in deps[key]:
        deps[key].append(depends_on)
    data[_DEP_KEY] = deps
    save_vault(vault_path, password, data)


def remove_dependency(vault_path: str, password: str, key: str, depends_on: str) -> None:
    """Remove the dependency of *key* on *depends_on*."""
    data = load_vault(vault_path, password)
    deps = _deps(data)
    if key not in deps or depends_on not in deps[key]:
        raise DependencyError(f"No dependency from {key!r} on {depends_on!r}.")
    deps[key].remove(depends_on)
    if not deps[key]:
        del deps[key]
    data[_DEP_KEY] = deps
    save_vault(vault_path, password, data)


def list_dependencies(vault_path: str, password: str, key: Optional[str] = None) -> Dict[str, List[str]]:
    """Return dependency map, optionally filtered to a single key."""
    data = load_vault(vault_path, password)
    deps = _deps(data)
    if key is not None:
        return {key: sorted(deps.get(key, []))}
    return {k: sorted(v) for k, v in sorted(deps.items())}


def dependents_of(vault_path: str, password: str, key: str) -> List[str]:
    """Return all keys that directly depend on *key*."""
    data = load_vault(vault_path, password)
    deps = _deps(data)
    return sorted(k for k, v in deps.items() if key in v)
