"""Tests for envault.search."""

from __future__ import annotations

import pytest

from envault.search import SearchError, SearchResult, search_vars
from envault.vault import save_vault


@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "vault.enc")
    data = {
        "DATABASE_URL": "postgres://localhost/db",
        "DATABASE_POOL": "5",
        "REDIS_URL": "redis://localhost",
        "SECRET_KEY": "supersecret",
    }
    save_vault(path, "pw", data)
    return path


def test_search_exact_key(vault_file):
    results = search_vars(vault_file, "pw", "SECRET_KEY")
    assert len(results) == 1
    assert results[0].key == "SECRET_KEY"


def test_search_wildcard_prefix(vault_file):
    results = search_vars(vault_file, "pw", "database*")
    keys = [r.key for r in results]
    assert "DATABASE_URL" in keys
    assert "DATABASE_POOL" in keys
    assert "REDIS_URL" not in keys


def test_search_case_insensitive_default(vault_file):
    results = search_vars(vault_file, "pw", "secret*")
    assert any(r.key == "SECRET_KEY" for r in results)


def test_search_case_sensitive_no_match(vault_file):
    results = search_vars(vault_file, "pw", "secret*", case_sensitive=True)
    assert results == []


def test_search_results_sorted(vault_file):
    results = search_vars(vault_file, "pw", "database*")
    keys = [r.key for r in results]
    assert keys == sorted(keys)


def test_search_values(vault_file):
    results = search_vars(vault_file, "pw", "*localhost*", search_values=True)
    keys = {r.key for r in results}
    assert "DATABASE_URL" in keys
    assert "REDIS_URL" in keys
    assert "SECRET_KEY" not in keys


def test_search_no_match_returns_empty(vault_file):
    results = search_vars(vault_file, "pw", "NOTHING*")
    assert results == []


def test_search_wrong_password_raises(vault_file):
    with pytest.raises(SearchError):
        search_vars(vault_file, "wrong", "*")


def test_search_result_to_dict(vault_file):
    results = search_vars(vault_file, "pw", "REDIS_URL")
    assert results[0].to_dict() == {"key": "REDIS_URL", "value": "redis://localhost"}
