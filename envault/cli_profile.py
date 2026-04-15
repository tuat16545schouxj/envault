"""CLI commands for managing envault profiles."""

from __future__ import annotations

from pathlib import Path

import click

from envault.profile import (
    ProfileError,
    delete_profile,
    get_profile_vars,
    list_profiles,
    save_profile,
)


@click.group("profile")
def profile_group() -> None:
    """Manage named profiles (snapshots of variable sets)."""


@profile_group.command("save")
@click.argument("name")
@click.option("--vault", default=".envault", show_default=True, help="Vault file path.")
@click.password_option("--password", prompt="Vault password", confirmation_prompt=False)
def save_command(name: str, vault: str, password: str) -> None:
    """Snapshot current vault variables into profile NAME."""
    try:
        save_profile(Path(vault), password, name)
        click.echo(f"Profile '{name}' saved.")
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc


@profile_group.command("list")
@click.option("--vault", default=".envault", show_default=True, help="Vault file path.")
@click.password_option("--password", prompt="Vault password", confirmation_prompt=False)
def list_command(vault: str, password: str) -> None:
    """List all saved profiles."""
    try:
        names = list_profiles(Path(vault), password)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    if not names:
        click.echo("No profiles found.")
    else:
        for name in names:
            click.echo(name)


@profile_group.command("show")
@click.argument("name")
@click.option("--vault", default=".envault", show_default=True, help="Vault file path.")
@click.password_option("--password", prompt="Vault password", confirmation_prompt=False)
def show_command(name: str, vault: str, password: str) -> None:
    """Show variables belonging to profile NAME."""
    try:
        variables = get_profile_vars(Path(vault), password, name)
    except ProfileError as exc:
        raise click.ClickException(str(exc)) from exc
    if not variables:
        click.echo(f"Profile '{name}' is empty or its variables were deleted.")
    else:
        for key, value in sorted(variables.items()):
            click.echo(f"{key}={value}")


@profile_group.command("delete")
@click.argument("name")
@click.option("--vault", default=".envault", show_default=True, help="Vault file path.")
@click.password_option("--password", prompt="Vault password", confirmation_prompt=False)
def delete_command(name: str, vault: str, password: str) -> None:
    """Delete profile NAME (variables are not removed from the vault)."""
    try:
        delete_profile(Path(vault), password, name)
        click.echo(f"Profile '{name}' deleted.")
    except ProfileError as exc:
        raise click.ClickException(str(exc)) from exc
