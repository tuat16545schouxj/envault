"""Watch a vault file for changes and trigger a callback."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Callable, Optional


class WatchError(Exception):
    """Raised when vault watching fails."""


def _file_hash(path: Path) -> str:
    """Return the MD5 hex-digest of *path*, or empty string if missing."""
    try:
        return hashlib.md5(path.read_bytes()).hexdigest()
    except FileNotFoundError:
        return ""


def watch_vault(
    vault_path: str,
    callback: Callable[[str], None],
    *,
    interval: float = 1.0,
    max_iterations: Optional[int] = None,
) -> None:
    """Poll *vault_path* every *interval* seconds and call *callback* on change.

    Parameters
    ----------
    vault_path:
        Path to the encrypted vault file to watch.
    callback:
        Callable invoked with the vault path string whenever a change is
        detected.  Exceptions raised inside the callback are propagated.
    interval:
        Polling interval in seconds (default 1.0).
    max_iterations:
        If set, stop after this many polling loops (useful for testing).
    """
    if interval <= 0:
        raise WatchError("interval must be a positive number")

    path = Path(vault_path)
    last_hash = _file_hash(path)
    iterations = 0

    while True:
        if max_iterations is not None and iterations >= max_iterations:
            break

        time.sleep(interval)
        current_hash = _file_hash(path)

        if current_hash != last_hash:
            last_hash = current_hash
            callback(vault_path)

        iterations += 1
