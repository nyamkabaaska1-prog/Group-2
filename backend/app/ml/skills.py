"""Skill extraction from job text.

Uses a curated taxonomy with alias regex matching. The taxonomy lives in
app/data/skills_taxonomy.json so it is easy to extend without code changes.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

_TAXONOMY_PATH = Path(__file__).resolve().parent.parent / "data" / "skills_taxonomy.json"


@lru_cache(maxsize=1)
def _load() -> dict:
    with _TAXONOMY_PATH.open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _compiled() -> list[tuple[str, str, re.Pattern]]:
    out: list[tuple[str, str, re.Pattern]] = []
    for category, skills in _load().items():
        for canonical, aliases in skills.items():
            patterns = [re.escape(canonical)] + list(aliases)
            joined = "|".join(patterns)
            # Short canonical names (R, Go, C, etc.) are matched case-sensitively
            # to avoid runaway false positives like " r " or "go" inside prose.
            flags = 0 if len(canonical) <= 2 else re.IGNORECASE
            pattern = re.compile(rf"(?<![a-zA-Z0-9+#]){joined}(?![a-zA-Z0-9])", flags)
            out.append((canonical, category, pattern))
    return out


def all_skills() -> list[tuple[str, str]]:
    """Return list of (canonical_name, category) tuples for the full taxonomy."""
    return [(name, cat) for name, cat, _ in _compiled()]


def extract(text: str) -> list[str]:
    """Return the canonical skill names mentioned in text, de-duplicated."""
    if not text:
        return []
    blob = f" {text} "
    found: list[str] = []
    seen: set[str] = set()
    for canonical, _cat, pattern in _compiled():
        if canonical in seen:
            continue
        if pattern.search(blob):
            found.append(canonical)
            seen.add(canonical)
    return found
