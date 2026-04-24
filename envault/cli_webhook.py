"""CLI commands for managing vault webhooks."""

from __future__ import annotations

import click

from envault.webhook import (
    WebhookError,
    add_webhook,
    fire_event,
    list_webhooks,
    remove_webhook,
)


@click.group(name="webhook")
def webhook_group() -> None:
    """Manage webhook notifications for vault events."""


@webhook_group.command(name="add")
@click.option("--vault", required=True, envvar="ENVAULT_PATH", help="Path to vault file.")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", hide_input=True)
@click.argument("name")
@click.argument("url")
@click.option(
    "--event",
    "events",
    multiple=True,
    default=("set", "delete"),
    show_default=True,
    help="Events to subscribe to (repeatable).",
)
def add_command(vault: str, password: str, name: str, url: str, events: tuple) -> None:
    """Register a webhook NAME pointing at URL."""
    try:
        add_webhook(vault, password, name, url, list(events))
        click.echo(f"Webhook '{name}' registered for events: {', '.join(sorted(events))}.")
    except WebhookError as exc:
        raise click.ClickException(str(exc)) from exc


@webhook_group.command(name="remove")
@click.option("--vault", required=True, envvar="ENVAULT_PATH")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", hide_input=True)
@click.argument("name")
def remove_command(vault: str, password: str, name: str) -> None:
    """Remove a registered webhook by NAME."""
    try:
        remove_webhook(vault, password, name)
        click.echo(f"Webhook '{name}' removed.")
    except WebhookError as exc:
        raise click.ClickException(str(exc)) from exc


@webhook_group.command(name="list")
@click.option("--vault", required=True, envvar="ENVAULT_PATH")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", hide_input=True)
def list_command(vault: str, password: str) -> None:
    """List all registered webhooks."""
    hooks = list_webhooks(vault, password)
    if not hooks:
        click.echo("No webhooks registered.")
        return
    for hook in hooks:
        events_str = ", ".join(hook["events"])
        click.echo(f"{hook['name']:20s}  {hook['url']}  [{events_str}]")


@webhook_group.command(name="fire")
@click.option("--vault", required=True, envvar="ENVAULT_PATH")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", hide_input=True)
@click.argument("event")
def fire_command(vault: str, password: str, event: str) -> None:
    """Manually fire EVENT to all subscribed webhooks."""
    results = fire_event(vault, password, event)
    if not results:
        click.echo("No webhooks matched that event.")
        return
    for r in results:
        status = r.get("status", "ERR")
        ok = "OK" if r["ok"] else "FAIL"
        click.echo(f"  {r['name']:20s}  {ok}  (HTTP {status})")
