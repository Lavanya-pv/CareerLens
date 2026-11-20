"""Skill-gap classification with explicit evidence and coverage denominator."""
from __future__ import annotations

from collections.abc import Sequence

from modules.semantic_matcher import batch_similarity


def _skill_name(value) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        return str(value.get("name", value.get("skill", ""))).strip()
    raise TypeError("Skills must be strings or dictionaries with a name/skill field.")


def _unique(values: Sequence) -> tuple[list[str], dict[str, dict]]:
    output, seen, metadata = [], set(), {}
    for value in values:
        name = _skill_name(value)
        if name and name.casefold() not in seen:
            seen.add(name.casefold())
            output.append(name)
            metadata[name.casefold()] = value if isinstance(value, dict) else {}
    return output, metadata


def analyze_skill_gaps(
    resume_skills: Sequence[str | dict],
    required_skills: Sequence[str | dict],
    similarity_threshold: float = .72,
) -> dict:
    """Partition target skills into direct matches, missing, and partial matches.

    Coverage is the percentage of unique required skills found by direct exact
    canonical-name match; partial semantic matches are reported separately and
    do not inflate coverage.
    """
    if not 0.0 <= similarity_threshold <= 1.0:
        raise ValueError("similarity_threshold must be between 0 and 1.")
    resume, _resume_metadata = _unique(resume_skills)
    required, required_metadata = _unique(required_skills)
    resume_by_key = {name.casefold(): name for name in resume}
    unmatched = [name for name in required if name.casefold() not in resume_by_key]
    similarity_frame = batch_similarity(resume, unmatched) if resume and unmatched else None
    nearest: dict[str, tuple[str, float]] = {}
    if similarity_frame is not None and not similarity_frame.empty:
        for requirement, group in similarity_frame.groupby("job_requirement"):
            row = group.loc[group["similarity"].idxmax()]
            nearest[str(requirement).casefold()] = (str(row["resume_statement"]), float(row["similarity"]))

    matched, missing, partial = [], [], []
    for required_name in required:
        direct = resume_by_key.get(required_name.casefold())
        category = required_metadata.get(required_name.casefold(), {}).get("category", "General")
        if direct:
            matched.append({"skill": required_name, "category": category, "evidence": f"Direct resume skill match: {direct}", "similarity": 1.0})
            continue
        related_name, score = nearest.get(required_name.casefold(), ("", 0.0))
        if related_name and score >= similarity_threshold:
            partial.append({
                "skill": required_name,
                "category": category,
                "related_resume_skill": related_name,
                "similarity": round(score, 4),
                "explanation": f"Resume lists {related_name!r}, with similarity {score:.0%}; it is related evidence, not an exact match.",
            })
        else:
            missing.append({
                "skill": required_name,
                "category": category,
                "closest_resume_skill": related_name or None,
                "similarity": round(score, 4),
                "explanation": "No direct match or sufficiently similar resume skill was found.",
            })

    coverage = (len(matched) / len(required) * 100.0) if required else 0.0
    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "partially_matched_skills": partial,
        "required_skill_count": len(required),
        "directly_matched_count": len(matched),
        "skill_coverage": round(coverage, 2),
        "coverage_denominator": "unique required skills",
        "similarity_threshold": similarity_threshold,
    }
