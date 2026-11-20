"""Rule-based learning recommendations backed by the editable CSV resource set."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from careerlens.config import DATA_DIR
from careerlens.skills.extractor import SKILLS_DATABASE

LEARNING_RESOURCES = DATA_DIR / "learning_resources.csv"
LEVELS = ("Beginner", "Intermediate", "Advanced")
PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}


def _names(items) -> list[tuple[str, dict]]:
    output, seen = [], set()
    for item in items or []:
        data = item if isinstance(item, dict) else {"skill": str(item)}
        name = str(data.get("skill", data.get("name", ""))).strip()
        if name and name.casefold() not in seen:
            output.append((name, data))
            seen.add(name.casefold())
    return output


def _canonicalize(skill: str, skills_csv: pd.DataFrame) -> str:
    lookup = {str(row.skill).casefold(): str(row.skill) for row in skills_csv.itertuples()}
    for row in skills_csv.itertuples():
        aliases = [part.strip().casefold() for part in str(row.aliases).split("|") if part.strip()]
        if skill.casefold() in aliases:
            return str(row.skill)
    return lookup.get(skill.casefold(), skill)


def recommend_learning_path(
    gap_analysis: dict,
    required_skills: list[str] | None = None,
    resources_path: str | Path | None = None,
    skills_path: str | Path | None = None,
) -> dict:
    """Create relevant, prioritized recommendations and a level-grouped roadmap.

    Missing required skills are High priority, partial required skills Medium,
    and optional gaps Low. Only a resource whose canonical skill exactly matches
    the gap (or its dictionary alias) is attached; unmatched gaps are clearly
    marked and never receive an unrelated course.
    """
    resource_file = Path(resources_path or LEARNING_RESOURCES)
    skill_file = Path(skills_path or SKILLS_DATABASE)
    if not resource_file.is_file():
        raise FileNotFoundError(f"Learning resources file not found: {resource_file}")
    if not skill_file.is_file():
        raise FileNotFoundError(f"Skills dictionary not found: {skill_file}")
    resource_df = pd.read_csv(resource_file, keep_default_na=False)
    required_columns = {"skill", "resource_name", "resource_url", "difficulty", "estimated_hours", "project_idea"}
    if not required_columns.issubset(resource_df.columns):
        raise ValueError("learning_resources.csv is missing one or more required columns")
    skills_df = pd.read_csv(skill_file, keep_default_na=False)

    required_set = {str(name).casefold() for name in (required_skills or [])}
    entries = []
    for skill, details in _names(gap_analysis.get("missing_skills", [])):
        entries.append((skill, "High" if not required_set or skill.casefold() in required_set else "Low", "Missing", details))
    for skill, details in _names(gap_analysis.get("partially_matched_skills", [])):
        entries.append((skill, "Medium" if not required_set or skill.casefold() in required_set else "Low", "Partial", details))

    recommendations = []
    for skill, priority, status, details in entries:
        canonical = _canonicalize(skill, skills_df)
        rows = resource_df[resource_df["skill"].astype(str).str.casefold() == canonical.casefold()]
        if rows.empty:
            recommendations.append({
                "skill": skill, "priority": priority, "match_status": status,
                "level": None, "resource_name": None, "resource_url": None,
                "estimated_hours": None, "project_idea": None,
                "explanation": "No curated resource is available for this exact skill yet.",
            })
            continue
        row = rows.iloc[0]
        level = str(row["difficulty"]).title()
        if level not in LEVELS:
            raise ValueError(f"Invalid difficulty {row['difficulty']!r} for {canonical!r}")
        try:
            hours = max(1, int(float(row["estimated_hours"])))
        except (TypeError, ValueError):
            raise ValueError(f"Invalid estimated_hours for resource {row['resource_name']!r}")
        recommendations.append({
            "skill": canonical, "priority": priority, "match_status": status,
            "level": level, "resource_name": str(row["resource_name"]),
            "resource_url": str(row["resource_url"]), "estimated_hours": hours,
            "project_idea": str(row["project_idea"]),
            "explanation": details.get("explanation", details.get("evidence", f"{status} skill in the job requirement.")),
        })

    recommendations.sort(key=lambda item: (PRIORITY_ORDER[item["priority"]], item["estimated_hours"] or 10**6, item["skill"].casefold()))
    roadmap = {level: [item for item in recommendations if item["level"] == level] for level in LEVELS}
    return {
        "recommendations": recommendations,
        "roadmap_by_level": roadmap,
        "total_estimated_hours": sum(item["estimated_hours"] or 0 for item in recommendations),
    }


def recommend_for_gaps(missing_skills, partially_matched_skills=None, **kwargs) -> dict:
    """Convenience API when callers hold the two gap lists separately."""
    return recommend_learning_path({
        "missing_skills": missing_skills,
        "partially_matched_skills": partially_matched_skills or [],
    }, **kwargs)
