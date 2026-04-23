"""Integration hook: register backup_group into the main CLI.

This module is imported by envault/cli.py to attach the backup sub-command.
Kept separate so the main CLI file stays concise.

Usage in cli.py::

    from envault.cli_backup_integration import attach_backup
    attach_backup(cli)
"""

from __future__ import annotations

import click

from .backup import BackupError, create_backup
from .cli_backup import backup_group


def attach_backup(cli: click.Group) -> None:
    """Register the backup command group onto *cli*."""
    cli.add_command(backup_group, name="backup")


# ---------------------------------------------------------------------------
# Convenience: auto-backup hook that other commands can call
# ---------------------------------------------------------------------------


def auto_backup(vault_path: str | None, label: str = "auto") -> None:
    """Create a backup before a destructive operation if *vault_path* is set.

    Silently skips if the vault file does not yet exist (e.g. first-time set).
    Errors are swallowed so they never block the primary operation.
    """
    if not vault_path:
        return
    from pathlib import Path

    path = Path(vault_path)
    if not path.exists():
        return
    try:
        create_backup(path, label=label)
    except BackupError:
        pass
