"""Copy variables between profiles or vaults."""

from __future__ import annotations

from typing import Optional

from envault.vault import VaultError, load_vault, save_vault


class CopyError(Exception):
    pass


def copy_vars(
    src_path: str,
    dst_path: str,
    src_password: str,
    dst_password: str,
    keys: Optional[list[str]] = None,
    overwrite: bool = False,
) -> dict[str, str]:
    """Copy variables from src vault to dst vault.

    Args:
        src_path: Path to source vault file.
        dst_path: Path to destination vault file.
        src_password: Password for source vault.
        dst_password: Password for destination vault.
        keys: Optional list of keys to copy. If None, copy all.
        overwrite: Whether to overwrite existing keys in destination.

    Returns:
        Dict of keys that were actually copied.

    Raises:
        CopyError: On missing keys or overwrite conflicts.
    """
    try:
        src_data = load_vault(src_path, src_password)
    except VaultError as e:
        raise CopyError(f"Failed to load source vault: {e}") from e

    try:
        dst_data = load_vault(dst_path, dst_password)
    except FileNotFoundError:
        dst_data = {}
    except VaultError as e:
        raise CopyError(f"Failed to load destination vault: {e}") from e

    if keys is None:
        keys = list(src_data.keys())

    missing = [k for k in keys if k not in src_data]
    if missing:
        raise CopyError(f"Keys not found in source vault: {', '.join(missing)}")

    conflicts = [k for k in keys if k in dst_data and not overwrite]
    if conflicts:
        raise CopyError(
            f"Keys already exist in destination (use --overwrite): {', '.join(conflicts)}"
        )

    copied = {k: src_data[k] for k in keys}
    dst_data.update(copied)

    try:
        save_vault(dst_path, dst_password, dst_data)
    except VaultError as e:
        raise CopyError(f"Failed to save destination vault: {e}") from e

    return copied
