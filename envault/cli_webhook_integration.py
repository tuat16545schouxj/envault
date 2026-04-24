"""Integration helpers: attach webhook auto-fire to vault-mutating CLI commands."""

from __future__ import annotations

import functools
from typing import Callable

import click

from envault.webhook import WebhookError, fire_event


def attach_webhook(cli_group: click.Group) -> None:
    """Register the webhook sub-group onto an existing Click group."""
    from envault.cli_webhook import webhook_group
    cli_group.add_command(webhook_group)


def auto_fire(
    event: str,
    vault_option: str = "vault",
    password_option: str = "password",
) -> Callable:
    """Decorator that fires *event* webhooks after a successful command invocation.

    Usage::

        @auto_fire("set")
        @click.command()
        @click.option("--vault", ...)
        @click.option("--password", ...)
        def set_command(vault, password, ...):
            ...
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            result = fn(*args, **kwargs)
            vault_path = kwargs.get(vault_option)
            password = kwargs.get(password_option)
            if vault_path and password:
                try:
                    fire_event(vault_path, password, event)
                except WebhookError:
                    # Webhook failures must not interrupt the main flow.
                    pass
            return result
        return wrapper
    return decorator


def webhook_summary(vault_path: str, password: str) -> str:
    """Return a one-line summary of registered webhooks for display in status output."""
    from envault.webhook import list_webhooks
    try:
        hooks = list_webhooks(vault_path, password)
    except Exception:
        return "webhooks: (unavailable)"
    if not hooks:
        return "webhooks: none"
    names = ", ".join(h["name"] for h in hooks)
    return f"webhooks: {len(hooks)} registered ({names})"
