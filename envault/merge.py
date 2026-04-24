"""Merge variables from one vault into another with configurable conflict resolution."""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from envault.vault import VaultError, load_vault, save_vault


class MergeError(Exception):
    """Raised when a merge operation fails."""


class ConflictStrategy(str, Enum):
    KEEP_DST = "keep_dst"   # keep destination value on conflict
    KEEP_SRC = "keep_src"   # overwrite with source value on conflict
    RAISE    = "raise"      # raise an error on any conflict


class MergeResult:
    def __init__(
        self,
        added: List[str],
        overwritten: List[str],
        skipped: List[str],
    ) -> None:
        self.added = sorted(added)
        self.overwritten = sorted(overwritten)
        self.skipped = sorted(skipped)

    def to_dict(self) -> Dict[str, List[str]]:
        return {
            "added": self.added,
            "overwritten": self.overwritten,
            "skipped": self.skipped,
        }


def merge_vaults(
    src_path: str,
    src_password: str,
    dst_path: str,
    dst_password: str,
    keys: Optional[List[str]] = None,
    strategy: ConflictStrategy = ConflictStrategy.KEEP_DST,
) -> MergeResult:
    """Merge variables from *src* vault into *dst* vault.

    Args:
        src_path: Path to the source vault file.
        src_password: Password for the source vault.
        dst_path: Path to the destination vault file.
        dst_password: Password for the destination vault.
        keys: Explicit list of keys to merge; merges all if None.
        strategy: How to handle keys that exist in both vaults.

    Returns:
        A :class:`MergeResult` describing what changed.

    Raises:
        MergeError: On conflict when strategy is RAISE, or on vault errors.
    """
    try:
        src_vars: Dict[str, str] = load_vault(src_path, src_password)
    except VaultError as exc:
        raise MergeError(f"Cannot load source vault: {exc}") from exc

    try:
        dst_vars: Dict[str, str] = load_vault(dst_path, dst_password)
    except FileNotFoundError:
        dst_vars = {}
    except VaultError as exc:
        raise MergeError(f"Cannot load destination vault: {exc}") from exc

    candidates = keys if keys is not None else list(src_vars.keys())
    missing = [k for k in candidates if k not in src_vars]
    if missing:
        raise MergeError(f"Keys not found in source vault: {', '.join(sorted(missing))}")

    added: List[str] = []
    overwritten: List[str] = []
    skipped: List[str] = []

    for key in candidates:
        value = src_vars[key]
        if key in dst_vars:
            if strategy == ConflictStrategy.RAISE:
                raise MergeError(f"Conflict on key '{key}': already exists in destination vault")
            elif strategy == ConflictStrategy.KEEP_SRC:
                dst_vars[key] = value
                overwritten.append(key)
            else:  # KEEP_DST
                skipped.append(key)
        else:
            dst_vars[key] = value
            added.append(key)

    try:
        save_vault(dst_path, dst_password, dst_vars)
    except VaultError as exc:
        raise MergeError(f"Cannot save destination vault: {exc}") from exc

    return MergeResult(added=added, overwritten=overwritten, skipped=skipped)
