"""Main CLI entry point for envault."""
from __future__ import annotations

import click

from envault.vault import VaultError, set_var, delete_var, load_vault
from envault.export import export_variables, ExportError
from envault.cli_audit import audit_group
from envault.cli_rotate import rotate_group
from envault.cli_profile import profile_group
from envault.cli_tag import tag_group
from envault.cli_snapshot import snapshot_group
from envault.cli_template import template_group


@click.group()
def cli() -> None:
    """envault — secure environment variable manager."""


@cli.command("set")
@click.argument("key")
@click.argument("value")
@click.option("--vault", "vault_path", required=True, type=click.Path(), help="Vault file path.")
@click.option("--password", prompt=True, hide_input=True)
def set_command(key: str, value: str, vault_path: str, password: str) -> None:
    """Set a variable in the vault."""
    from pathlib import Path
    try:
        set_var(Path(vault_path), password, key, value)
        click.echo(f"Set {key}")
    except VaultError as exc:
        raise click.ClickException(str(exc))


@cli.command("delete")
@click.argument("key")
@click.option("--vault", "vault_path", required=True, type=click.Path())
@click.option("--password", prompt=True, hide_input=True)
def delete_command(key: str, vault_path: str, password: str) -> None:
    """Delete a variable from the vault."""
    from pathlib import Path
    try:
        delete_var(Path(vault_path), password, key)
        click.echo(f"Deleted {key}")
    except VaultError as exc:
        raise click.ClickException(str(exc))


@cli.command("list")
@click.option("--vault", "vault_path", required=True, type=click.Path())
@click.option("--password", prompt=True, hide_input=True)
@click.option("--show-values", is_flag=True, default=False)
def list_command(vault_path: str, password: str, show_values: bool) -> None:
    """List variables in the vault."""
    from pathlib import Path
    try:
        variables = load_vault(Path(vault_path), password)
    except VaultError as exc:
        raise click.ClickException(str(exc))
    for key in sorted(variables):
        if show_values:
            click.echo(f"{key}={variables[key]}")
        else:
            click.echo(key)


@cli.command("export")
@click.option("--vault", "vault_path", required=True, type=click.Path())
@click.option("--password", prompt=True, hide_input=True)
@click.option("--format", "fmt", default="dotenv", type=click.Choice(["dotenv", "shell", "json"]))
def export_command(vault_path: str, password: str, fmt: str) -> None:
    """Export vault variables."""
    from pathlib import Path
    try:
        output = export_variables(Path(vault_path), password, fmt)
        click.echo(output)
    except (VaultError, ExportError) as exc:
        raise click.ClickException(str(exc))


cli.add_command(audit_group, "audit")
cli.add_command(rotate_group, "rotate")
cli.add_command(profile_group, "profile")
cli.add_command(tag_group, "tag")
cli.add_command(snapshot_group, "snapshot")
cli.add_command(template_group, "template")
