"""CLI commands for managing variable priorities."""
from __future__ import annotations

import click

from envault.priority import (
    PriorityError,
    get_priority,
    list_priorities,
    remove_priority,
    set_priority,
    sorted_by_priority,
)


@click.group("priority")
def priority_group() -> None:
    """Manage variable priority levels."""


@priority_group.command("set")
@click.option("--vault", required=True, envvar="ENVAULT_VAULT", help="Vault file path.")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", prompt=True, hide_input=True)
@click.argument("key")
@click.argument("level", type=int)
def set_command(vault: str, password: str, key: str, level: int) -> None:
    """Set the priority LEVEL for KEY."""
    try:
        set_priority(vault, password, key, level)
        click.echo(f"Priority for '{key}' set to {level}.")
    except PriorityError as exc:
        raise click.ClickException(str(exc)) from exc


@priority_group.command("remove")
@click.option("--vault", required=True, envvar="ENVAULT_VAULT")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", prompt=True, hide_input=True)
@click.argument("key")
def remove_command(vault: str, password: str, key: str) -> None:
    """Remove explicit priority from KEY (resets to default 0)."""
    try:
        remove_priority(vault, password, key)
        click.echo(f"Priority removed from '{key}'.")
    except PriorityError as exc:
        raise click.ClickException(str(exc)) from exc


@priority_group.command("show")
@click.option("--vault", required=True, envvar="ENVAULT_VAULT")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", prompt=True, hide_input=True)
@click.argument("key")
def show_command(vault: str, password: str, key: str) -> None:
    """Show the priority level for KEY."""
    try:
        level = get_priority(vault, password, key)
        click.echo(f"{key}: {level}")
    except PriorityError as exc:
        raise click.ClickException(str(exc)) from exc


@priority_group.command("list")
@click.option("--vault", required=True, envvar="ENVAULT_VAULT")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", prompt=True, hide_input=True)
@click.option("--sorted", "show_sorted", is_flag=True, help="Show all keys ordered by priority.")
def list_command(vault: str, password: str, show_sorted: bool) -> None:
    """List all explicit priorities, or all keys sorted by priority."""
    try:
        if show_sorted:
            keys = sorted_by_priority(vault, password)
            if not keys:
                click.echo("No variables found.")
            for k in keys:
                click.echo(k)
        else:
            entries = list_priorities(vault, password)
            if not entries:
                click.echo("No explicit priorities set.")
            for entry in entries:
                click.echo(f"{entry['key']}: {entry['priority']}")
    except PriorityError as exc:
        raise click.ClickException(str(exc)) from exc
