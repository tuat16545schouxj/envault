"""Label management for vault variables.

Labels are free-form string tags attached to keys for categorisation,
distinct from structured tags (tag.py) in that multiple labels can be
stored per key and queried collectively.
"""
from __future__ import annotations

from typing import Dict, List

from envault.vault import VaultError, load_vault, save_vault

__all__ = ["LabelError", "add_label", "remove_label", "list_labels", "keys_for_label"]

_LABEL_KEY = "__labels__"


class LabelError(Exception):
    """Raised when a label operation fails."""


def _labels(data: dict) -> Dict[str, List[str]]:
    """Return the labels mapping from vault data, defaulting to empty dict."""
    return data.get(_LABEL_KEY, {})


def add_label(vault_path: str, password: str, key: str, label: str) -> None:
    """Attach *label* to *key* in the vault (idempotent)."""
    data = load_vault(vault_path, password)
    if key not in data:
        raise LabelError(f"Key '{key}' not found in vault.")
    label = label.strip()
    if not label:
        raise LabelError("Label must not be empty.")
    labels: Dict[str, List[str]] = _labels(data)
    existing = labels.get(key, [])
    if label not in existing:
        existing.append(label)
        existing.sort()
    labels[key] = existing
    data[_LABEL_KEY] = labels
    save_vault(vault_path, password, data)


def remove_label(vault_path: str, password: str, key: str, label: str) -> None:
    """Detach *label* from *key*. Raises LabelError if label not present."""
    data = load_vault(vault_path, password)
    labels: Dict[str, List[str]] = _labels(data)
    existing = labels.get(key, [])
    if label not in existing:
        raise LabelError(f"Label '{label}' not found on key '{key}'.")
    existing.remove(label)
    labels[key] = existing
    data[_LABEL_KEY] = labels
    save_vault(vault_path, password, data)


def list_labels(vault_path: str, password: str, key: str) -> List[str]:
    """Return sorted list of labels attached to *key*."""
    data = load_vault(vault_path, password)
    return sorted(_labels(data).get(key, []))


def keys_for_label(vault_path: str, password: str, label: str) -> List[str]:
    """Return sorted list of keys that carry *label*."""
    data = load_vault(vault_path, password)
    return sorted(k for k, lbls in _labels(data).items() if label in lbls)
