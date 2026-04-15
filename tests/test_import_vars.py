"""Tests for envault/import_vars.py."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.import_vars import parse_dotenv, import_from_file, ImportError
from envault.vault import load_vault


# ---------------------------------------------------------------------------
# parse_dotenv
# ---------------------------------------------------------------------------

def test_parse_dotenv_basic():
    text = "KEY=value\nFOO=bar"
    assert parse_dotenv(text) == {"KEY": "value", "FOO": "bar"}


def test_parse_dotenv_export_prefix():
    text = "export API_KEY=secret123"
    assert parse_dotenv(text) == {"API_KEY": "secret123"}


def test_parse_dotenv_double_quoted():
    text = 'DB_URL="postgres://localhost/mydb"'
    assert parse_dotenv(text) == {"DB_URL": "postgres://localhost/mydb"}


def test_parse_dotenv_single_quoted():
    text = "SECRET='hello world'"
    assert parse_dotenv(text) == {"SECRET": "hello world"}


def test_parse_dotenv_skips_comments_and_blanks():
    text = "# This is a comment\n\nKEY=value\n  # another comment\n"
    assert parse_dotenv(text) == {"KEY": "value"}


def test_parse_dotenv_inline_comment_stripped():
    text = "KEY=value # inline comment"
    assert parse_dotenv(text) == {"KEY": "value"}


def test_parse_dotenv_empty_value():
    text = "EMPTY="
    assert parse_dotenv(text) == {"EMPTY": ""}


def test_parse_dotenv_empty_string():
    assert parse_dotenv("") == {}


# ---------------------------------------------------------------------------
# import_from_file
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("FOO=bar\nBAZ=qux\n")
    return p


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    return tmp_path / "vault.json.enc"


def test_import_from_file_creates_vault(env_file, vault_file):
    imported, skipped = import_from_file(env_file, vault_file, "pass")
    assert imported == 2
    assert skipped == 0
    data = load_vault(vault_file, "pass")
    assert data["FOO"] == "bar"
    assert data["BAZ"] == "qux"


def test_import_from_file_skips_existing_when_no_overwrite(env_file, vault_file):
    # Pre-populate vault with FOO
    from envault.vault import set_var
    set_var(vault_file, "pass", "FOO", "original")

    imported, skipped = import_from_file(env_file, vault_file, "pass", overwrite=False)
    assert skipped == 1
    assert imported == 1
    data = load_vault(vault_file, "pass")
    assert data["FOO"] == "original"  # unchanged
    assert data["BAZ"] == "qux"       # new key imported


def test_import_from_file_overwrite_replaces_existing(env_file, vault_file):
    from envault.vault import set_var
    set_var(vault_file, "pass", "FOO", "original")

    imported, skipped = import_from_file(env_file, vault_file, "pass", overwrite=True)
    assert imported == 2
    assert skipped == 0
    data = load_vault(vault_file, "pass")
    assert data["FOO"] == "bar"  # overwritten


def test_import_from_file_missing_source_raises(tmp_path, vault_file):
    missing = tmp_path / "nonexistent.env"
    with pytest.raises(ImportError, match="Cannot read source file"):
        import_from_file(missing, vault_file, "pass")


def test_import_from_file_empty_file_returns_zeros(tmp_path, vault_file):
    empty = tmp_path / "empty.env"
    empty.write_text("# only a comment\n")
    imported, skipped = import_from_file(empty, vault_file, "pass")
    assert imported == 0
    assert skipped == 0
