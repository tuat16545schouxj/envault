"""Notification hooks for envault — send alerts when vault keys change."""

from __future__ import annotations

import json
import smtplib
from dataclasses import dataclass, field
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from envault.vault import load_vault, save_vault

NOTIFY_KEY = "__notify__"


class NotifyError(Exception):
    """Raised when a notification operation fails."""


@dataclass
class NotifyChannel:
    kind: str  # "email" | "slack"
    target: str  # email address or Slack webhook URL
    events: list[str] = field(default_factory=list)  # e.g. ["set", "delete"]

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "target": self.target, "events": self.events}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "NotifyChannel":
        return cls(kind=d["kind"], target=d["target"], events=d.get("events", []))


def _channels(vault_path: Path, password: str) -> list[NotifyChannel]:
    data = load_vault(vault_path, password)
    raw = data.get(NOTIFY_KEY, "[]")
    return [NotifyChannel.from_dict(c) for c in json.loads(raw)]


def _save_channels(vault_path: Path, password: str, channels: list[NotifyChannel]) -> None:
    data = load_vault(vault_path, password)
    data[NOTIFY_KEY] = json.dumps([c.to_dict() for c in channels])
    save_vault(vault_path, password, data)


def add_channel(vault_path: Path, password: str, kind: str, target: str, events: list[str]) -> NotifyChannel:
    if kind not in ("email", "slack"):
        raise NotifyError(f"Unsupported channel kind: {kind!r}. Use 'email' or 'slack'.")
    if not events:
        raise NotifyError("At least one event must be specified.")
    valid_events = {"set", "delete", "rotate", "import"}
    bad = set(events) - valid_events
    if bad:
        raise NotifyError(f"Unknown events: {bad}. Valid: {valid_events}")
    channels = _channels(vault_path, password)
    channel = NotifyChannel(kind=kind, target=target, events=sorted(set(events)))
    channels.append(channel)
    _save_channels(vault_path, password, channels)
    return channel


def remove_channel(vault_path: Path, password: str, target: str) -> None:
    channels = _channels(vault_path, password)
    updated = [c for c in channels if c.target != target]
    if len(updated) == len(channels):
        raise NotifyError(f"No channel found for target: {target!r}")
    _save_channels(vault_path, password, updated)


def list_channels(vault_path: Path, password: str) -> list[NotifyChannel]:
    return sorted(_channels(vault_path, password), key=lambda c: c.target)


def fire_notification(channel: NotifyChannel, event: str, message: str) -> None:
    """Dispatch a notification; raises NotifyError on failure."""
    if event not in channel.events:
        return
    if channel.kind == "slack":
        _fire_slack(channel.target, event, message)
    elif channel.kind == "email":
        _fire_email(channel.target, event, message)


def _fire_slack(url: str, event: str, message: str) -> None:
    import urllib.request
    payload = json.dumps({"text": f"[envault:{event}] {message}"}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=5)
    except Exception as exc:
        raise NotifyError(f"Slack notification failed: {exc}") from exc


def _fire_email(address: str, event: str, message: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = f"[envault] {event} event"
    msg["From"] = "envault@localhost"
    msg["To"] = address
    msg.set_content(message)
    try:
        with smtplib.SMTP("localhost") as smtp:
            smtp.send_message(msg)
    except Exception as exc:
        raise NotifyError(f"Email notification failed: {exc}") from exc
