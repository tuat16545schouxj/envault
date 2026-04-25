"""Tests for envault.notify."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envault.notify import (
    NotifyError,
    NotifyChannel,
    add_channel,
    fire_notification,
    list_channels,
    remove_channel,
    NOTIFY_KEY,
)
from envault.vault import load_vault, save_vault


PASSWORD = "testpass"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    path = tmp_path / "vault.enc"
    save_vault(path, PASSWORD, {})
    return path


def test_add_channel_success(vault_file: Path) -> None:
    ch = add_channel(vault_file, PASSWORD, "slack", "https://hooks.slack.com/x", ["set", "delete"])
    assert ch.kind == "slack"
    assert ch.target == "https://hooks.slack.com/x"
    assert set(ch.events) == {"set", "delete"}


def test_add_channel_persisted(vault_file: Path) -> None:
    add_channel(vault_file, PASSWORD, "email", "dev@example.com", ["rotate"])
    channels = list_channels(vault_file, PASSWORD)
    assert len(channels) == 1
    assert channels[0].target == "dev@example.com"


def test_add_channel_invalid_kind_raises(vault_file: Path) -> None:
    with pytest.raises(NotifyError, match="Unsupported channel kind"):
        add_channel(vault_file, PASSWORD, "sms", "+1234", ["set"])


def test_add_channel_no_events_raises(vault_file: Path) -> None:
    with pytest.raises(NotifyError, match="At least one event"):
        add_channel(vault_file, PASSWORD, "slack", "https://hooks.slack.com/x", [])


def test_add_channel_unknown_event_raises(vault_file: Path) -> None:
    with pytest.raises(NotifyError, match="Unknown events"):
        add_channel(vault_file, PASSWORD, "slack", "https://hooks.slack.com/x", ["explode"])


def test_list_channels_empty(vault_file: Path) -> None:
    assert list_channels(vault_file, PASSWORD) == []


def test_list_channels_sorted(vault_file: Path) -> None:
    add_channel(vault_file, PASSWORD, "email", "z@example.com", ["set"])
    add_channel(vault_file, PASSWORD, "email", "a@example.com", ["set"])
    targets = [c.target for c in list_channels(vault_file, PASSWORD)]
    assert targets == sorted(targets)


def test_remove_channel_success(vault_file: Path) -> None:
    add_channel(vault_file, PASSWORD, "slack", "https://hooks.slack.com/x", ["set"])
    remove_channel(vault_file, PASSWORD, "https://hooks.slack.com/x")
    assert list_channels(vault_file, PASSWORD) == []


def test_remove_channel_missing_raises(vault_file: Path) -> None:
    with pytest.raises(NotifyError, match="No channel found"):
        remove_channel(vault_file, PASSWORD, "ghost@example.com")


def test_fire_notification_skips_if_event_not_subscribed() -> None:
    ch = NotifyChannel(kind="slack", target="https://hooks.slack.com/x", events=["delete"])
    # Should not raise even though "set" is not in events
    fire_notification(ch, "set", "KEY was set")


def test_fire_slack_notification_calls_urlopen() -> None:
    ch = NotifyChannel(kind="slack", target="https://hooks.slack.com/x", events=["set"])
    mock_response = MagicMock()
    with patch("urllib.request.urlopen", return_value=mock_response) as mock_open:
        fire_notification(ch, "set", "MY_KEY was updated")
        mock_open.assert_called_once()


def test_fire_slack_raises_notify_error_on_failure() -> None:
    ch = NotifyChannel(kind="slack", target="https://hooks.slack.com/x", events=["set"])
    with patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
        with pytest.raises(NotifyError, match="Slack notification failed"):
            fire_notification(ch, "set", "msg")
