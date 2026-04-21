"""Rename a variable key within a vault, preserving its value and metadata."""

from __future__ import annotations

from envault.vault import VaultError, load_vault, save_vault


class RenameError(Exception):
    """Raised when a rename operation fails."""


def rename_var(
    vault_path: str,
    password: str,
    old_key: str,
    new_key: str,
    *,
    overwrite: bool = False,
) -> None:
    """Rename *old_key* to *new_key* inside the vault at *vault_path*.

    Parameters
    ----------
    vault_path:
        Path to the encrypted vault file.
    password:
        Master password used to decrypt / re-encrypt the vault.
    old_key:
        The existing variable name.
    new_key:
        The desired new variable name.
    overwrite:
        When *True*, silently replace *new_key* if it already exists.
        When *False* (default), raise :class:`RenameError` instead.

    Raises
    ------
    RenameError
        If *old_key* does not exist, *new_key* already exists (and
        *overwrite* is ``False``), or either key is empty / invalid.
    VaultError
        Propagated from the vault layer on I/O or decryption failures.
    """
    if not old_key or not old_key.strip():
        raise RenameError("old_key must not be empty.")
    if not new_key or not new_key.strip():
        raise RenameError("new_key must not be empty.")
    if old_key == new_key:
        raise RenameError("old_key and new_key are identical — nothing to rename.")

    try:
        data = load_vault(vault_path, password)
    except VaultError:
        raise

    variables: dict[str, str] = data.get("variables", {})

    if old_key not in variables:
        raise RenameError(f"Key '{old_key}' not found in vault.")

    if new_key in variables and not overwrite:
        raise RenameError(
            f"Key '{new_key}' already exists. Use overwrite=True to replace it."
        )

    # Preserve insertion order: rebuild dict with new_key in old_key's position.
    updated: dict[str, str] = {}
    for k, v in variables.items():
        if k == old_key:
            updated[new_key] = v
        elif k != new_key:  # drop old new_key entry when overwriting
            updated[k] = v

    data["variables"] = updated
    save_vault(vault_path, password, data)
