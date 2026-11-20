"""Dictionary-based skill extraction for resumes and job descriptions.

Add or edit rows in ``data/skills_database.csv`` to grow the vocabulary without
changing this module. Aliases in the CSV are separated with ``|``.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import TypedDict

import pandas as pd


SKILLS_DATABASE = Path(__file__).resolve().parents[2] / "data" / "skills_database.csv"
ALLOWED_CATEGORIES = {
    "Programming", "AI/ML", "Database", "Testing", "Cloud", "DevOps", "Frameworks", "Tools"
}


class ExtractedSkill(TypedDict):
    name: str
    category: str
    confidence: float
    evidence: str


@lru_cache(maxsize=1)
def _load_skills(path: str = str(SKILLS_DATABASE)) -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    """Load and validate the editable CSV dictionary once per process."""
    csv_path = Path(path)
    if not csv_path.is_file():
        raise FileNotFoundError(f"Skills dictionary not found: {csv_path}")
    frame = pd.read_csv(csv_path, keep_default_na=False, dtype=str)
    name_column = "skill" if "skill" in frame.columns else "canonical_name"
    required = {name_column, "category", "aliases"}
    if not required.issubset(frame.columns):
        raise ValueError("skills_database.csv must contain skill (or canonical_name), category, and aliases columns")

    entries: list[tuple[str, str, tuple[str, ...]]] = []
    seen: set[str] = set()
    for _, row in frame.iterrows():
        name = str(row[name_column]).strip()
        category = str(row["category"]).strip()
        if not name:
            continue
        if category not in ALLOWED_CATEGORIES:
            raise ValueError(f"Unsupported category {category!r} for skill {name!r}")
        key = name.casefold()
        if key in seen:
            raise ValueError(f"Duplicate canonical skill in dictionary: {name}")
        seen.add(key)
        aliases = tuple(
            alias.strip() for alias in str(row["aliases"]).split("|")
            if alias.strip() and alias.strip().casefold() != key
        )
        entries.append((name, category, aliases))
    return tuple(entries)


def _matches(alias: str, text: str) -> re.Match[str] | None:
    """Match a whole skill token; C is kept distinct from C++ and C#."""
    pattern = rf"(?<![A-Za-z0-9]){re.escape(alias)}(?![A-Za-z0-9])"
    for match in re.finditer(pattern, text, flags=re.IGNORECASE):
        if alias.casefold() == "c" and text[match.end():].startswith(("++", "#")):
            continue
        return match
    return None


def extract_skills(text: str, dictionary_path: str | Path | None = None) -> list[ExtractedSkill]:
    """Extract unique canonical skills from resume or job-description text.

    Matching is case-insensitive, alias-aware, and bounded by alphanumeric
    characters to avoid substring false positives (for example, C in "career").
    The same function can be used for either source; output remains deterministic
    and in the order of the curated CSV dictionary.
    """
    if not text or not text.strip():
        return []

    results: list[ExtractedSkill] = []
    dictionary = _load_skills(str(dictionary_path)) if dictionary_path else _load_skills()
    for name, category, aliases in dictionary:
        evidence = next((m.group(0) for term in (name, *aliases) if (m := _matches(term, text))), None)
        if evidence is not None:
            results.append({"name": name, "category": category, "confidence": 1.0, "evidence": evidence})
    return results


def extract_resume_skills(resume_text: str, dictionary_path: str | Path | None = None) -> list[ExtractedSkill]:
    """Named convenience wrapper for resume text."""
    return extract_skills(resume_text, dictionary_path)


def extract_job_description_skills(job_description: str, dictionary_path: str | Path | None = None) -> list[ExtractedSkill]:
    """Named convenience wrapper for job-description text."""
    return extract_skills(job_description, dictionary_path)
