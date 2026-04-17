"""CLI commands for vault snapshots."""

import click

from envault.snapshot import SnapshotError, create_snapshot, delete_snapshot, list_snapshots, restore_snapshot


@click.group("snapshot")
def snapshot_group():
    """Manage vault snapshots."""


@snapshot_group.command("create")
@click.option("--vault", required=True, envvar="ENVAULT_PATH", help="Path to vault file.")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", hide_input=True, help="Vault password.")
@click.option("--name", default=None, help="Snapshot name (default: timestamp).")
def create_command(vault, password, name):
    """Create a snapshot of current variables."""
    try:
        snap_name = create_snapshot(vault, password, name)
        click.echo(f"Snapshot '{snap_name}' created.")
    except SnapshotError as e:
        raise click.ClickException(str(e))


@snapshot_group.command("list")
@click.option("--vault", required=True, envvar="ENVAULT_PATH")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", hide_input=True)
def list_command(vault, password):
    """List available snapshots."""
    try:
        names = list_snapshots(vault, password)
        if not names:
            click.echo("No snapshots found.")
        else:
            for n in names:
                click.echo(n)
    except SnapshotError as e:
        raise click.ClickException(str(e))


@snapshot_group.command("restore")
@click.argument("name")
@click.option("--vault", required=True, envvar="ENVAULT_PATH")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", hide_input=True)
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing variables.")
def restore_command(name, vault, password, overwrite):
    """Restore variables from a snapshot."""
    try:
        restored = restore_snapshot(vault, password, name, overwrite=overwrite)
        click.echo(f"Restored {len(restored)} variable(s) from snapshot '{name}'.")
    except SnapshotError as e:
        raise click.ClickException(str(e))


@snapshot_group.command("delete")
@click.argument("name")
@click.option("--vault", required=True, envvar="ENVAULT_PATH")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", hide_input=True)
def delete_command(name, vault, password):
    """Delete a snapshot."""
    try:
        delete_snapshot(vault, password, name)
        click.echo(f"Snapshot '{name}' deleted.")
    except SnapshotError as e:
        raise click.ClickException(str(e))
