"""CLI commands for vault namespace management."""

from __future__ import annotations

import click

from envault.namespace import (
    NamespaceError,
    delete_namespace,
    get_namespace_vars,
    list_namespaces,
    move_to_namespace,
)


@click.group(name="namespace", help="Manage variable namespaces in the vault.")
def namespace_group() -> None:
    pass


@namespace_group.command(name="list")
@click.option("--vault", required=True, envvar="ENVAULT_PATH", help="Path to vault file.")
@click.password_option("--password", envvar="ENVAULT_PASSWORD", confirmation_prompt=False)
def list_command(vault: str, password: str) -> None:
    """List all namespaces present in the vault."""
    try:
        namespaces = list_namespaces(vault, password)
    except NamespaceError as exc:
        raise click.ClickException(str(exc))

    if not namespaces:
        click.echo("No namespaces found.")
        return
    for ns in namespaces:
        click.echo(ns)


@namespace_group.command(name="show")
@click.argument("namespace")
@click.option("--vault", required=True, envvar="ENVAULT_PATH", help="Path to vault file.")
@click.password_option("--password", envvar="ENVAULT_PASSWORD", confirmation_prompt=False)
def show_command(namespace: str, vault: str, password: str) -> None:
    """Show all variables in NAMESPACE (without prefix)."""
    try:
        variables = get_namespace_vars(vault, password, namespace)
    except NamespaceError as exc:
        raise click.ClickException(str(exc))

    if not variables:
        click.echo(f"No variables found in namespace '{namespace}'.")
        return
    for key, value in sorted(variables.items()):
        click.echo(f"{key}={value}")


@namespace_group.command(name="move")
@click.argument("namespace")
@click.option("--key", "keys", multiple=True, help="Specific key(s) to move (repeatable).")
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing keys.")
@click.option("--vault", required=True, envvar="ENVAULT_PATH", help="Path to vault file.")
@click.password_option("--password", envvar="ENVAULT_PASSWORD", confirmation_prompt=False)
def move_command(
    namespace: str, keys: tuple, overwrite: bool, vault: str, password: str
) -> None:
    """Move variables into NAMESPACE."""
    try:
        moved = move_to_namespace(
            vault, password, namespace,
            keys=list(keys) if keys else None,
            overwrite=overwrite,
        )
    except NamespaceError as exc:
        raise click.ClickException(str(exc))

    for key in moved:
        click.echo(f"Moved -> {key}")
    click.echo(f"{len(moved)} variable(s) moved to namespace '{namespace}'.")


@namespace_group.command(name="delete")
@click.argument("namespace")
@click.option("--vault", required=True, envvar="ENVAULT_PATH", help="Path to vault file.")
@click.password_option("--password", envvar="ENVAULT_PASSWORD", confirmation_prompt=False)
def delete_command(namespace: str, vault: str, password: str) -> None:
    """Delete all variables in NAMESPACE."""
    try:
        count = delete_namespace(vault, password, namespace)
    except NamespaceError as exc:
        raise click.ClickException(str(exc))

    click.echo(f"Deleted {count} variable(s) from namespace '{namespace}'.")
