"""Quota-aware guarded set: prevents writing variables when quota is exceeded."""

from __future__ import annotations

from pathlib import Path

from envault.quota import QuotaError, check_quota
from envault.vault import VaultError, load_vault, save_vault


class QuotaGuardError(Exception):
    """Raised when a write is blocked by the quota limit."""


def guarded_set_with_quota(
    vault_path: Path,
    password: str,
    key: str,
    value: str,
) -> None:
    """Set a variable, enforcing the quota limit before writing.

    If the key already exists the quota is not re-checked (it's an update).
    If the key is new and would exceed the quota, QuotaGuardError is raised.
    """
    data = load_vault(vault_path, password)
    vars_ = data.setdefault("vars", {})

    is_new_key = key not in vars_
    if is_new_key:
        status = check_quota(vault_path, password)
        if status["limit"] is not None and status["used"] >= status["limit"]:
            raise QuotaGuardError(
                f"Cannot add '{key}': quota limit of {status['limit']} variables reached."
            )

    vars_[key] = value
    save_vault(vault_path, password, data)


def quota_summary(vault_path: Path, password: str) -> str:
    """Return a human-readable one-line quota summary string."""
    status = check_quota(vault_path, password)
    if status["limit"] is None:
        return f"No quota configured ({status['used']} variables in use)."
    flag = " *** EXCEEDED ***" if status["exceeded"] else ""
    return (
        f"Quota: {status['used']}/{status['limit']} variables used, "
        f"{status['remaining']} remaining.{flag}"
    )
