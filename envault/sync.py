"""Remote sync support for envault — push/pull vault files via a remote URL."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Optional

import httpx

from envault.vault import VaultError, load_vault, save_vault


class SyncError(Exception):
    """Raised when a remote sync operation fails."""


def _vault_checksum(vault_path: Path) -> str:
    """Return the SHA-256 hex digest of the raw vault file bytes."""
    data = vault_path.read_bytes()
    return hashlib.sha256(data).hexdigest()


def push_vault(
    vault_path: Path,
    remote_url: str,
    token: str,
    *,
    timeout: float = 10.0,
) -> str:
    """Upload the encrypted vault file to *remote_url*.

    Returns the server-reported checksum on success.
    Raises :class:`SyncError` on any HTTP or connectivity error.
    """
    if not vault_path.exists():
        raise SyncError(f"Vault file not found: {vault_path}")

    payload = vault_path.read_bytes()
    checksum = _vault_checksum(vault_path)

    try:
        response = httpx.put(
            remote_url,
            content=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/octet-stream",
                "X-Vault-Checksum": checksum,
            },
            timeout=timeout,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise SyncError(
            f"Push failed — HTTP {exc.response.status_code}: {exc.response.text}"
        ) from exc
    except httpx.RequestError as exc:
        raise SyncError(f"Push failed — connection error: {exc}") from exc

    body = response.json()
    return body.get("checksum", checksum)


def pull_vault(
    vault_path: Path,
    remote_url: str,
    token: str,
    *,
    timeout: float = 10.0,
) -> bool:
    """Download the encrypted vault file from *remote_url* and write it to disk.

    Returns ``True`` when the local file was updated, ``False`` when it was
    already up-to-date (server checksum matches local checksum).
    Raises :class:`SyncError` on any HTTP or connectivity error.
    """
    local_checksum: Optional[str] = None
    if vault_path.exists():
        local_checksum = _vault_checksum(vault_path)

    try:
        response = httpx.get(
            remote_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise SyncError(
            f"Pull failed — HTTP {exc.response.status_code}: {exc.response.text}"
        ) from exc
    except httpx.RequestError as exc:
        raise SyncError(f"Pull failed — connection error: {exc}") from exc

    remote_checksum = response.headers.get("X-Vault-Checksum", "")
    if local_checksum and remote_checksum and local_checksum == remote_checksum:
        return False

    vault_path.parent.mkdir(parents=True, exist_ok=True)
    vault_path.write_bytes(response.content)
    return True
