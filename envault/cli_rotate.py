"""CLI command for rotating the vault encryption key."""

from __future__ import annotations

from pathlib import Path

import click

from envault.rotate import RotateError, rotate_key


@click.group()
def rotate_group() -> None:
    """Key rotation commands."""


@rotate_group.command("rotate")
@click.option(
    "--vault",
    "vault_path",
    default=".envault",
    show_default=True,
    help="Path to the vault file.",
)
@click.password_option(
    "--old-password",
    prompt="Current vault password",
    confirmation_prompt=False,
    help="Current encryption password.",
)
@click.password_option(
    "--new-password",
    prompt="New vault password",
    help="New encryption password (prompted twice for confirmation).",
)
def rotate_command(vault_path: str, old_password: str, new_password: str) -> None:
    """Re-encrypt the vault with a new password."""
    path = Path(vault_path)
    try:
        count = rotate_key(path, old_password, new_password)
    except RotateError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(
        click.style("\u2713", fg="green")
        + f" Key rotated successfully. {count} variable(s) re-encrypted."
    )
