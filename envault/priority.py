"""Priority management for vault variables.

Allows assigning numeric priority levels to keys, useful for cascade
resolution ordering and conflict tiebreaking.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from envault.vault import VaultError, load_vault, save_vault

_PRIORITY_KEY = "__priorities__"
DEFAULT_PRIORITY = 0


class PriorityError(Exception):
    """Raised when a priority operation fails."""


def _priorities(data: dict) -> dict:
    return data.setdefault(_PRIORITY_KEY, {})


def set_priority(vault_path: str, password: str, key: str, level: int) -> None:
    """Assign a priority *level* to *key*."""
    data = load_vault(vault_path, password)
    if key not in data.get("vars", {}):
        raise PriorityError(f"Key '{key}' not found in vault.")
    if not isinstance(level, int):
        raise PriorityError("Priority level must be an integer.")
    _priorities(data)[key] = level
    save_vault(vault_path, password, data)


def remove_priority(vault_path: str, password: str, key: str) -> None:
    """Remove any explicit priority from *key* (resets to default)."""
    data = load_vault(vault_path, password)
    priorities = _priorities(data)
    if key not in priorities:
        raise PriorityError(f"Key '{key}' has no explicit priority set.")
    del priorities[key]
    save_vault(vault_path, password, data)


def get_priority(vault_path: str, password: str, key: str) -> int:
    """Return the priority level for *key*, or DEFAULT_PRIORITY if unset."""
    data = load_vault(vault_path, password)
    return _priorities(data).get(key, DEFAULT_PRIORITY)


def list_priorities(vault_path: str, password: str) -> List[Dict]:
    """Return all explicit priorities sorted by level descending, then key."""
    data = load_vault(vault_path, password)
    priorities = _priorities(data)
    result = [
        {"key": k, "priority": v}
        for k, v in priorities.items()
    ]
    result.sort(key=lambda x: (-x["priority"], x["key"]))
    return result


def sorted_by_priority(vault_path: str, password: str) -> List[str]:
    """Return all variable keys sorted by priority descending, then alphabetically."""
    data = load_vault(vault_path, password)
    variables = list(data.get("vars", {}).keys())
    priorities = _priorities(data)
    variables.sort(key=lambda k: (-priorities.get(k, DEFAULT_PRIORITY), k))
    return variables
