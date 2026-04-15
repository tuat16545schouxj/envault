"""Key rotation support for envault vaults."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from envault.vault import VaultError, load_vault, save_vault
from envault.audit import record


class RotateError(Exception):
    """Raised when key rotation fails."""


def rotate_key(
    vault_path: Path,
    old_password: str,
    new_password: str,
    audit: bool = True,
) -> int:
    """Re-encrypt the vault with a new password.

    Loads the vault using *old_password*, then saves it using *new_password*.
    Returns the number of variables that were re-encrypted.

    Raises:
        RotateError: if the vault cannot be read or written.
    """
    if not old_password:
        raise RotateError("Old password must not be empty.")
    if not new_password:
        raise RotateError("New password must not be empty.")
    if old_password == new_password:
        raise RotateError("New password must differ from the old password.")

    try:
        variables = load_vault(vault_path, old_password)
    except VaultError as exc:
        raise RotateError(f"Failed to load vault with old password: {exc}") from exc

    try:
        save_vault(vault_path, variables, new_password)
    except VaultError as exc:
        raise RotateError(f"Failed to save vault with new password: {exc}") from exc

    count = len(variables)

    if audit:
        record(
            action="rotate",
            detail=f"Re-encrypted {count} variable(s) in {vault_path}",
        )

    return count
