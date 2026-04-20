"""Tests for envault.env_compare."""

from __future__ import annotations

import json
import os

import pytest

from envault.env_compare import EnvCompareError, compare_env
from envault.vault import save_vault


@pytest.fixture
def vault_file(tmp_path):
    path = str(tmp_path / "vault.enc")
    save_vault(
        path,
        "secret",
        {
            "variables": {
                "APP_ENV": "production",
                "DB_HOST": "db.example.com",
                "DEBUG": "false",
            }
        },
    )
    return path


def test_compare_all_match(vault_file):
    env = {"APP_ENV": "production", "DB_HOST": "db.example.com", "DEBUG": "false"}
    results = compare_env(vault_file, "secret", env=env)
    assert all(r.status == "match" for r in results)
    assert [r.key for r in results] == ["APP_ENV", "DB_HOST", "DEBUG"]


def test_compare_missing_in_env(vault_file):
    env = {"APP_ENV": "production"}  # DB_HOST and DEBUG absent
    results = compare_env(vault_file, "secret", env=env)
    statuses = {r.key: r.status for r in results}
    assert statuses["APP_ENV"] == "match"
    assert statuses["DB_HOST"] == "missing_in_env"
    assert statuses["DEBUG"] == "missing_in_env"


def test_compare_mismatch(vault_file):
    env = {"APP_ENV": "staging", "DB_HOST": "db.example.com", "DEBUG": "false"}
    results = compare_env(vault_file, "secret", env=env)
    statuses = {r.key: r.status for r in results}
    assert statuses["APP_ENV"] == "mismatch"
    assert statuses["DB_HOST"] == "match"


def test_compare_specific_keys(vault_file):
    env = {"APP_ENV": "production", "DB_HOST": "wrong"}
    results = compare_env(vault_file, "secret", keys=["APP_ENV", "DB_HOST"], env=env)
    assert len(results) == 2
    statuses = {r.key: r.status for r in results}
    assert statuses["APP_ENV"] == "match"
    assert statuses["DB_HOST"] == "mismatch"


def test_compare_specific_keys_missing_in_vault(vault_file):
    with pytest.raises(EnvCompareError, match="NONEXISTENT"):
        compare_env(vault_file, "secret", keys=["NONEXISTENT"], env={})


def test_compare_wrong_password(vault_file):
    with pytest.raises(EnvCompareError):
        compare_env(vault_file, "wrongpassword", env={})


def test_compare_env_value_stored_in_result(vault_file):
    env = {"APP_ENV": "staging", "DB_HOST": "db.example.com", "DEBUG": "false"}
    results = compare_env(vault_file, "secret", env=env)
    app_env_result = next(r for r in results if r.key == "APP_ENV")
    assert app_env_result.env_value == "staging"
    assert app_env_result.vault_value == "production"


def test_compare_missing_env_value_is_none(vault_file):
    results = compare_env(vault_file, "secret", env={})
    for r in results:
        assert r.env_value is None
        assert r.status == "missing_in_env"


def test_to_dict_structure(vault_file):
    env = {"APP_ENV": "production"}
    results = compare_env(vault_file, "secret", keys=["APP_ENV"], env=env)
    d = results[0].to_dict()
    assert set(d.keys()) == {"key", "vault_value", "env_value", "status"}
    assert d["status"] == "match"
