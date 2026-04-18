"""Vault locking: temporarily lock a vault to prevent modifications."""

from __future__ import annotations

import json
import time
from pathlib import Path

LOCK_SUFFIX = ".lock"


class LockError(Exception):
    pass


def _lock_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix(LOCK_SUFFIX)


def lock_vault(vault_path: str, reason: str = "", ttl_seconds: int = 3600) -> None:
    """Create a lock file for the vault. Raises LockError if already locked."""
    lp = _lock_path(vault_path)
    if lp.exists():
        info = _read_lock(lp)
        raise LockError(
            f"Vault is already locked by '{info.get('user', 'unknown')}' "
            f"at {info.get('locked_at', '?')}. Reason: {info.get('reason', '')}"
        )
    import getpass
    payload = {
        "user": getpass.getuser(),
        "locked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "expires_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + ttl_seconds)),
        "reason": reason,
    }
    lp.write_text(json.dumps(payload))


def unlock_vault(vault_path: str) -> None:
    """Remove the lock file. Raises LockError if not locked."""
    lp = _lock_path(vault_path)
    if not lp.exists():
        raise LockError("Vault is not locked.")
    lp.unlink()


def is_locked(vault_path: str) -> bool:
    lp = _lock_path(vault_path)
    if not lp.exists():
        return False
    info = _read_lock(lp)
    expires_at = info.get("expires_at")
    if expires_at:
        expiry = time.strptime(expires_at, "%Y-%m-%dT%H:%M:%SZ")
        if time.gmtime() > expiry:
            lp.unlink()
            return False
    return True


def get_lock_info(vault_path: str) -> dict | None:
    lp = _lock_path(vault_path)
    if not lp.exists():
        return None
    return _read_lock(lp)


def _read_lock(lp: Path) -> dict:
    try:
        return json.loads(lp.read_text())
    except Exception:
        return {}
