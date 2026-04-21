"""CLI commands for variable change history."""

from __future__ import annotations

import time
from datetime import datetime

import click

from envault.history import clear_history, get_history
from envault.vault import VaultError, load_vault, save_vault


@click.group("history")
def history_group() -> None:
    """View and manage variable change history."""


@history_group.command("log")
@click.option("--vault", "vault_path", required=True, help="Path to the vault file.")
@click.option("--password", required=True, hide_input=True, help="Vault password.")
@click.option("--key", default=None, help="Filter history by variable key.")
@click.option("--limit", default=20, show_default=True, help="Max entries to show.")
def log_command(vault_path: str, password: str, key: str, limit: int) -> None:
    """Display recent change history."""
    try:
        vault = load_vault(vault_path, password)
    except VaultError as exc:
        raise click.ClickException(str(exc)) from exc

    entries = get_history(vault, key=key, limit=limit)
    if not entries:
        click.echo("No history entries found.")
        return

    for entry in entries:
        ts = datetime.fromtimestamp(entry.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        old = entry.old_value if entry.old_value is not None else "<none>"
        new = entry.new_value if entry.new_value is not None else "<none>"
        click.echo(f"[{ts}] {entry.action.upper():6s} {entry.key}: {old!r} -> {new!r}")


@history_group.command("clear")
@click.option("--vault", "vault_path", required=True, help="Path to the vault file.")
@click.option("--password", required=True, hide_input=True, help="Vault password.")
@click.option("--key", default=None, help="Clear history only for this key.")
@click.confirmation_option(prompt="Clear history? This cannot be undone.")
def clear_command(vault_path: str, password: str, key: str) -> None:
    """Remove history entries from the vault."""
    try:
        vault = load_vault(vault_path, password)
        removed = clear_history(vault, key=key)
        save_vault(vault_path, password, vault)
    except VaultError as exc:
        raise click.ClickException(str(exc)) from exc

    target = f"for key '{key}'" if key else "(all keys)"
    click.echo(f"Cleared {removed} history entr{'y' if removed == 1 else 'ies'} {target}.")
