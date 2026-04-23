"""Vault backup and restore functionality for envault."""

from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import List


class BackupError(Exception):
    """Raised when a backup or restore operation fails."""


_BACKUP_SUFFIX = ".bak"
_BACKUP_DIR_NAME = ".envault_backups"


def _backup_dir(vault_path: Path) -> Path:
    return vault_path.parent / _BACKUP_DIR_NAME


def _backup_name(vault_path: Path, label: str | None = None) -> str:
    ts = int(time.time())
    stem = vault_path.stem
    tag = f"_{label}" if label else ""
    return f"{stem}{tag}_{ts}{_BACKUP_SUFFIX}"


def create_backup(vault_path: Path, label: str | None = None) -> Path:
    """Copy the vault file into the backup directory and return the backup path."""
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise BackupError(f"Vault file not found: {vault_path}")

    backup_dir = _backup_dir(vault_path)
    backup_dir.mkdir(parents=True, exist_ok=True)

    name = _backup_name(vault_path, label)
    dest = backup_dir / name
    shutil.copy2(vault_path, dest)
    return dest


def list_backups(vault_path: Path) -> List[Path]:
    """Return backup paths sorted oldest-first."""
    backup_dir = _backup_dir(Path(vault_path))
    if not backup_dir.exists():
        return []
    files = sorted(backup_dir.glob(f"*{_BACKUP_SUFFIX}"), key=lambda p: p.stat().st_mtime)
    return files


def restore_backup(vault_path: Path, backup_path: Path) -> None:
    """Overwrite the vault file with the given backup."""
    backup_path = Path(backup_path)
    if not backup_path.exists():
        raise BackupError(f"Backup file not found: {backup_path}")
    shutil.copy2(backup_path, vault_path)


def delete_backup(backup_path: Path) -> None:
    """Delete a single backup file."""
    backup_path = Path(backup_path)
    if not backup_path.exists():
        raise BackupError(f"Backup file not found: {backup_path}")
    backup_path.unlink()


def prune_backups(vault_path: Path, keep: int = 5) -> List[Path]:
    """Delete oldest backups, keeping at most *keep* files. Returns deleted paths."""
    if keep < 1:
        raise BackupError("keep must be >= 1")
    all_backups = list_backups(vault_path)
    to_delete = all_backups[: max(0, len(all_backups) - keep)]
    for p in to_delete:
        p.unlink()
    return to_delete
