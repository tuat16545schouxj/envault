"""Quota management: enforce limits on the number of variables in a vault."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from envault.vault import VaultError, load_vault, save_vault

DEFAULT_QUOTA_KEY = "__quota__"


class QuotaError(Exception):
    """Raised when a quota operation fails."""


def set_quota(vault_path: Path, password: str, limit: int) -> None:
    """Set the maximum number of variables allowed in the vault."""
    if limit < 1:
        raise QuotaError("Quota limit must be a positive integer.")
    data = load_vault(vault_path, password)
    data.setdefault("__meta__", {})
    data["__meta__"][DEFAULT_QUOTA_KEY] = limit
    save_vault(vault_path, password, data)


def remove_quota(vault_path: Path, password: str) -> None:
    """Remove the quota limit from the vault."""
    data = load_vault(vault_path, password)
    meta = data.get("__meta__", {})
    meta.pop(DEFAULT_QUOTA_KEY, None)
    data["__meta__"] = meta
    save_vault(vault_path, password, data)


def get_quota(vault_path: Path, password: str) -> Optional[int]:
    """Return the configured quota limit, or None if not set."""
    data = load_vault(vault_path, password)
    return data.get("__meta__", {}).get(DEFAULT_QUOTA_KEY)


def check_quota(vault_path: Path, password: str) -> dict:
    """Return a dict with quota status: limit, used, remaining, exceeded."""
    data = load_vault(vault_path, password)
    limit = data.get("__meta__", {}).get(DEFAULT_QUOTA_KEY)
    vars_ = {k: v for k, v in data.get("vars", {}).items()}
    used = len(vars_)
    if limit is None:
        return {"limit": None, "used": used, "remaining": None, "exceeded": False}
    remaining = max(0, limit - used)
    return {
        "limit": limit,
        "used": used,
        "remaining": remaining,
        "exceeded": used > limit,
    }


def enforce_quota(vault_path: Path, password: str) -> None:
    """Raise QuotaError if the vault currently exceeds its quota."""
    status = check_quota(vault_path, password)
    if status["exceeded"]:
        raise QuotaError(
            f"Vault exceeds quota: {status['used']} variables set, "
            f"limit is {status['limit']}."
        )
