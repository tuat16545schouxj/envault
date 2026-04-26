"""Annotation support for vault variables — attach freeform notes to keys."""

from __future__ import annotations

from typing import Optional

from envault.vault import VaultError, load_vault, save_vault


class AnnotateError(Exception):
    """Raised when an annotation operation fails."""


_ANNOTATIONS_KEY = "__annotations__"


def _annotations(data: dict) -> dict:
    return data.setdefault(_ANNOTATIONS_KEY, {})


def set_annotation(vault_path: str, password: str, key: str, note: str) -> None:
    """Attach a note to *key* in the vault."""
    data = load_vault(vault_path, password)
    vars_ = data.get("vars", {})
    if key not in vars_:
        raise AnnotateError(f"Key '{key}' not found in vault.")
    if not note.strip():
        raise AnnotateError("Annotation note must not be empty.")
    _annotations(data)[key] = note.strip()
    save_vault(vault_path, password, data)


def remove_annotation(vault_path: str, password: str, key: str) -> None:
    """Remove the annotation for *key*, if any."""
    data = load_vault(vault_path, password)
    ann = _annotations(data)
    if key not in ann:
        raise AnnotateError(f"No annotation found for key '{key}'.")
    del ann[key]
    save_vault(vault_path, password, data)


def get_annotation(vault_path: str, password: str, key: str) -> Optional[str]:
    """Return the annotation for *key*, or *None* if not set."""
    data = load_vault(vault_path, password)
    return _annotations(data).get(key)


def list_annotations(vault_path: str, password: str) -> dict[str, str]:
    """Return a sorted dict of all key → note pairs."""
    data = load_vault(vault_path, password)
    ann = _annotations(data)
    return dict(sorted(ann.items()))
