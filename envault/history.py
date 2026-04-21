"""Variable change history tracking for envault."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

HISTORY_KEY = "__history__"


class HistoryError(Exception):
    """Raised when a history operation fails."""


@dataclass
class HistoryEntry:
    key: str
    old_value: Optional[str]
    new_value: Optional[str]
    action: str  # 'set' | 'delete'
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "action": self.action,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HistoryEntry":
        return cls(
            key=data["key"],
            old_value=data.get("old_value"),
            new_value=data.get("new_value"),
            action=data["action"],
            timestamp=data["timestamp"],
        )


def record_change(
    vault: dict,
    key: str,
    old_value: Optional[str],
    new_value: Optional[str],
    action: str,
) -> None:
    """Append a change entry to the vault's history log."""
    entries: List[dict] = vault.setdefault(HISTORY_KEY, [])
    entry = HistoryEntry(
        key=key, old_value=old_value, new_value=new_value, action=action
    )
    entries.append(entry.to_dict())


def get_history(
    vault: dict, key: Optional[str] = None, limit: int = 50
) -> List[HistoryEntry]:
    """Return history entries, optionally filtered by key."""
    raw: List[dict] = vault.get(HISTORY_KEY, [])
    entries = [HistoryEntry.from_dict(r) for r in raw]
    if key:
        entries = [e for e in entries if e.key == key]
    return entries[-limit:]


def clear_history(vault: dict, key: Optional[str] = None) -> int:
    """Clear history entries. Returns number of entries removed."""
    raw: List[dict] = vault.get(HISTORY_KEY, [])
    if key is None:
        count = len(raw)
        vault[HISTORY_KEY] = []
        return count
    before = len(raw)
    vault[HISTORY_KEY] = [r for r in raw if r.get("key") != key]
    return before - len(vault[HISTORY_KEY])
