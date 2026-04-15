"""Profile management for envault — named sets of environment variables."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from envault.vault import VaultError, load_vault, save_vault


class ProfileError(Exception):
    """Raised when a profile operation fails."""


PROFILE_META_KEY = "__envault_profiles__"


def list_profiles(vault_path: Path, password: str) -> List[str]:
    """Return the names of all profiles stored in the vault."""
    data = load_vault(vault_path, password)
    raw = data.get(PROFILE_META_KEY)
    if not raw:
        return []
    profiles: Dict[str, List[str]] = json.loads(raw)
    return sorted(profiles.keys())


def save_profile(vault_path: Path, password: str, profile_name: str) -> None:
    """Snapshot the current vault variables into a named profile."""
    data = load_vault(vault_path, password)
    raw = data.get(PROFILE_META_KEY)
    profiles: Dict[str, List[str]] = json.loads(raw) if raw else {}
    # Store the names of all non-meta keys as this profile's variable list
    var_keys = [k for k in data if k != PROFILE_META_KEY]
    profiles[profile_name] = var_keys
    data[PROFILE_META_KEY] = json.dumps(profiles)
    save_vault(vault_path, password, data)


def delete_profile(vault_path: Path, password: str, profile_name: str) -> None:
    """Remove a named profile (does not delete the underlying variables)."""
    data = load_vault(vault_path, password)
    raw = data.get(PROFILE_META_KEY)
    profiles: Dict[str, List[str]] = json.loads(raw) if raw else {}
    if profile_name not in profiles:
        raise ProfileError(f"Profile '{profile_name}' does not exist.")
    del profiles[profile_name]
    data[PROFILE_META_KEY] = json.dumps(profiles)
    save_vault(vault_path, password, data)


def get_profile_vars(
    vault_path: Path, password: str, profile_name: str
) -> Dict[str, str]:
    """Return the key/value pairs that belong to a named profile."""
    data = load_vault(vault_path, password)
    raw = data.get(PROFILE_META_KEY)
    profiles: Dict[str, List[str]] = json.loads(raw) if raw else {}
    if profile_name not in profiles:
        raise ProfileError(f"Profile '{profile_name}' does not exist.")
    keys = profiles[profile_name]
    return {k: data[k] for k in keys if k in data}
