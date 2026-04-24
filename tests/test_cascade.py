"""Tests for envault.cascade."""

from __future__ import annotations

import json
import os

import pytest
from click.testing import CliRunner

from envault.cascade import CascadeError, resolve_cascade
from envault.cli_cascade import cascade_group
from envault.vault import save_vault


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "test.vault")
    data = {
        "vars": {
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "prod.DB_HOST": "prod.db.example.com",
            "prod.DB_PORT": "5433",
            "staging.DB_HOST": "staging.db.example.com",
        },
        "profiles": {
            "backend": {"keys": ["DB_HOST", "DB_PORT"]},
        },
    }
    save_vault(path, "secret", data)
    return path


# ---------------------------------------------------------------------------
# Unit tests for resolve_cascade
# ---------------------------------------------------------------------------

def test_resolve_root_layer(vault_file):
    result = resolve_cascade(vault_file, "secret", ["__root__"])
    assert result.resolved["DB_HOST"] == "localhost"
    assert result.sources["DB_HOST"] == "__root__"


def test_later_layer_wins(vault_file):
    result = resolve_cascade(vault_file, "secret", ["__root__", "prod"])
    assert result.resolved["DB_HOST"] == "prod.db.example.com"
    assert result.sources["DB_HOST"] == "prod"
    # DB_PORT not in prod namespace -> still from __root__
    assert result.resolved["DB_PORT"] == "5432"
    assert result.sources["DB_PORT"] == "__root__"


def test_profile_layer(vault_file):
    result = resolve_cascade(vault_file, "secret", ["backend"])
    assert set(result.resolved.keys()) == {"DB_HOST", "DB_PORT"}
    assert result.sources["DB_HOST"] == "backend"


def test_base_lowest_priority(vault_file):
    base = {"DB_HOST": "base-host", "EXTRA": "extra-val"}
    result = resolve_cascade(vault_file, "secret", ["__root__"], base=base)
    # __root__ overrides base for DB_HOST
    assert result.resolved["DB_HOST"] == "localhost"
    assert result.sources["DB_HOST"] == "__root__"
    # EXTRA comes from base
    assert result.resolved["EXTRA"] == "extra-val"
    assert result.sources["EXTRA"] == "__base__"


def test_empty_layers_raises(vault_file):
    with pytest.raises(CascadeError, match="At least one layer"):
        resolve_cascade(vault_file, "secret", [])


def test_wrong_password_raises(vault_file):
    with pytest.raises(CascadeError, match="Failed to load vault"):
        resolve_cascade(vault_file, "wrong", ["__root__"])


def test_to_dict_shape(vault_file):
    result = resolve_cascade(vault_file, "secret", ["__root__"])
    d = result.to_dict()
    assert "resolved" in d
    assert "sources" in d


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def _args(vault_file):
    return ["--vault", vault_file, "--password", "secret"]


def test_cli_resolve_table(runner, vault_file, _args):
    result = runner.invoke(cascade_group, ["resolve"] + _args + ["--layer", "__root__"])
    assert result.exit_code == 0
    assert "DB_HOST" in result.output
    assert "localhost" in result.output


def test_cli_resolve_json(runner, vault_file, _args):
    result = runner.invoke(
        cascade_group,
        ["resolve"] + _args + ["--layer", "__root__", "--format", "json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "resolved" in data
    assert data["resolved"]["DB_HOST"] == "localhost"


def test_cli_resolve_show_source(runner, vault_file, _args):
    result = runner.invoke(
        cascade_group,
        ["resolve"] + _args + ["--layer", "__root__", "--layer", "prod", "--show-source"],
    )
    assert result.exit_code == 0
    assert "(prod)" in result.output


def test_cli_resolve_bad_password(runner, vault_file):
    result = runner.invoke(
        cascade_group,
        ["resolve", "--vault", vault_file, "--password", "bad", "--layer", "__root__"],
    )
    assert result.exit_code != 0
    assert "Error" in result.output
