"""CLI commands for managing vault key access rules."""

from __future__ import annotations

import click

from envault.access import AccessError, check_access, list_rules, remove_rule, set_rule


@click.group("access")
def access_group() -> None:
    """Manage read/write access rules for vault keys."""


@access_group.command("set")
@click.argument("pattern")
@click.argument("mode", type=click.Choice(["ro", "rw", "none"]))
@click.option("--vault", required=True, envvar="ENVAULT_VAULT", help="Path to vault file.")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", prompt=True, hide_input=True)
def set_command(pattern: str, mode: str, vault: str, password: str) -> None:
    """Set an access rule for keys matching PATTERN."""
    try:
        set_rule(vault, password, pattern, mode)
        click.echo(f"Access rule set: '{pattern}' → {mode}")
    except AccessError as exc:
        raise click.ClickException(str(exc)) from exc


@access_group.command("remove")
@click.argument("pattern")
@click.option("--vault", required=True, envvar="ENVAULT_VAULT", help="Path to vault file.")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", prompt=True, hide_input=True)
def remove_command(pattern: str, vault: str, password: str) -> None:
    """Remove the access rule for PATTERN."""
    try:
        remove_rule(vault, password, pattern)
        click.echo(f"Access rule removed: '{pattern}'")
    except AccessError as exc:
        raise click.ClickException(str(exc)) from exc


@access_group.command("list")
@click.option("--vault", required=True, envvar="ENVAULT_VAULT", help="Path to vault file.")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", prompt=True, hide_input=True)
def list_command(vault: str, password: str) -> None:
    """List all access rules."""
    try:
        rules = list_rules(vault, password)
    except AccessError as exc:
        raise click.ClickException(str(exc)) from exc
    if not rules:
        click.echo("No access rules defined.")
        return
    for rule in rules:
        click.echo(f"  {rule['pattern']:<30} {rule['mode']}")


@access_group.command("check")
@click.argument("key")
@click.argument("mode", type=click.Choice(["ro", "rw"]))
@click.option("--vault", required=True, envvar="ENVAULT_VAULT", help="Path to vault file.")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", prompt=True, hide_input=True)
def check_command(key: str, mode: str, vault: str, password: str) -> None:
    """Check whether KEY has the required access MODE."""
    try:
        allowed = check_access(vault, password, key, mode)
    except AccessError as exc:
        raise click.ClickException(str(exc)) from exc
    if allowed:
        click.echo(f"ALLOWED: '{key}' has '{mode}' access.")
    else:
        click.echo(f"DENIED: '{key}' does not have '{mode}' access.")
        raise SystemExit(1)
