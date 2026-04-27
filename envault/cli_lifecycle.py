"""CLI commands for managing lifecycle hooks on vault keys."""

import click

from envault.lifecycle import LifecycleError, set_hook, remove_hook, list_hooks


@click.group(name="lifecycle")
def lifecycle_group() -> None:
    """Manage lifecycle hooks (on_create / on_update / on_delete) for keys."""


@lifecycle_group.command(name="set")
@click.argument("key")
@click.argument("event")
@click.argument("command")
@click.option("--vault", "vault_path", required=True, envvar="ENVAULT_VAULT")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", hide_input=True)
def set_command(key: str, event: str, command: str, vault_path: str, password: str) -> None:
    """Register COMMAND to run on EVENT for KEY."""
    try:
        set_hook(vault_path, password, key, event, command)
        click.echo(f"Hook '{event}' set for key '{key}'.")
    except LifecycleError as exc:
        raise click.ClickException(str(exc)) from exc


@lifecycle_group.command(name="remove")
@click.argument("key")
@click.argument("event")
@click.option("--vault", "vault_path", required=True, envvar="ENVAULT_VAULT")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", hide_input=True)
def remove_command(key: str, event: str, vault_path: str, password: str) -> None:
    """Remove the EVENT hook for KEY."""
    try:
        remove_hook(vault_path, password, key, event)
        click.echo(f"Hook '{event}' removed from key '{key}'.")
    except LifecycleError as exc:
        raise click.ClickException(str(exc)) from exc


@lifecycle_group.command(name="list")
@click.option("--key", default=None, help="Filter by key name.")
@click.option("--vault", "vault_path", required=True, envvar="ENVAULT_VAULT")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", hide_input=True)
def list_command(key: str | None, vault_path: str, password: str) -> None:
    """List all registered lifecycle hooks."""
    try:
        hooks = list_hooks(vault_path, password, key)
    except LifecycleError as exc:
        raise click.ClickException(str(exc)) from exc

    if not any(hooks.values() if key is None else [hooks.get(key or "", {})]):
        click.echo("No lifecycle hooks registered.")
        return

    for k, events in sorted(hooks.items()):
        for event, command in sorted(events.items()):
            click.echo(f"{k}  {event}  {command}")
