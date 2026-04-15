"""Tests for envault.export module."""

import json
import pytest

from envault.export import (
    ExportError,
    export_dotenv,
    export_shell,
    export_json,
    export_variables,
)

SAMPLE = {"DATABASE_URL": "postgres://localhost/db", "SECRET_KEY": 'abc"def'}


def test_export_dotenv_basic():
    result = export_dotenv({"FOO": "bar"})
    assert result == 'FOO="bar"\n'


def test_export_dotenv_escapes_quotes():
    result = export_dotenv({"K": 'say "hi"'})
    assert '\\"' in result


def test_export_dotenv_sorted_keys():
    result = export_dotenv({"Z": "1", "A": "2"})
    lines = result.strip().splitlines()
    assert lines[0].startswith("A=")
    assert lines[1].startswith("Z=")


def test_export_dotenv_empty():
    assert export_dotenv({}) == ""


def test_export_shell_uses_export():
    result = export_shell({"MY_VAR": "hello"})
    assert result.startswith("export MY_VAR=")


def test_export_shell_escapes_quotes():
    result = export_shell({"K": 'it\'s a "test"'})
    assert '\\"' in result


def test_export_json_valid():
    result = export_json(SAMPLE)
    parsed = json.loads(result)
    assert parsed["DATABASE_URL"] == SAMPLE["DATABASE_URL"]
    assert parsed["SECRET_KEY"] == SAMPLE["SECRET_KEY"]


def test_export_json_sorted_keys():
    result = export_json({"Z": "1", "A": "2"})
    parsed = json.loads(result)
    assert list(parsed.keys()) == sorted(parsed.keys())


def test_export_variables_dotenv():
    result = export_variables({"X": "1"}, "dotenv")
    assert 'X="1"' in result


def test_export_variables_shell():
    result = export_variables({"X": "1"}, "shell")
    assert "export X=" in result


def test_export_variables_json():
    result = export_variables({"X": "1"}, "json")
    assert json.loads(result) == {"X": "1"}


def test_export_variables_unsupported_format():
    with pytest.raises(ExportError, match="Unsupported format"):
        export_variables({"X": "1"}, "yaml")
