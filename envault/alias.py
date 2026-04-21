"""Alias support: map short names to vault variable keys."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from envault.vault import VaultError, load_vault, save_vault

_ALIAS_NS = "__aliases__"


class AliasError(Exception):
    """Raised when an alias operation fails."""


def _aliases(vault: dict) -> dict:
    """Return the alias mapping stored inside a vault dict."""
    return vault.get(_ALIAS_NS, {})


def set_alias(vault_path: Path, password: str, alias: str, key: str) -> None:
    """Create or update *alias* to point at *key*.

    Raises AliasError if *key* does not exist in the vault.
    """
    vault = load_vault(vault_path, password)
    variables: dict = vault.get("variables", {})
    if key not in variables:
        raise AliasError(f"Key '{key}' not found in vault.")
    aliases = vault.setdefault(_ALIAS_NS, {})
    aliases[alias] = key
    save_vault(vault_path, password, vault)


def remove_alias(vault_path: Path, password: str, alias: str) -> None:
    """Delete *alias* from the vault.

    Raises AliasError if the alias does not exist.
    """
    vault = load_vault(vault_path, password)
    aliases: dict = vault.get(_ALIAS_NS, {})
    if alias not in aliases:
        raise AliasError(f"Alias '{alias}' not found.")
    del aliases[alias]
    vault[_ALIAS_NS] = aliases
    save_vault(vault_path, password, vault)


def resolve_alias(vault_path: Path, password: str, alias: str) -> str:
    """Return the key that *alias* maps to.

    Raises AliasError if the alias does not exist.
    """
    vault = load_vault(vault_path, password)
    aliases = _aliases(vault)
    if alias not in aliases:
        raise AliasError(f"Alias '{alias}' not found.")
    return aliases[alias]


def list_aliases(vault_path: Path, password: str) -> dict[str, str]:
    """Return all aliases as a {alias: key} mapping, sorted by alias name."""
    vault = load_vault(vault_path, password)
    return dict(sorted(_aliases(vault).items()))
