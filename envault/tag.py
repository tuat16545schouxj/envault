"""Tag-based grouping for vault variables."""
from __future__ import annotations
from typing import Optional
from envault.vault import VaultError, load_vault, save_vault


class TagError(Exception):
    pass


def _tags_for(var_meta: dict) -> list[str]:
    return var_meta.get("tags", [])


def add_tag(vault_path: str, password: str, key: str, tag: str) -> None:
    data = load_vault(vault_path, password)
    if key not in data.get("vars", {}):
        raise TagError(f"Variable '{key}' not found.")
    meta = data.setdefault("meta", {}).setdefault(key, {})
    tags = meta.setdefault("tags", [])
    if tag not in tags:
        tags.append(tag)
    save_vault(vault_path, password, data)


def remove_tag(vault_path: str, password: str, key: str, tag: str) -> None:
    data = load_vault(vault_path, password)
    tags = data.get("meta", {}).get(key, {}).get("tags", [])
    if tag not in tags:
        raise TagError(f"Tag '{tag}' not found on '{key}'.")
    tags.remove(tag)
    save_vault(vault_path, password, data)


def list_tags(vault_path: str, password: str) -> dict[str, list[str]]:
    data = load_vault(vault_path, password)
    meta = data.get("meta", {})
    return {k: _tags_for(v) for k, v in meta.items() if _tags_for(v)}


def vars_by_tag(vault_path: str, password: str, tag: str) -> list[str]:
    data = load_vault(vault_path, password)
    meta = data.get("meta", {})
    return sorted(k for k, v in meta.items() if tag in _tags_for(v))
