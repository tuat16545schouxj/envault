"""Search/filter variables across the vault."""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from typing import Dict, List, Optional

from envault.vault import VaultError, load_vault


class SearchError(Exception):
    pass


@dataclass
class SearchResult:
    key: str
    value: str

    def to_dict(self) -> Dict[str, str]:
        return {"key": self.key, "value": self.value}


def search_vars(
    vault_path: str,
    password: str,
    pattern: str,
    *,
    search_values: bool = False,
    case_sensitive: bool = False,
) -> List[SearchResult]:
    """Return vault entries whose key (or optionally value) matches *pattern*.

    *pattern* supports shell-style wildcards via :func:`fnmatch`.
    """
    try:
        data = load_vault(vault_path, password)
    except VaultError as exc:
        raise SearchError(str(exc)) from exc

    if not case_sensitive:
        pattern = pattern.lower()

    results: List[SearchResult] = []
    for key, value in sorted(data.items()):
        hay_key = key if case_sensitive else key.lower()
        hay_val = value if case_sensitive else value.lower()

        matched = fnmatch(hay_key, pattern)
        if not matched and search_values:
            matched = fnmatch(hay_val, pattern)

        if matched:
            results.append(SearchResult(key=key, value=value))

    return results
