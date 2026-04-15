"""Tests for envault.sync (push_vault / pull_vault)."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
import respx

from envault.sync import SyncError, pull_vault, push_vault

REMOTE_URL = "https://envault.example.com/vault/myproject"
TOKEN = "test-token-abc"
FAKE_PAYLOAD = b"encrypted-vault-bytes"
FAKE_CHECKSUM = "abc123"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    path = tmp_path / ".envault"
    path.write_bytes(FAKE_PAYLOAD)
    return path


# ---------------------------------------------------------------------------
# push_vault
# ---------------------------------------------------------------------------


@respx.mock
def test_push_vault_success(vault_file: Path) -> None:
    respx.put(REMOTE_URL).mock(
        return_value=httpx.Response(200, json={"checksum": FAKE_CHECKSUM})
    )
    result = push_vault(vault_file, REMOTE_URL, TOKEN)
    assert result == FAKE_CHECKSUM


@respx.mock
def test_push_vault_sends_auth_header(vault_file: Path) -> None:
    route = respx.put(REMOTE_URL).mock(
        return_value=httpx.Response(200, json={"checksum": FAKE_CHECKSUM})
    )
    push_vault(vault_file, REMOTE_URL, TOKEN)
    assert route.called
    request = route.calls.last.request
    assert request.headers["Authorization"] == f"Bearer {TOKEN}"


@respx.mock
def test_push_vault_http_error_raises_sync_error(vault_file: Path) -> None:
    respx.put(REMOTE_URL).mock(return_value=httpx.Response(403, text="Forbidden"))
    with pytest.raises(SyncError, match="403"):
        push_vault(vault_file, REMOTE_URL, TOKEN)


def test_push_vault_missing_file_raises_sync_error(tmp_path: Path) -> None:
    missing = tmp_path / "nonexistent.vault"
    with pytest.raises(SyncError, match="not found"):
        push_vault(missing, REMOTE_URL, TOKEN)


@respx.mock
def test_push_vault_connection_error_raises_sync_error(vault_file: Path) -> None:
    respx.put(REMOTE_URL).mock(side_effect=httpx.ConnectError("refused"))
    with pytest.raises(SyncError, match="connection error"):
        push_vault(vault_file, REMOTE_URL, TOKEN)


# ---------------------------------------------------------------------------
# pull_vault
# ---------------------------------------------------------------------------


@respx.mock
def test_pull_vault_writes_file(tmp_path: Path) -> None:
    dest = tmp_path / ".envault"
    respx.get(REMOTE_URL).mock(
        return_value=httpx.Response(
            200,
            content=FAKE_PAYLOAD,
            headers={"X-Vault-Checksum": FAKE_CHECKSUM},
        )
    )
    updated = pull_vault(dest, REMOTE_URL, TOKEN)
    assert updated is True
    assert dest.read_bytes() == FAKE_PAYLOAD


@respx.mock
def test_pull_vault_already_up_to_date(vault_file: Path) -> None:
    import hashlib

    checksum = hashlib.sha256(FAKE_PAYLOAD).hexdigest()
    respx.get(REMOTE_URL).mock(
        return_value=httpx.Response(
            200,
            content=FAKE_PAYLOAD,
            headers={"X-Vault-Checksum": checksum},
        )
    )
    updated = pull_vault(vault_file, REMOTE_URL, TOKEN)
    assert updated is False


@respx.mock
def test_pull_vault_http_error_raises_sync_error(tmp_path: Path) -> None:
    dest = tmp_path / ".envault"
    respx.get(REMOTE_URL).mock(return_value=httpx.Response(404, text="Not Found"))
    with pytest.raises(SyncError, match="404"):
        pull_vault(dest, REMOTE_URL, TOKEN)


@respx.mock
def test_pull_vault_creates_parent_dirs(tmp_path: Path) -> None:
    dest = tmp_path / "nested" / "dir" / ".envault"
    respx.get(REMOTE_URL).mock(
        return_value=httpx.Response(
            200,
            content=FAKE_PAYLOAD,
            headers={"X-Vault-Checksum": FAKE_CHECKSUM},
        )
    )
    pull_vault(dest, REMOTE_URL, TOKEN)
    assert dest.exists()
