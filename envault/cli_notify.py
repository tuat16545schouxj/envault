"""CLI commands for managing vault notification channels."""

from __future__ import annotations

import click

from envault.notify import NotifyError, add_channel, list_channels, remove_channel


@click.group("notify")
def notify_group() -> None:
    """Manage notification channels for vault events."""


@notify_group.command("add")
@click.option("--vault", required=True, type=click.Path(), help="Path to vault file.")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", help="Vault password.")
@click.option("--kind", required=True, type=click.Choice(["email", "slack"]), help="Channel type.")
@click.option("--target", required=True, help="Email address or Slack webhook URL.")
@click.option("--events", required=True, help="Comma-separated events: set,delete,rotate,import.")
def add_command(vault: str, password: str, kind: str, target: str, events: str) -> None:
    """Add a notification channel."""
    from pathlib import Path

    event_list = [e.strip() for e in events.split(",") if e.strip()]
    try:
        ch = add_channel(Path(vault), password, kind, target, event_list)
        click.echo(f"Added {ch.kind} channel → {ch.target} for events: {', '.join(ch.events)}")
    except NotifyError as exc:
        raise click.ClickException(str(exc)) from exc


@notify_group.command("remove")
@click.option("--vault", required=True, type=click.Path(), help="Path to vault file.")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", help="Vault password.")
@click.option("--target", required=True, help="Target identifier to remove.")
def remove_command(vault: str, password: str, target: str) -> None:
    """Remove a notification channel by target."""
    from pathlib import Path

    try:
        remove_channel(Path(vault), password, target)
        click.echo(f"Removed channel: {target}")
    except NotifyError as exc:
        raise click.ClickException(str(exc)) from exc


@notify_group.command("list")
@click.option("--vault", required=True, type=click.Path(), help="Path to vault file.")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", help="Vault password.")
def list_command(vault: str, password: str) -> None:
    """List all registered notification channels."""
    from pathlib import Path

    try:
        channels = list_channels(Path(vault), password)
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc

    if not channels:
        click.echo("No notification channels configured.")
        return

    for ch in channels:
        click.echo(f"[{ch.kind}] {ch.target}  events={','.join(ch.events)}")
