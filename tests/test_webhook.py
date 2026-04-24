"""Tests for envault.webhook."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from envault.vault import save_vault
from envault.webhook import (
    WebhookError,
    add_webhook,
    fire_event,
    list_webhooks,
    remove_webhook,
)


@pytest.fixture
def vault_file(tmp_path):
    path = str(tmp_path / "vault.enc")
    save_vault(path, "pw", {})
    return path


def test_add_webhook_success(vault_file):
    add_webhook(vault_file, "pw", "slack", "https://hooks.example.com/abc", ["set"])
    hooks = list_webhooks(vault_file, "pw")
    assert len(hooks) == 1
    assert hooks[0]["name"] == "slack"
    assert hooks[0]["url"] == "https://hooks.example.com/abc"
    assert hooks[0]["events"] == ["set"]


def test_add_webhook_invalid_url_raises(vault_file):
    with pytest.raises(WebhookError, match="Invalid URL"):
        add_webhook(vault_file, "pw", "bad", "ftp://not-valid", ["set"])


def test_add_webhook_no_events_raises(vault_file):
    with pytest.raises(WebhookError, match="At least one event"):
        add_webhook(vault_file, "pw", "empty", "https://example.com", [])


def test_add_webhook_deduplicates_events(vault_file):
    add_webhook(vault_file, "pw", "hook", "https://example.com", ["set", "set", "delete"])
    hooks = list_webhooks(vault_file, "pw")
    assert hooks[0]["events"] == ["delete", "set"]


def test_remove_webhook_success(vault_file):
    add_webhook(vault_file, "pw", "hook", "https://example.com", ["set"])
    remove_webhook(vault_file, "pw", "hook")
    assert list_webhooks(vault_file, "pw") == []


def test_remove_webhook_missing_raises(vault_file):
    with pytest.raises(WebhookError, match="not found"):
        remove_webhook(vault_file, "pw", "nonexistent")


def test_list_webhooks_sorted(vault_file):
    add_webhook(vault_file, "pw", "z_hook", "https://z.example.com", ["set"])
    add_webhook(vault_file, "pw", "a_hook", "https://a.example.com", ["delete"])
    names = [h["name"] for h in list_webhooks(vault_file, "pw")]
    assert names == ["a_hook", "z_hook"]


def test_fire_event_posts_to_matching_hooks(vault_file):
    add_webhook(vault_file, "pw", "hook", "https://example.com/notify", ["set"])
    mock_resp = MagicMock(ok=True, status_code=200)
    with patch("envault.webhook.requests.post", return_value=mock_resp) as mock_post:
        results = fire_event(vault_file, "pw", "set", {"key": "FOO"})
    assert len(results) == 1
    assert results[0]["ok"] is True
    assert results[0]["status"] == 200
    mock_post.assert_called_once()
    _, kwargs = mock_post.call_args
    assert kwargs["json"]["event"] == "set"


def test_fire_event_skips_non_matching_hooks(vault_file):
    add_webhook(vault_file, "pw", "hook", "https://example.com/notify", ["delete"])
    with patch("envault.webhook.requests.post") as mock_post:
        results = fire_event(vault_file, "pw", "set")
    assert results == []
    mock_post.assert_not_called()


def test_fire_event_handles_request_exception(vault_file):
    import requests as req_lib
    add_webhook(vault_file, "pw", "hook", "https://example.com/notify", ["set"])
    with patch("envault.webhook.requests.post", side_effect=req_lib.ConnectionError("timeout")):
        results = fire_event(vault_file, "pw", "set")
    assert results[0]["ok"] is False
    assert "timeout" in results[0]["error"]
