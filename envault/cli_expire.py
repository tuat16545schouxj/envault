"""cli_expire.py — CLI commands for expiration management."""

from __future__ import annotations

import click

from envault.expire import expiration_report, extend_ttl_bulk, purge_and_report, ExpireError


@click.group("expire")
def expire_group() -> None:
    """Manage variable expiration (TTL) in bulk."""


@expire_group.command("report")
@click.option("--vault", required=True, envvar="ENVAULT_VAULT", help="Path to vault file.")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", prompt=True, hide_input=True)
@click.option("--key", "keys", multiple=True, help="Limit report to specific keys.")
@click.option("--expired-only", is_flag=True, default=False, help="Show only expired entries.")
def report_command(vault: str, password: str, keys: tuple, expired_only: bool) -> None:
    """Show expiration status for vault variables."""
    try:
        statuses = expiration_report(
            vault_path=vault, password=password, keys=list(keys) if keys else None
        )
    except ExpireError as exc:
        raise click.ClickException(str(exc))

    if expired_only:
        statuses = [s for s in statuses if s.is_expired]

    if not statuses:
        click.echo("No matching variables found.")
        return

    for s in statuses:
        if s.expires_at is None:
            click.echo(f"  {s.key}: no TTL set")
        elif s.is_expired:
            click.echo(f"  {s.key}: EXPIRED")
        else:
            click.echo(f"  {s.key}: expires in {s.seconds_remaining:.0f}s")


@expire_group.command("extend")
@click.option("--vault", required=True, envvar="ENVAULT_VAULT", help="Path to vault file.")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", prompt=True, hide_input=True)
@click.option("--seconds", required=True, type=int, help="Seconds to add to existing TTLs.")
@click.option("--key", "keys", multiple=True, help="Limit to specific keys.")
def extend_command(vault: str, password: str, seconds: int, keys: tuple) -> None:
    """Extend TTLs of variables that already have a TTL set."""
    try:
        extended = extend_ttl_bulk(
            vault_path=vault, password=password, extra_seconds=seconds,
            keys=list(keys) if keys else None,
        )
    except ExpireError as exc:
        raise click.ClickException(str(exc))

    if extended:
        click.echo(f"Extended TTL for: {', '.join(extended)}")
    else:
        click.echo("No variables with an existing TTL were found.")


@expire_group.command("purge")
@click.option("--vault", required=True, envvar="ENVAULT_VAULT", help="Path to vault file.")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", prompt=True, hide_input=True)
@click.confirmation_option(prompt="Remove all expired variables?")
def purge_command(vault: str, password: str) -> None:
    """Remove all expired variables from the vault."""
    try:
        removed = purge_and_report(vault_path=vault, password=password)
    except ExpireError as exc:
        raise click.ClickException(str(exc))

    if removed:
        click.echo(f"Purged {len(removed)} expired variable(s): {', '.join(removed)}")
    else:
        click.echo("No expired variables found.")
