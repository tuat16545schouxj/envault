"""Group management for envault — organize vault keys into named groups."""

from __future__ import annotations

from typing import Dict, List

from envault.vault import VaultError, load_vault, save_vault


class GroupError(Exception):
    """Raised when a group operation fails."""


_GROUPS_KEY = "__groups__"


def _groups(data: dict) -> Dict[str, List[str]]:
    """Return the groups mapping from vault data."""
    return data.get(_GROUPS_KEY, {})


def create_group(vault_path: str, password: str, group: str) -> None:
    """Create an empty group (no-op if it already exists)."""
    data = load_vault(vault_path, password)
    groups = _groups(data)
    if group not in groups:
        groups[group] = []
    data[_GROUPS_KEY] = groups
    save_vault(vault_path, password, data)


def add_to_group(vault_path: str, password: str, group: str, key: str) -> None:
    """Add *key* to *group*, creating the group if needed."""
    data = load_vault(vault_path, password)
    if key not in data:
        raise GroupError(f"Key '{key}' not found in vault.")
    groups = _groups(data)
    members = groups.setdefault(group, [])
    if key not in members:
        members.append(key)
        members.sort()
    data[_GROUPS_KEY] = groups
    save_vault(vault_path, password, data)


def remove_from_group(vault_path: str, password: str, group: str, key: str) -> None:
    """Remove *key* from *group*."""
    data = load_vault(vault_path, password)
    groups = _groups(data)
    if group not in groups:
        raise GroupError(f"Group '{group}' does not exist.")
    if key not in groups[group]:
        raise GroupError(f"Key '{key}' is not in group '{group}'.")
    groups[group].remove(key)
    data[_GROUPS_KEY] = groups
    save_vault(vault_path, password, data)


def delete_group(vault_path: str, password: str, group: str) -> None:
    """Delete a group entirely."""
    data = load_vault(vault_path, password)
    groups = _groups(data)
    if group not in groups:
        raise GroupError(f"Group '{group}' does not exist.")
    del groups[group]
    data[_GROUPS_KEY] = groups
    save_vault(vault_path, password, data)


def list_groups(vault_path: str, password: str) -> List[str]:
    """Return sorted list of group names."""
    data = load_vault(vault_path, password)
    return sorted(_groups(data).keys())


def get_group_keys(vault_path: str, password: str, group: str) -> List[str]:
    """Return sorted list of keys belonging to *group*."""
    data = load_vault(vault_path, password)
    groups = _groups(data)
    if group not in groups:
        raise GroupError(f"Group '{group}' does not exist.")
    return sorted(groups[group])
