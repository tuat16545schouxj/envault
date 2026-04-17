"""Lint vault variables for common issues."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from envault.vault import load_vault


class LintError(Exception):
    pass


@dataclass
class LintIssue:
    key: str
    code: str
    message: str

    def to_dict(self) -> dict:
        return {"key": self.key, "code": self.code, "message": self.message}


_VALID_KEY_RE = re.compile(r'^[A-Z_][A-Z0-9_]*$')


def lint_vars(vault_path: str, password: str) -> List[LintIssue]:
    """Return a list of lint issues found in the vault."""
    try:
        data = load_vault(vault_path, password)
    except Exception as exc:
        raise LintError(str(exc)) from exc

    variables: dict = data.get("variables", {})
    issues: List[LintIssue] = []

    for key, value in variables.items():
        # E001: key not uppercase / invalid characters
        if not _VALID_KEY_RE.match(key):
            issues.append(LintIssue(
                key=key,
                code="E001",
                message=f"Key '{key}' does not match pattern [A-Z_][A-Z0-9_]*",
            ))

        # E002: empty value
        if value == "":
            issues.append(LintIssue(
                key=key,
                code="E002",
                message=f"Key '{key}' has an empty value",
            ))

        # W001: value looks like it contains an unexpanded variable reference
        if re.search(r'\$[A-Z_][A-Z0-9_]*', value):
            issues.append(LintIssue(
                key=key,
                code="W001",
                message=f"Key '{key}' value may contain an unexpanded shell variable",
            ))

        # W002: suspiciously short secret (less than 8 chars) for keys hinting at secrets
        secret_hint = re.search(r'(SECRET|PASSWORD|TOKEN|KEY)', key)
        if secret_hint and 0 < len(value) < 8:
            issues.append(LintIssue(
                key=key,
                code="W002",
                message=f"Key '{key}' looks like a secret but has a very short value",
            ))

    return sorted(issues, key=lambda i: (i.key, i.code))
