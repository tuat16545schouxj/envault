"""Tests for envault.profile module."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.profile import (
    ProfileError,
    delete_profile,
    get_profile_vars,
    list_profiles,
    save_profile,
)
from envault.vault import save_vault

PASSWORD = "test-secret"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    path = tmp_path / ".envault"
    save_vault(path, PASSWORD, {"KEY1": "val1", "KEY2": "val2"})
    return path


def test_save_profile_creates_entry(vault_file: Path) -> None:
    save_profile(vault_file, PASSWORD, "dev")
    profiles = list_profiles(vault_file, PASSWORD)
    assert "dev" in profiles


def test_list_profiles_empty_vault(tmp_path: Path) -> None:
    path = tmp_path / ".envault"
    save_vault(path, PASSWORD, {})
    assert list_profiles(path, PASSWORD) == []


def test_list_profiles_returns_sorted(vault_file: Path) -> None:
    save_profile(vault_file, PASSWORD, "staging")
    save_profile(vault_file, PASSWORD, "dev")
    save_profile(vault_file, PASSWORD, "prod")
    profiles = list_profiles(vault_file, PASSWORD)
    assert profiles == sorted(profiles)


def test_get_profile_vars_returns_correct_keys(vault_file: Path) -> None:
    save_profile(vault_file, PASSWORD, "dev")
    variables = get_profile_vars(vault_file, PASSWORD, "dev")
    assert variables == {"KEY1": "val1", "KEY2": "val2"}


def test_get_profile_vars_missing_profile_raises(vault_file: Path) -> None:
    with pytest.raises(ProfileError, match="does not exist"):
        get_profile_vars(vault_file, PASSWORD, "nonexistent")


def test_delete_profile_removes_entry(vault_file: Path) -> None:
    save_profile(vault_file, PASSWORD, "dev")
    delete_profile(vault_file, PASSWORD, "dev")
    assert "dev" not in list_profiles(vault_file, PASSWORD)


def test_delete_nonexistent_profile_raises(vault_file: Path) -> None:
    with pytest.raises(ProfileError, match="does not exist"):
        delete_profile(vault_file, PASSWORD, "ghost")


def test_multiple_profiles_independent(vault_file: Path) -> None:
    save_profile(vault_file, PASSWORD, "dev")
    save_profile(vault_file, PASSWORD, "prod")
    profiles = list_profiles(vault_file, PASSWORD)
    assert "dev" in profiles
    assert "prod" in profiles
    assert len(profiles) == 2
