"""Main CLI entry point for envault."""

from __future__ import annotations

from pathlib import Path

import click

from envault.vault import VaultError, delete_var, list_vars, load_vault, save_vault, set_var
from envault.export import ExportError, export_variables
from envault.cli_audit import audit_group
from envault.cli_rotate import rotate_group
from envault.cli_profile import profile_group


@click.group()
def cli() -> None:
    """envault — secure environment variable manager."""


@cli.command("set")
@click.argument("key")
@click.argument("value")
@click.option("--vault", default=".envault", show_default=True, help="Vault file path.")
@click.password_option("--password", prompt="Vault password", confirmation_prompt=False)
def set_command(key: str, value: str, vault: str, password: str) -> None:
    """Set KEY to VALUE in the vault."""
    try:
        set_var(Path(vault), password, key, value)
        click.echo(f"Set {key}.")
    except VaultError as exc:
        raise click.ClickException(str(exc)) from exc


@cli.command("delete")
@click.argument("key")
@click.option("--vault", default=".envault", show_default=True, help="Vault file path.")
@click.password_option("--password", prompt="Vault password", confirmation_prompt=False)
def delete_command(key: str, vault: str, password: str) -> None:
    """Delete KEY from the vault."""
    try:
        delete_var(Path(vault), password, key)
        click.echo(f"Deleted {key}.")
    except VaultError as exc:
        raise click.ClickException(str(exc)) from exc


@cli.command("list")
@click.option("--vault", default=".envault", show_default=True, help="Vault file path.")
@click.option("--show-values", is_flag=True, default=False, help="Reveal values.")
@click.password_option("--password", prompt="Vault password", confirmation_prompt=False)
def list_command(vault: str, show_values: bool, password: str) -> None:
    """List variables stored in the vault."""
    try:
        variables = list_vars(Path(vault), password)
    except VaultError as exc:
        raise click.ClickException(str(exc)) from exc
    if not variables:
        click.echo("No variables found.")
        return
    for key, value in sorted(variables.items()):
        if show_values:
            click.echo(f"{key}={value}")
        else:
            click.echo(key)


@cli.command("export")
@click.option("--vault", default=".envault", show_default=True, help="Vault file path.")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["dotenv", "shell", "json"], case_sensitive=False),
    default="dotenv",
    show_default=True,
)
@click.password_option("--password", prompt="Vault password", confirmation_prompt=False)
def export_command(vault: str, fmt: str, password: str) -> None:
    """Export variables in the chosen format."""
    try:
        variables = list_vars(Path(vault), password)
        output = export_variables(variables, fmt)
        click.echo(output)
    except (VaultError, ExportError) as exc:
        raise click.ClickException(str(exc)) from exc


cli.add_command(audit_group)
cli.add_command(rotate_group)
cli.add_command(profile_group)
