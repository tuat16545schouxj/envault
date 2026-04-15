"""CLI commands for the audit log sub-group."""

from __future__ import annotations

from typing import Optional

import click

from envault.audit import clear_log, read_log


@click.group("audit")
def audit_group() -> None:
    """Inspect and manage the envault audit log."""


@audit_group.command("log")
@click.option("--log-file", default=None, help="Path to audit log file.")
@click.option("--limit", default=20, show_default=True, help="Number of recent entries to show.")
@click.option("--action", default=None, help="Filter by action type (set, delete, export, ...).")
def log_command(log_file: Optional[str], limit: int, action: Optional[str]) -> None:
    """Display recent audit log entries."""
    entries = read_log(log_path=log_file)
    if action:
        entries = [e for e in entries if e.action == action]
    entries = entries[-limit:]
    if not entries:
        click.echo("No audit log entries found.")
        return
    click.echo(f"{'TIMESTAMP':<30} {'USER':<15} {'ACTION':<10} {'KEY':<20} DETAILS")
    click.echo("-" * 85)
    for e in entries:
        key_display = e.key or "-"
        click.echo(f"{e.timestamp:<30} {e.user:<15} {e.action:<10} {key_display:<20} {e.details}")


@audit_group.command("clear")
@click.option("--log-file", default=None, help="Path to audit log file.")
@click.confirmation_option(prompt="Are you sure you want to clear the audit log?")
def clear_command(log_file: Optional[str]) -> None:
    """Permanently delete the audit log."""
    clear_log(log_path=log_file)
    click.echo("Audit log cleared.")
