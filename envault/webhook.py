"""Webhook notification support for envault vault events."""

from __future__ import annotations

import json
import time
from typing import Any

import requests

from envault.vault import VaultError, load_vault, save_vault

WEBHOOK_KEY = "__webhooks__"


class WebhookError(Exception):
    """Raised when a webhook operation fails."""


def _webhooks(vault: dict) -> dict:
    return vault.get(WEBHOOK_KEY, {})


def add_webhook(vault_path: str, password: str, name: str, url: str, events: list[str]) -> None:
    """Register a webhook endpoint for the given events."""
    if not url.startswith(("http://", "https://")):
        raise WebhookError(f"Invalid URL: {url!r}")
    if not events:
        raise WebhookError("At least one event must be specified.")
    vault = load_vault(vault_path, password)
    hooks = _webhooks(vault)
    hooks[name] = {"url": url, "events": sorted(set(events))}
    vault[WEBHOOK_KEY] = hooks
    save_vault(vault_path, password, vault)


def remove_webhook(vault_path: str, password: str, name: str) -> None:
    """Remove a registered webhook by name."""
    vault = load_vault(vault_path, password)
    hooks = _webhooks(vault)
    if name not in hooks:
        raise WebhookError(f"Webhook {name!r} not found.")
    del hooks[name]
    vault[WEBHOOK_KEY] = hooks
    save_vault(vault_path, password, vault)


def list_webhooks(vault_path: str, password: str) -> list[dict]:
    """Return all registered webhooks sorted by name."""
    vault = load_vault(vault_path, password)
    hooks = _webhooks(vault)
    return [
        {"name": name, **data}
        for name, data in sorted(hooks.items())
    ]


def fire_event(
    vault_path: str,
    password: str,
    event: str,
    payload: dict[str, Any] | None = None,
    timeout: int = 5,
) -> list[dict]:
    """POST to all webhooks subscribed to *event*. Returns a list of results."""
    vault = load_vault(vault_path, password)
    hooks = _webhooks(vault)
    body = {"event": event, "timestamp": time.time(), "payload": payload or {}}
    results = []
    for name, data in hooks.items():
        if event not in data.get("events", []):
            continue
        try:
            resp = requests.post(data["url"], json=body, timeout=timeout)
            results.append({"name": name, "status": resp.status_code, "ok": resp.ok})
        except requests.RequestException as exc:
            results.append({"name": name, "status": None, "ok": False, "error": str(exc)})
    return results
