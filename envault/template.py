"""Template rendering: substitute vault variables into template strings/files."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Optional

from envault.vault import load_vault


class TemplateError(Exception):
    pass


_PATTERN = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


def render_string(template: str, variables: Dict[str, str], strict: bool = True) -> str:
    """Replace {{VAR}} placeholders with values from variables dict."""
    missing: list[str] = []

    def replacer(m: re.Match) -> str:
        key = m.group(1)
        if key in variables:
            return variables[key]
        missing.append(key)
        return m.group(0)

    result = _PATTERN.sub(replacer, template)
    if strict and missing:
        raise TemplateError(f"Undefined variables in template: {', '.join(sorted(missing))}")
    return result


def render_file(
    template_path: Path,
    vault_path: Path,
    password: str,
    output_path: Optional[Path] = None,
    strict: bool = True,
) -> str:
    """Load vault, render a template file, optionally write output."""
    if not template_path.exists():
        raise TemplateError(f"Template file not found: {template_path}")
    variables = load_vault(vault_path, password)
    template = template_path.read_text(encoding="utf-8")
    rendered = render_string(template, variables, strict=strict)
    if output_path is not None:
        output_path.write_text(rendered, encoding="utf-8")
    return rendered
