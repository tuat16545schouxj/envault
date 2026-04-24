"""Promote variables from one vault profile/environment to another."""

from __future__ import annotations

from typing import Optional

from envault.vault import VaultError, load_vault, save_vault


class PromoteError(Exception):
    """Raised when a promotion operation fails."""


def promote_vars(
    src_vault_path: str,
    src_password: str,
    dst_vault_path: str,
    dst_password: str,
    keys: Optional[list[str]] = None,
    overwrite: bool = False,
    dry_run: bool = False,
) -> dict[str, str]:
    """Promote variables from src vault to dst vault.

    Args:
        src_vault_path: Path to the source vault file.
        src_password: Password for the source vault.
        dst_vault_path: Path to the destination vault file.
        dst_password: Password for the destination vault.
        keys: Specific keys to promote; promotes all if None.
        overwrite: If True, overwrite existing keys in dst.
        dry_run: If True, return planned changes without writing.

    Returns:
        A dict of {key: value} pairs that were (or would be) promoted.

    Raises:
        PromoteError: If a key is missing from src or a conflict is found.
    """
    try:
        src_data = load_vault(src_vault_path, src_password)
    except VaultError as exc:
        raise PromoteError(f"Failed to load source vault: {exc}") from exc

    try:
        dst_data = load_vault(dst_vault_path, dst_password)
    except FileNotFoundError:
        dst_data = {}
    except VaultError as exc:
        raise PromoteError(f"Failed to load destination vault: {exc}") from exc

    target_keys = keys if keys is not None else list(src_data.keys())

    missing = [k for k in target_keys if k not in src_data]
    if missing:
        raise PromoteError(
            f"Key(s) not found in source vault: {', '.join(sorted(missing))}"
        )

    conflicts = [k for k in target_keys if k in dst_data and not overwrite]
    if conflicts:
        raise PromoteError(
            f"Key(s) already exist in destination (use overwrite=True): "
            f"{', '.join(sorted(conflicts))}"
        )

    promoted = {k: src_data[k] for k in target_keys}

    if not dry_run:
        dst_data.update(promoted)
        try:
            save_vault(dst_vault_path, dst_password, dst_data)
        except VaultError as exc:
            raise PromoteError(f"Failed to save destination vault: {exc}") from exc

    return promoted
