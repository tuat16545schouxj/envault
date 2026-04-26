"""Tests for envault.annotate and envault.cli_annotate."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.annotate import AnnotateError, get_annotation, list_annotations, remove_annotation, set_annotation
from envault.cli_annotate import annotate_group
from envault.vault import save_vault


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "vault.enc")
    data = {"vars": {"DB_URL": "postgres://localhost", "API_KEY": "secret"}}
    save_vault(path, "pw", data)
    return path


@pytest.fixture()
def runner():
    return CliRunner()


def _args(vault_file, *extra):
    return ["--vault", vault_file, "--password", "pw", *extra]


# ---------------------------------------------------------------------------
# Unit tests — annotate module
# ---------------------------------------------------------------------------

def test_set_annotation_success(vault_file):
    set_annotation(vault_file, "pw", "DB_URL", "Primary database connection string")
    note = get_annotation(vault_file, "pw", "DB_URL")
    assert note == "Primary database connection string"


def test_set_annotation_strips_whitespace(vault_file):
    set_annotation(vault_file, "pw", "API_KEY", "  my note  ")
    assert get_annotation(vault_file, "pw", "API_KEY") == "my note"


def test_set_annotation_missing_key_raises(vault_file):
    with pytest.raises(AnnotateError, match="not found"):
        set_annotation(vault_file, "pw", "MISSING", "some note")


def test_set_annotation_empty_note_raises(vault_file):
    with pytest.raises(AnnotateError, match="must not be empty"):
        set_annotation(vault_file, "pw", "DB_URL", "   ")


def test_get_annotation_none_when_not_set(vault_file):
    assert get_annotation(vault_file, "pw", "DB_URL") is None


def test_remove_annotation_success(vault_file):
    set_annotation(vault_file, "pw", "DB_URL", "to be removed")
    remove_annotation(vault_file, "pw", "DB_URL")
    assert get_annotation(vault_file, "pw", "DB_URL") is None


def test_remove_annotation_missing_raises(vault_file):
    with pytest.raises(AnnotateError, match="No annotation"):
        remove_annotation(vault_file, "pw", "DB_URL")


def test_list_annotations_sorted(vault_file):
    set_annotation(vault_file, "pw", "DB_URL", "note b")
    set_annotation(vault_file, "pw", "API_KEY", "note a")
    result = list_annotations(vault_file, "pw")
    assert list(result.keys()) == ["API_KEY", "DB_URL"]


def test_list_annotations_empty(vault_file):
    assert list_annotations(vault_file, "pw") == {}


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

def test_cli_set_and_show(runner, vault_file):
    result = runner.invoke(annotate_group, _args(vault_file, "set", "DB_URL", "main db"))
    assert result.exit_code == 0
    assert "Annotation set" in result.output

    result = runner.invoke(annotate_group, _args(vault_file, "show", "DB_URL"))
    assert result.exit_code == 0
    assert "main db" in result.output


def test_cli_show_no_annotation(runner, vault_file):
    result = runner.invoke(annotate_group, _args(vault_file, "show", "DB_URL"))
    assert result.exit_code == 0
    assert "No annotation" in result.output


def test_cli_list_empty(runner, vault_file):
    result = runner.invoke(annotate_group, _args(vault_file, "list"))
    assert result.exit_code == 0
    assert "No annotations" in result.output


def test_cli_remove_output(runner, vault_file):
    runner.invoke(annotate_group, _args(vault_file, "set", "API_KEY", "key note"))
    result = runner.invoke(annotate_group, _args(vault_file, "remove", "API_KEY"))
    assert result.exit_code == 0
    assert "removed" in result.output


def test_cli_set_missing_key_error(runner, vault_file):
    result = runner.invoke(annotate_group, _args(vault_file, "set", "NOPE", "note"))
    assert result.exit_code != 0
    assert "not found" in result.output
