"""CLI commands for promoting variables between vaults."""

from __future__ import annotations

import click

from envault.promote import PromoteError, promote_vars


@click.group("promote")
def promote_group() -> None:
    """Promote variables from one vault to another."""


@promote_group.command("run")
@click.argument("src_vault", type=click.Path())
@click.argument("dst_vault", type=click.Path())
@click.option("--src-password", envvar="ENVAULT_SRC_PASSWORD", prompt=True, hide_input=True)
@click.option("--dst-password", envvar="ENVAULT_DST_PASSWORD", prompt=True, hide_input=True)
@click.option("-k", "--key", "keys", multiple=True, help="Key(s) to promote (default: all).")
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing keys in destination.")
@click.option("--dry-run", is_flag=True, default=False, help="Preview changes without writing.")
def run_command(
    src_vault: str,
    dst_vault: str,
    src_password: str,
    dst_password: str,
    keys: tuple[str, ...],
    overwrite: bool,
    dry_run: bool,
) -> None:
    """Promote variables from SRC_VAULT to DST_VAULT."""
    try:
        promoted = promote_vars(
            src_vault_path=src_vault,
            src_password=src_password,
            dst_vault_path=dst_vault,
            dst_password=dst_password,
            keys=list(keys) if keys else None,
            overwrite=overwrite,
            dry_run=dry_run,
        )
    except PromoteError as exc:
        raise click.ClickException(str(exc)) from exc

    prefix = "[dry-run] " if dry_run else ""
    if not promoted:
        click.echo("No variables to promote.")
        return

    for key in sorted(promoted):
        click.echo(f"{prefix}Promoted: {key}")

    click.echo(f"{prefix}{len(promoted)} variable(s) promoted from '{src_vault}' to '{dst_vault}'.")
