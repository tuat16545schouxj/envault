"""CLI commands for merging vaults."""

from __future__ import annotations

import click

from envault.merge import ConflictStrategy, MergeError, merge_vaults


@click.group(name="merge")
def merge_group() -> None:
    """Merge variables from one vault into another."""


@merge_group.command(name="run")
@click.argument("src")
@click.argument("dst")
@click.option("--src-password", envvar="ENVAULT_SRC_PASSWORD", prompt="Source vault password", hide_input=True)
@click.option("--dst-password", envvar="ENVAULT_DST_PASSWORD", prompt="Destination vault password", hide_input=True)
@click.option(
    "--strategy",
    type=click.Choice([s.value for s in ConflictStrategy], case_sensitive=False),
    default=ConflictStrategy.KEEP_DST.value,
    show_default=True,
    help="Conflict resolution strategy.",
)
@click.option(
    "--key",
    "keys",
    multiple=True,
    metavar="KEY",
    help="Specific key(s) to merge (repeatable). Merges all if omitted.",
)
def run_command(
    src: str,
    dst: str,
    src_password: str,
    dst_password: str,
    strategy: str,
    keys: tuple,
) -> None:
    """Merge variables from SRC vault into DST vault."""
    try:
        result = merge_vaults(
            src_path=src,
            src_password=src_password,
            dst_path=dst,
            dst_password=dst_password,
            keys=list(keys) if keys else None,
            strategy=ConflictStrategy(strategy),
        )
    except MergeError as exc:
        raise click.ClickException(str(exc)) from exc

    if result.added:
        click.echo(f"Added    ({len(result.added)}): {', '.join(result.added)}")
    if result.overwritten:
        click.echo(f"Updated  ({len(result.overwritten)}): {', '.join(result.overwritten)}")
    if result.skipped:
        click.echo(f"Skipped  ({len(result.skipped)}): {', '.join(result.skipped)}")

    total = len(result.added) + len(result.overwritten)
    click.echo(f"Merge complete. {total} key(s) written to '{dst}'.")
