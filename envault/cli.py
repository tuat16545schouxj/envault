"""CLI entry point for envault using Click."""

import sys
import click
from envault.vault import VaultError, set_var, delete_var, list_vars

DEFAULT_VAULT = ".envault"


@click.group()
@click.version_option("0.1.0", prog_name="envault")
def cli():
    """envault — securely manage and sync environment variables."""


@cli.command("set")
@click.argument("key")
@click.argument("value")
@click.option("--vault", default=DEFAULT_VAULT, show_default=True, help="Path to vault file.")
@click.password_option("--password", envvar="ENVAULT_PASSWORD", help="Vault password.")
def set_command(key, value, vault, password):
    """Set a KEY=VALUE pair in the vault."""
    try:
        set_var(vault, password, key, value)
        click.echo(f"✔ Set '{key}' in {vault}")
    except VaultError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@cli.command("delete")
@click.argument("key")
@click.option("--vault", default=DEFAULT_VAULT, show_default=True, help="Path to vault file.")
@click.password_option("--password", envvar="ENVAULT_PASSWORD", help="Vault password.")
def delete_command(key, vault, password):
    """Delete a KEY from the vault."""
    try:
        delete_var(vault, password, key)
        click.echo(f"✔ Deleted '{key}' from {vault}")
    except VaultError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@cli.command("list")
@click.option("--vault", default=DEFAULT_VAULT, show_default=True, help="Path to vault file.")
@click.option("--password", envvar="ENVAULT_PASSWORD", prompt=True, hide_input=True, help="Vault password.")
@click.option("--show-values", is_flag=True, default=False, help="Print variable values (sensitive).")
def list_command(vault, password, show_values):
    """List all keys (and optionally values) stored in the vault."""
    try:
        variables = list_vars(vault, password)
    except VaultError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if not variables:
        click.echo("Vault is empty.")
        return

    for key, value in sorted(variables.items()):
        if show_values:
            click.echo(f"{key}={value}")
        else:
            click.echo(key)


if __name__ == "__main__":
    cli()
