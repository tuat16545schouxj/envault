"""Audit log for tracking vault operations."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

AUDIT_LOG_ENV = "ENVAULT_AUDIT_LOG"
DEFAULT_AUDIT_LOG = ".envault_audit.log"


class AuditEntry:
    """Represents a single audit log entry."""

    def __init__(self, action: str, key: Optional[str], user: str, details: str = ""):
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.action = action
        self.key = key
        self.user = user
        self.details = details

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "action": self.action,
            "key": self.key,
            "user": self.user,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        entry = cls(
            action=data["action"],
            key=data.get("key"),
            user=data["user"],
            details=data.get("details", ""),
        )
        entry.timestamp = data["timestamp"]
        return entry


def _get_log_path(log_path: Optional[str] = None) -> Path:
    path = log_path or os.environ.get(AUDIT_LOG_ENV, DEFAULT_AUDIT_LOG)
    return Path(path)


def _get_user() -> str:
    return os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"


def record(action: str, key: Optional[str] = None, details: str = "", log_path: Optional[str] = None) -> None:
    """Append an audit entry to the log file."""
    entry = AuditEntry(action=action, key=key, user=_get_user(), details=details)
    path = _get_log_path(log_path)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry.to_dict()) + "\n")


def read_log(log_path: Optional[str] = None) -> List[AuditEntry]:
    """Read all audit entries from the log file."""
    path = _get_log_path(log_path)
    if not path.exists():
        return []
    entries: List[AuditEntry] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                entries.append(AuditEntry.from_dict(json.loads(line)))
    return entries


def clear_log(log_path: Optional[str] = None) -> None:
    """Remove the audit log file if it exists."""
    path = _get_log_path(log_path)
    if path.exists():
        path.unlink()
