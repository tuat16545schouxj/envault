"""Tests for envault.pin."""

from __future__ import annotations

import pytest

from envault.vault import save_vault
from envault.pin import (
    PinError,
    get_pin_reason,
    is_pinned,
    list_pins,
    pin_var,
    unpin_var,
)


PASSWORD = "test-password"


@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "vault.enc")
    data = {"variables": {"FOO": "bar", "BAZ": "qux"}}
    save_vault(path, PASSWORD, data)
    return path


def test_pin_var_success(vault_file):
    pin_var(vault_file, PASSWORD, "FOO")
    pins = list_pins(vault_file, PASSWORD)
    assert "FOO" in pins


def test_pin_var_with_reason(vault_file):
    pin_var(vault_file, PASSWORD, "FOO", reason="do not change")
    reason = get_pin_reason(vault_file, PASSWORD, "FOO")
    assert reason == "do not change"


def test_pin_var_missing_key_raises(vault_file):
    with pytest.raises(PinError, match="does not exist"):
        pin_var(vault_file, PASSWORD, "MISSING_KEY")


def test_pin_idempotent(vault_file):
    pin_var(vault_file, PASSWORD, "FOO", reason="first")
    pin_var(vault_file, PASSWORD, "FOO", reason="second")
    assert get_pin_reason(vault_file, PASSWORD, "FOO") == "second"


def test_unpin_var_success(vault_file):
    pin_var(vault_file, PASSWORD, "FOO")
    unpin_var(vault_file, PASSWORD, "FOO")
    pins = list_pins(vault_file, PASSWORD)
    assert "FOO" not in pins


def test_unpin_not_pinned_raises(vault_file):
    with pytest.raises(PinError, match="not pinned"):
        unpin_var(vault_file, PASSWORD, "FOO")


def test_list_pins_empty(vault_file):
    assert list_pins(vault_file, PASSWORD) == {}


def test_list_pins_multiple(vault_file):
    pin_var(vault_file, PASSWORD, "FOO", reason="r1")
    pin_var(vault_file, PASSWORD, "BAZ", reason="r2")
    pins = list_pins(vault_file, PASSWORD)
    assert pins == {"FOO": "r1", "BAZ": "r2"}


def test_is_pinned_false_by_default(vault_file):
    from envault.vault import load_vault
    data = load_vault(vault_file, PASSWORD)
    assert not is_pinned(data, "FOO")


def test_is_pinned_true_after_pin(vault_file):
    pin_var(vault_file, PASSWORD, "FOO")
    from envault.vault import load_vault
    data = load_vault(vault_file, PASSWORD)
    assert is_pinned(data, "FOO")


def test_get_pin_reason_none_when_not_pinned(vault_file):
    assert get_pin_reason(vault_file, PASSWORD, "FOO") is None
