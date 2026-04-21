"""Tests for envault.env_push."""

from __future__ import annotations

import os
import pytest

from envault.env_push import EnvPushError, push_from_env
from envault.vault import load_vault, save_vault


@pytest.fixture()
def vault_file(tmp_path):
    return str(tmp_path / "test.vault")


PASSWORD = "test-password"


def test_push_specific_keys(vault_file, monkeypatch):
    monkeypatch.setenv("MY_API_KEY", "abc123")
    monkeypatch.setenv("MY_SECRET", "s3cr3t")

    written = push_from_env(vault_file, PASSWORD, keys=["MY_API_KEY", "MY_SECRET"])

    assert written == {"MY_API_KEY": "abc123", "MY_SECRET": "s3cr3t"}
    vault = load_vault(vault_file, PASSWORD)
    assert vault["MY_API_KEY"] == "abc123"
    assert vault["MY_SECRET"] == "s3cr3t"


def test_push_by_prefix(vault_file, monkeypatch):
    monkeypatch.setenv("APP_HOST", "localhost")
    monkeypatch.setenv("APP_PORT", "8080")
    monkeypatch.setenv("OTHER_VAR", "ignored")

    written = push_from_env(vault_file, PASSWORD, prefix="APP_")

    assert "APP_HOST" in written
    assert "APP_PORT" in written
    assert "OTHER_VAR" not in written


def test_push_no_keys_no_prefix_raises(vault_file):
    with pytest.raises(EnvPushError, match="Either 'keys' or 'prefix'"):
        push_from_env(vault_file, PASSWORD)


def test_push_missing_key_raises(vault_file):
    with pytest.raises(EnvPushError, match="not found in the environment"):
        push_from_env(vault_file, PASSWORD, keys=["DEFINITELY_NOT_SET_XYZ"])


def test_push_no_prefix_matches_raises(vault_file, monkeypatch):
    # Make sure no vars with this prefix exist
    for key in list(os.environ.keys()):
        if key.startswith("ZZZNOTAPREFIX_"):
            monkeypatch.delenv(key)

    with pytest.raises(EnvPushError, match="No matching environment variables found"):
        push_from_env(vault_file, PASSWORD, prefix="ZZZNOTAPREFIX_")


def test_push_no_overwrite_skips_existing(vault_file, monkeypatch):
    monkeypatch.setenv("KEEP_ME", "new_value")
    save_vault(vault_file, PASSWORD, {"KEEP_ME": "original"})

    written = push_from_env(vault_file, PASSWORD, keys=["KEEP_ME"], overwrite=False)

    assert written == {}
    vault = load_vault(vault_file, PASSWORD)
    assert vault["KEEP_ME"] == "original"


def test_push_overwrite_replaces_existing(vault_file, monkeypatch):
    monkeypatch.setenv("REPLACE_ME", "updated")
    save_vault(vault_file, PASSWORD, {"REPLACE_ME": "old"})

    written = push_from_env(vault_file, PASSWORD, keys=["REPLACE_ME"], overwrite=True)

    assert written["REPLACE_ME"] == "updated"
    vault = load_vault(vault_file, PASSWORD)
    assert vault["REPLACE_ME"] == "updated"


def test_push_creates_vault_if_missing(vault_file, monkeypatch):
    monkeypatch.setenv("BRAND_NEW", "hello")
    assert not os.path.exists(vault_file)

    push_from_env(vault_file, PASSWORD, keys=["BRAND_NEW"])

    assert os.path.exists(vault_file)
    vault = load_vault(vault_file, PASSWORD)
    assert vault["BRAND_NEW"] == "hello"
