"""Tests for envault.env_check module."""

from __future__ import annotations

import json
import os

import pytest

from envault.env_check import EnvCheckError, check_env
from envault.vault import save_vault


@pytest.fixture()
def vault_file(tmp_path):
    path = tmp_path / "vault.env"
    save_vault(
        str(path),
        "secret",
        {"variables": {"DB_HOST": "localhost", "DB_PORT": "5432", "API_KEY": "abc123"}},
    )
    return str(path)


def test_check_env_all_missing(vault_file, monkeypatch):
    for key in ("DB_HOST", "DB_PORT", "API_KEY"):
        monkeypatch.delenv(key, raising=False)

    results = check_env(vault_file, "secret")
    assert all(r.status == "missing" for r in results)
    assert [r.key for r in results] == ["API_KEY", "DB_HOST", "DB_PORT"]


def test_check_env_all_present(vault_file, monkeypatch):
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("API_KEY", "abc123")

    results = check_env(vault_file, "secret")
    assert all(r.status == "ok" for r in results)


def test_check_env_partial_missing(vault_file, monkeypatch):
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.delenv("DB_PORT", raising=False)
    monkeypatch.delenv("API_KEY", raising=False)

    results = {r.key: r.status for r in check_env(vault_file, "secret")}
    assert results["DB_HOST"] == "ok"
    assert results["DB_PORT"] == "missing"
    assert results["API_KEY"] == "missing"


def test_check_env_specific_keys(vault_file, monkeypatch):
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.delenv("API_KEY", raising=False)

    results = check_env(vault_file, "secret", keys=["DB_HOST", "API_KEY"])
    assert len(results) == 2
    statuses = {r.key: r.status for r in results}
    assert statuses["DB_HOST"] == "ok"
    assert statuses["API_KEY"] == "missing"


def test_check_env_value_mismatch(vault_file, monkeypatch):
    monkeypatch.setenv("DB_HOST", "remotehost")

    results = check_env(vault_file, "secret", keys=["DB_HOST"], check_values=True)
    assert len(results) == 1
    r = results[0]
    assert r.status == "mismatch"
    assert r.vault_value == "localhost"
    assert r.env_value == "remotehost"


def test_check_env_value_match(vault_file, monkeypatch):
    monkeypatch.setenv("DB_HOST", "localhost")

    results = check_env(vault_file, "secret", keys=["DB_HOST"], check_values=True)
    assert results[0].status == "ok"


def test_check_env_wrong_password(vault_file):
    with pytest.raises(EnvCheckError, match="password|decrypt|invalid"):
        check_env(vault_file, "wrongpassword")


def test_check_env_missing_key_raises(vault_file):
    with pytest.raises(EnvCheckError, match="NONEXISTENT"):
        check_env(vault_file, "secret", keys=["NONEXISTENTndef test_to_dict_structure(vault_file, monkeypatch):
    monkeypatch.setenv("DB_HOST", "other")
    results = check_env(vault_file, "secret", keys=["DB_HOST"], check_values=True)
    d = results[0].to_dict()
    assert set(d.keys()) == {"key", "status", "vault_value", "env_value"}
