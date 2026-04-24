"""CLI commands for managing vault variable quotas."""

from __future__ import annotations

from pathlib import Path

import click

from envault.quota import QuotaError, check_quota, get_quota, remove_quota, set_quota


@click.group("quota")
def quota_group() -> None:
    """Manage variable quota limits for a vault."""


@quota_group.command("set")
@click.option("--vault", required=True, type=click.Path(), help="Path to vault file.")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", help="Vault password.")
@click.argument("limit", type=int)
def set_command(vault: str, password: str, limit: int) -> None:
    """Set the maximum number of variables allowed in the vault."""
    try:
        set_quota(Path(vault), password, limit)
        click.echo(f"Quota set to {limit} variables.")
    except QuotaError as exc:
        raise click.ClickException(str(exc)) from exc


@quota_group.command("remove")
@click.option("--vault", required=True, type=click.Path(), help="Path to vault file.")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", help="Vault password.")
def remove_command(vault: str, password: str) -> None:
    """Remove the quota limit from the vault."""
    remove_quota(Path(vault), password)
    click.echo("Quota removed.")


@quota_group.command("show")
@click.option("--vault", required=True, type=click.Path(), help="Path to vault file.")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", help="Vault password.")
def show_command(vault: str, password: str) -> None:
    """Show current quota usage for the vault."""
    status = check_quota(Path(vault), password)
    if status["limit"] is None:
        click.echo(f"No quota set. Variables in use: {status['used']}")
    else:
        indicator = " [EXCEEDED]" if status["exceeded"] else ""
        click.echo(
            f"Quota: {status['used']}/{status['limit']} used, "
            f"{status['remaining']} remaining{indicator}"
        )
