"""Single orchestration entry point used by the Streamlit dashboard."""
from __future__ import annotations

from modules.database import save_analysis
from modules.gap_analyzer import analyze_skill_gaps
from modules.recommendation_engine import recommend_learning_path
from modules.resume_parser import parse_resume
from modules.scoring_engine import calculate_compatibility_score
from modules.semantic_matcher import semantic_comparison
from modules.skill_extractor import extract_job_description_skills
from careerlens.parsing.entity_extractor import extract_profile
from careerlens.config import ROLE_PROFILES_PATH
import json


def _role_description(job_title: str) -> str:
    """Resolve a title-only request to a curated role profile."""
    profiles = json.loads(ROLE_PROFILES_PATH.read_text(encoding="utf-8"))
    title = " ".join(job_title.casefold().replace("/", " ").replace("-", " ").split())
    for profile in profiles:
        name = " ".join(profile["name"].casefold().replace("/", " ").replace("-", " ").split())
        if title == name:
            return " ".join((profile["description"], "Required skills: " + ", ".join(profile["required"]), "Preferred skills: " + ", ".join(profile.get("preferred", []))))
    raise ValueError("No job description was provided, and this title is not in the built-in role catalog. Add a job description or choose a supported role title.")


def analyze_resume(uploaded_file, job_title: str, job_description: str, db_path=None) -> dict:
    """Run the local analysis stack and persist only non-resume-text results."""
    if not str(job_title).strip():
        raise ValueError("Enter a job title before starting the analysis.")
    job_description = str(job_description or "").strip()
    used_role_profile = not job_description
    if used_role_profile:
        job_description = _role_description(str(job_title).strip())

    parsed = parse_resume(uploaded_file)
    if not parsed.text:
        raise ValueError(parsed.warning or "The PDF has no extractable resume text.")
    required_skills = extract_job_description_skills(job_description)
    if not required_skills:
        raise ValueError("No known skills were found in this job description. Add recognizable skill names or aliases.")
    gap_analysis = analyze_skill_gaps(parsed.skills, required_skills)
    semantic = semantic_comparison(parsed.text, job_description)
    resume_profile = extract_profile(parsed.text)
    score = calculate_compatibility_score(
        skill_coverage=gap_analysis["skill_coverage"],
        semantic_relevance=semantic["similarity"],
        resume_profile=resume_profile,
        job_description=job_description,
    )
    recommendations = recommend_learning_path(gap_analysis, required_skills=[item["name"] for item in required_skills])
    skills = []
    for status, key in (("matched", "matched_skills"), ("missing", "missing_skills"), ("partial", "partially_matched_skills")):
        skills.extend({**item, "name": item["skill"], "status": status} for item in gap_analysis[key])

    # Summary intentionally excludes name, email, phone, and the original resume text.
    candidate_summary = {
        "estimated_experience_years": resume_profile.get("estimated_experience") or "Not detected",
        "degrees_detected": ", ".join(resume_profile.get("degrees", [])) or "Not detected",
        "resume_sections": ", ".join(parsed.sections.keys()) or "Not detected",
        "pdf_pages": parsed.page_count,
    }
    result = {
        "job_title": job_title.strip(),
        "used_role_profile": used_role_profile,
        "target_name": job_title.strip(),
        "filename": getattr(uploaded_file, "name", "Uploaded resume"),
        "candidate_summary": candidate_summary,
        "score": score,
        "overall_score": score["overall_score"],
        "component_scores": score["component_scores"],
        "semantic": semantic,
        "gap_analysis": gap_analysis,
        "skills": skills,
        "recommendations": recommendations,
        "sections": parsed.sections,
        "warnings": [parsed.warning] if parsed.warning else [],
        "disclaimer": score["disclaimer"],
    }
    result["analysis_id"] = save_analysis(result, db_path=db_path)
    result["id"] = result["analysis_id"]
    return result
