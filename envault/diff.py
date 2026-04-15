"""Diff utilities for comparing vault variables across profiles or revisions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from envault.vault import VaultError, load_vault


class DiffError(Exception):
    """Raised when a diff operation fails."""


@dataclass
class DiffEntry:
    key: str
    status: str  # 'added', 'removed', 'changed', 'unchanged'
    old_value: Optional[str] = None
    new_value: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "status": self.status,
            "old_value": self.old_value,
            "new_value": self.new_value,
        }


def diff_dicts(
    old: Dict[str, str],
    new: Dict[str, str],
    show_values: bool = False,
) -> List[DiffEntry]:
    """Compare two variable dicts and return a list of DiffEntry objects."""
    all_keys = sorted(set(old) | set(new))
    entries: List[DiffEntry] = []

    for key in all_keys:
        if key in old and key not in new:
            entries.append(DiffEntry(
                key=key,
                status="removed",
                old_value=old[key] if show_values else None,
            ))
        elif key not in old and key in new:
            entries.append(DiffEntry(
                key=key,
                status="added",
                new_value=new[key] if show_values else None,
            ))
        elif old[key] != new[key]:
            entries.append(DiffEntry(
                key=key,
                status="changed",
                old_value=old[key] if show_values else None,
                new_value=new[key] if show_values else None,
            ))
        else:
            entries.append(DiffEntry(key=key, status="unchanged"))

    return entries


def diff_vaults(
    vault_path_a: str,
    password_a: str,
    vault_path_b: str,
    password_b: str,
    show_values: bool = False,
) -> List[DiffEntry]:
    """Load two vault files and diff their variables."""
    try:
        data_a = load_vault(vault_path_a, password_a)
    except VaultError as exc:
        raise DiffError(f"Failed to load vault A: {exc}") from exc

    try:
        data_b = load_vault(vault_path_b, password_b)
    except VaultError as exc:
        raise DiffError(f"Failed to load vault B: {exc}") from exc

    vars_a: Dict[str, str] = data_a.get("variables", {})
    vars_b: Dict[str, str] = data_b.get("variables", {})

    return diff_dicts(vars_a, vars_b, show_values=show_values)
