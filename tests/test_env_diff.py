"""Tests for envault.env_diff — compare vault variables against the live environment."""

import os
import json
import pytest
from unittest.mock import patch
from pathlib import Path

from envault.env_diff import EnvDiffError, EnvDiffResult, env_diff
from envault.vault import save_vault


@pytest.fixture
def vault_file(tmp_path):
    """Return a path to a temporary vault file pre-populated with test variables."""
    path = tmp_path / "test.vault"
    save_vault(
        path,
        "secret",
        {
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "API_KEY": "abc123",
            "DEBUG": "true",
        },
    )
    return path


# ---------------------------------------------------------------------------
# EnvDiffResult.to_dict
# ---------------------------------------------------------------------------

def test_to_dict_contains_expected_keys():
    result = EnvDiffResult(
        key="FOO",
        vault_value="bar",
        env_value="baz",
        status="mismatch",
    )
    d = result.to_dict()
    assert d["key"] == "FOO"
    assert d["vault_value"] == "bar"
    assert d["env_value"] == "baz"
    assert d["status"] == "mismatch"


def test_to_dict_missing_env_value():
    result = EnvDiffResult(
        key="FOO",
        vault_value="bar",
        env_value=None,
        status="missing_in_env",
    )
    d = result.to_dict()
    assert d["env_value"] is None
    assert d["status"] == "missing_in_env"


# ---------------------------------------------------------------------------
# env_diff — all match
# ---------------------------------------------------------------------------

def test_env_diff_all_match(vault_file):
    env = {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "API_KEY": "abc123",
        "DEBUG": "true",
    }
    with patch.dict(os.environ, env, clear=False):
        results = env_diff(vault_file, "secret")

    statuses = {r.key: r.status for r in results}
    assert statuses["DB_HOST"] == "match"
    assert statuses["DB_PORT"] == "match"
    assert statuses["API_KEY"] == "match"
    assert statuses["DEBUG"] == "match"


# ---------------------------------------------------------------------------
# env_diff — missing in env
# ---------------------------------------------------------------------------

def test_env_diff_missing_in_env(vault_file):
    # Ensure none of the vault keys are in the environment
    with patch.dict(os.environ, {}, clear=True):
        results = env_diff(vault_file, "secret")

    statuses = {r.key: r.status for r in results}
    for key in ("DB_HOST", "DB_PORT", "API_KEY", "DEBUG"):
        assert statuses[key] == "missing_in_env"
        assert results[0].env_value is None or statuses[key] == "missing_in_env"


# ---------------------------------------------------------------------------
# env_diff — mismatch
# ---------------------------------------------------------------------------

def test_env_diff_mismatch(vault_file):
    env = {
        "DB_HOST": "remotehost",  # differs from vault value
        "DB_PORT": "5432",
        "API_KEY": "abc123",
        "DEBUG": "true",
    }
    with patch.dict(os.environ, env, clear=False):
        results = env_diff(vault_file, "secret")

    by_key = {r.key: r for r in results}
    assert by_key["DB_HOST"].status == "mismatch"
    assert by_key["DB_HOST"].vault_value == "localhost"
    assert by_key["DB_HOST"].env_value == "remotehost"
    assert by_key["DB_PORT"].status == "match"


# ---------------------------------------------------------------------------
# env_diff — specific keys filter
# ---------------------------------------------------------------------------

def test_env_diff_specific_keys(vault_file):
    env = {"DB_HOST": "localhost", "API_KEY": "wrong"}
    with patch.dict(os.environ, env, clear=False):
        results = env_diff(vault_file, "secret", keys=["DB_HOST", "API_KEY"])

    assert len(results) == 2
    by_key = {r.key: r for r in results}
    assert by_key["DB_HOST"].status == "match"
    assert by_key["API_KEY"].status == "mismatch"


def test_env_diff_specific_keys_not_in_vault(vault_file):
    """Requesting a key that doesn't exist in the vault should raise EnvDiffError."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(EnvDiffError, match="NONEXISTENT"):
            env_diff(vault_file, "secret", keys=["NONEXISTENT"])


# ---------------------------------------------------------------------------
# env_diff — wrong password
# ---------------------------------------------------------------------------

def test_env_diff_wrong_password_raises(vault_file):
    with pytest.raises(Exception):
        env_diff(vault_file, "wrongpassword")


# ---------------------------------------------------------------------------
# env_diff — missing vault file
# ---------------------------------------------------------------------------

def test_env_diff_missing_vault_raises(tmp_path):
    missing = tmp_path / "no_such.vault"
    with pytest.raises(EnvDiffError, match="not found"):
        env_diff(missing, "secret")


# ---------------------------------------------------------------------------
# env_diff — results sorted by key
# ---------------------------------------------------------------------------

def test_env_diff_results_sorted(vault_file):
    with patch.dict(os.environ, {}, clear=True):
        results = env_diff(vault_file, "secret")

    keys = [r.key for r in results]
    assert keys == sorted(keys)
