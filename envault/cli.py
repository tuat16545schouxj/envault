"""CLI entry-point for envault."""

from __future__ import annotations

import sys

import click

from envault.vault import VaultError, delete_var, get_var, list_vars, set_var
from envault.export import ExportError, export_variables, SUPPORTED_FORMATS


@click.group()
def cli() -> None:
    """envault — secure environment variable manager."""


@cli.command("set")
@click.argument("key")
@click.argument("value")
@click.option("--vault", default=".envault", show_default=True, help="Vault file path.")
@click.password_option("--password", prompt="Vault password", help="Vault password.")
def set_command(key: str, value: str, vault: str, password: str) -> None:
    """Set KEY to VALUE in the vault."""
    try:
        set_var(vault, password, key, value)
        click.echo(f"✓ Set {key}")
    except VaultError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@cli.command("delete")
@click.argument("key")
@click.option("--vault", default=".envault", show_default=True, help="Vault file path.")
@click.password_option("--password", prompt="Vault password", help="Vault password.")
def delete_command(key: str, vault: str, password: str) -> None:
    """Delete KEY from the vault."""
    try:
        delete_var(vault, password, key)
        click.echo(f"✓ Deleted {key}")
    except VaultError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@cli.command("list")
@click.option("--vault", default=".envault", show_default=True, help="Vault file path.")
@click.option("--show-values", is_flag=True, default=False, help="Reveal values.")
@click.password_option("--password", prompt="Vault password", help="Vault password.")
def list_command(vault: str, show_values: bool, password: str) -> None:
    """List variables stored in the vault."""
    try:
        variables = list_vars(vault, password)
    except VaultError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if not variables:
        click.echo("(empty vault)")
        return

    for key in sorted(variables):
        display = variables[key] if show_values else "***"
        click.echo(f"{key}={display}")


@cli.command("export")
@click.option("--vault", default=".envault", show_default=True, help="Vault file path.")
@click.option(
    "--format", "fmt",
    default="dotenv",
    show_default=True,
    type=click.Choice(SUPPORTED_FORMATS),
    help="Output format.",
)
@click.option("--output", "-o", default=None, help="Write to file instead of stdout.")
@click.password_option("--password", prompt="Vault password", help="Vault password.")
def export_command(vault: str, fmt: str, output: str | None, password: str) -> None:
    """Export vault variables to dotenv, shell, or JSON format."""
    try:
        variables = list_vars(vault, password)
        rendered = export_variables(variables, fmt)
    except (VaultError, ExportError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if output:
        with open(output, "w", encoding="utf-8") as fh:
            fh.write(rendered)
        click.echo(f"✓ Exported {len(variables)} variable(s) to {output}")
    else:
        click.echo(rendered, nl=False)
