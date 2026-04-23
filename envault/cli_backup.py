"""CLI commands for vault backup management."""

from __future__ import annotations

from pathlib import Path

import click

from .backup import (
    BackupError,
    create_backup,
    delete_backup,
    list_backups,
    prune_backups,
    restore_backup,
)


@click.group("backup")
def backup_group() -> None:
    """Manage vault backups."""


@backup_group.command("create")
@click.option("--vault", required=True, help="Path to the vault file.")
@click.option("--label", default=None, help="Optional label for the backup.")
def create_command(vault: str, label: str | None) -> None:
    """Create a backup of the vault file."""
    try:
        dest = create_backup(Path(vault), label=label)
        click.echo(f"Backup created: {dest}")
    except BackupError as exc:
        raise click.ClickException(str(exc)) from exc


@backup_group.command("list")
@click.option("--vault", required=True, help="Path to the vault file.")
def list_command(vault: str) -> None:
    """List all backups for the vault."""
    backups = list_backups(Path(vault))
    if not backups:
        click.echo("No backups found.")
        return
    for b in backups:
        click.echo(str(b))


@backup_group.command("restore")
@click.option("--vault", required=True, help="Path to the vault file.")
@click.argument("backup_path")
def restore_command(vault: str, backup_path: str) -> None:
    """Restore the vault from a backup file."""
    try:
        restore_backup(Path(vault), Path(backup_path))
        click.echo(f"Vault restored from: {backup_path}")
    except BackupError as exc:
        raise click.ClickException(str(exc)) from exc


@backup_group.command("delete")
@click.argument("backup_path")
def delete_command(backup_path: str) -> None:
    """Delete a specific backup file."""
    try:
        delete_backup(Path(backup_path))
        click.echo(f"Deleted backup: {backup_path}")
    except BackupError as exc:
        raise click.ClickException(str(exc)) from exc


@backup_group.command("prune")
@click.option("--vault", required=True, help="Path to the vault file.")
@click.option("--keep", default=5, show_default=True, help="Number of backups to keep.")
def prune_command(vault: str, keep: int) -> None:
    """Prune old backups, keeping the most recent N."""
    try:
        deleted = prune_backups(Path(vault), keep=keep)
        if deleted:
            for p in deleted:
                click.echo(f"Deleted: {p}")
        else:
            click.echo("Nothing to prune.")
    except BackupError as exc:
        raise click.ClickException(str(exc)) from exc
