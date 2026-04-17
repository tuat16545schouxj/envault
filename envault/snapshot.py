"""Snapshot: save and restore point-in-time copies of vault variables."""

from __future__ import annotations

import datetime
from typing import Optional

from envault.vault import VaultError, load_vault, save_vault


class SnapshotError(Exception):
    pass


_SNAPSHOT_PREFIX = "__snapshot__"


def _snapshot_key(name: str) -> str:
    return f"{_SNAPSHOT_PREFIX}{name}"


def create_snapshot(vault_path: str, password: str, name: Optional[str] = None) -> str:
    """Save current variables under a snapshot name. Returns the snapshot name."""
    data = load_vault(vault_path, password)
    variables = data.get("variables", {})
    if not variables:
        raise SnapshotError("No variables to snapshot.")

    if name is None:
        name = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    key = _snapshot_key(name)
    snapshots = data.get("snapshots", {})
    if key in snapshots:
        raise SnapshotError(f"Snapshot '{name}' already exists.")

    snapshots[key] = dict(variables)
    data["snapshots"] = snapshots
    save_vault(vault_path, password, data)
    return name


def list_snapshots(vault_path: str, password: str) -> list[str]:
    """Return sorted list of snapshot names."""
    data = load_vault(vault_path, password)
    snapshots = data.get("snapshots", {})
    names = [k[len(_SNAPSHOT_PREFIX):] for k in snapshots if k.startswith(_SNAPSHOT_PREFIX)]
    return sorted(names)


def restore_snapshot(vault_path: str, password: str, name: str, overwrite: bool = False) -> dict:
    """Restore variables from a snapshot. Returns restored variables dict."""
    data = load_vault(vault_path, password)
    key = _snapshot_key(name)
    snapshots = data.get("snapshots", {})
    if key not in snapshots:
        raise SnapshotError(f"Snapshot '{name}' not found.")

    saved = snapshots[key]
    variables = data.get("variables", {})
    if overwrite:
        variables = dict(saved)
    else:
        for k, v in saved.items():
            if k not in variables:
                variables[k] = v
    data["variables"] = variables
    save_vault(vault_path, password, data)
    return variables


def delete_snapshot(vault_path: str, password: str, name: str) -> None:
    """Delete a named snapshot."""
    data = load_vault(vault_path, password)
    key = _snapshot_key(name)
    snapshots = data.get("snapshots", {})
    if key not in snapshots:
        raise SnapshotError(f"Snapshot '{name}' not found.")
    del snapshots[key]
    data["snapshots"] = snapshots
    save_vault(vault_path, password, data)
