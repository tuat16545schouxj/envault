"""CLI commands for pin management."""

from __future__ import annotations

import click

from envault.pin import PinError, list_pins, pin_var, unpin_var, get_pin_reason


@click.group("pin")
def pin_group() -> None:
    """Pin variables to prevent accidental overwrites."""


@pin_group.command("add")
@click.argument("key")
@click.option("--reason", "-r", default="", help="Optional reason for pinning.")
@click.option("--vault", envvar="ENVAULT_VAULT", required=True, help="Path to vault file.")
@click.option("--password", envvar="ENVAULT_PASSWORD", prompt=True, hide_input=True)
def add_command(key: str, reason: str, vault: str, password: str) -> None:
    """Pin KEY so it cannot be overwritten."""
    try:
        pin_var(vault, password, key, reason)
        msg = f"Pinned '{key}'."
        if reason:
            msg += f" Reason: {reason}"
        click.echo(msg)
    except PinError as exc:
        raise click.ClickException(str(exc)) from exc


@pin_group.command("remove")
@click.argument("key")
@click.option("--vault", envvar="ENVAULT_VAULT", required=True)
@click.option("--password", envvar="ENVAULT_PASSWORD", prompt=True, hide_input=True)
def remove_command(key: str, vault: str, password: str) -> None:
    """Unpin KEY, allowing it to be overwritten again."""
    try:
        unpin_var(vault, password, key)
        click.echo(f"Unpinned '{key}'.")
    except PinError as exc:
        raise click.ClickException(str(exc)) from exc


@pin_group.command("list")
@click.option("--vault", envvar="ENVAULT_VAULT", required=True)
@click.option("--password", envvar="ENVAULT_PASSWORD", prompt=True, hide_input=True)
def list_command(vault: str, password: str) -> None:
    """List all pinned variables."""
    try:
        pins = list_pins(vault, password)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if not pins:
        click.echo("No pinned variables.")
        return
    for key, reason in sorted(pins.items()):
        line = key
        if reason:
            line += f"  # {reason}"
        click.echo(line)
