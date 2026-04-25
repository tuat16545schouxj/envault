"""Tests for envault.transform module."""
from __future__ import annotations

import json
import os
import pytest

from envault.transform import (
    TransformError,
    apply_transform,
    list_transforms,
    transform_var,
)
from envault.vault import save_vault


@pytest.fixture
def vault_file(tmp_path):
    path = str(tmp_path / "vault.env")
    save_vault(path, "secret", {"GREETING": "hello world", "TOKEN": "  abc123  "})
    return path


# --- list_transforms ---

def test_list_transforms_returns_sorted_list():
    names = list_transforms()
    assert isinstance(names, list)
    assert names == sorted(names)
    assert "upper" in names
    assert "lower" in names


# --- apply_transform ---

def test_apply_transform_upper():
    assert apply_transform("hello", "upper") == "HELLO"


def test_apply_transform_lower():
    assert apply_transform("WORLD", "lower") == "world"


def test_apply_transform_strip():
    assert apply_transform("  hi  ", "strip") == "hi"


def test_apply_transform_reverse():
    assert apply_transform("abc", "reverse") == "cba"


def test_apply_transform_base64_roundtrip():
    original = "my-secret-value"
    encoded = apply_transform(original, "base64_encode")
    decoded = apply_transform(encoded, "base64_decode")
    assert decoded == original


def test_apply_transform_url_encode():
    result = apply_transform("hello world&foo=bar", "url_encode")
    assert " " not in result
    assert "%20" in result or "+" in result


def test_apply_transform_trim_quotes():
    assert apply_transform('"value"', "trim_quotes") == "value"
    assert apply_transform("'value'", "trim_quotes") == "value"


def test_apply_transform_unknown_raises():
    with pytest.raises(TransformError, match="Unknown transform"):
        apply_transform("value", "nonexistent_transform")


# --- transform_var ---

def test_transform_var_single_transform(vault_file):
    result = transform_var(vault_file, "secret", "GREETING", ["upper"])
    assert result == "HELLO WORLD"


def test_transform_var_chained_transforms(vault_file):
    result = transform_var(vault_file, "secret", "TOKEN", ["strip", "upper"])
    assert result == "ABC123"


def test_transform_var_persists_value(vault_file):
    transform_var(vault_file, "secret", "GREETING", ["upper"])
    from envault.vault import load_vault
    data = load_vault(vault_file, "secret")
    assert data["GREETING"] == "HELLO WORLD"


def test_transform_var_dry_run_does_not_persist(vault_file):
    result = transform_var(vault_file, "secret", "GREETING", ["upper"], dry_run=True)
    assert result == "HELLO WORLD"
    from envault.vault import load_vault
    data = load_vault(vault_file, "secret")
    assert data["GREETING"] == "hello world"  # unchanged


def test_transform_var_missing_key_raises(vault_file):
    with pytest.raises(TransformError, match="not found in vault"):
        transform_var(vault_file, "secret", "MISSING_KEY", ["upper"])


def test_transform_var_unknown_transform_raises(vault_file):
    with pytest.raises(TransformError, match="Unknown transform"):
        transform_var(vault_file, "secret", "GREETING", ["bogus"])
