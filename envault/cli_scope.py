"""CLI commands for scope management."""

from __future__ import annotations

import click

from envault.scope import ScopeError, assign_scope, get_keys_for_scope, list_scopes, remove_scope


@click.group(name="scope")
def scope_group() -> None:
    """Manage key scopes (dev, staging, prod, …)."""


@scope_group.command(name="assign")
@click.argument("key")
@click.argument("scope")
@click.option("--vault", required=True, envvar="ENVAULT_PATH", help="Path to vault file.")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", prompt=True, hide_input=True)
def assign_command(key: str, scope: str, vault: str, password: str) -> None:
    """Assign KEY to SCOPE."""
    try:
        assign_scope(vault, password, key, scope)
        click.echo(f"Key '{key}' assigned to scope '{scope}'.")
    except ScopeError as exc:
        raise click.ClickException(str(exc)) from exc


@scope_group.command(name="remove")
@click.argument("key")
@click.argument("scope")
@click.option("--vault", required=True, envvar="ENVAULT_PATH", help="Path to vault file.")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", prompt=True, hide_input=True)
def remove_command(key: str, scope: str, vault: str, password: str) -> None:
    """Remove SCOPE assignment from KEY."""
    try:
        remove_scope(vault, password, key, scope)
        click.echo(f"Scope '{scope}' removed from key '{key}'.")
    except ScopeError as exc:
        raise click.ClickException(str(exc)) from exc


@scope_group.command(name="list")
@click.option("--vault", required=True, envvar="ENVAULT_PATH", help="Path to vault file.")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", prompt=True, hide_input=True)
@click.option("--scope", default=None, help="Filter keys by a specific scope.")
def list_command(vault: str, password: str, scope: str | None) -> None:
    """List scope assignments. Optionally filter by --scope."""
    try:
        if scope:
            keys = get_keys_for_scope(vault, password, scope)
            if not keys:
                click.echo(f"No keys assigned to scope '{scope}'.")
            else:
                for key in keys:
                    click.echo(key)
        else:
            mapping = list_scopes(vault, password)
            if not mapping:
                click.echo("No scope assignments found.")
            else:
                for key in sorted(mapping):
                    click.echo(f"{key}: {', '.join(mapping[key])}")
    except ScopeError as exc:
        raise click.ClickException(str(exc)) from exc
