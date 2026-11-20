"""Transparent 50/30/20 compatibility scoring (not a hiring probability)."""
from __future__ import annotations

import re
from collections.abc import Mapping


DEFAULT_WEIGHTS = {"required_skill_coverage": .50, "semantic_relevance": .30, "experience_qualifications": .20}
_DEGREE_TERMS = ("bachelor", "b.sc", "b.s.", "b.tech", "master", "m.sc", "m.s.", "m.tech", "ph.d", "phd", "mba")


def _score_value(value: float, label: str) -> float:
    number = float(value)
    if not 0.0 <= number <= 100.0:
        raise ValueError(f"{label} must be between 0 and 100 (or 0 and 1).")
    return number * 100.0 if number <= 1.0 else number


def _experience_and_qualification(resume_profile: Mapping | None, job_description: str) -> tuple[float, list[str]]:
    profile = resume_profile or {}
    explanations: list[str] = []
    resume_years = profile.get("estimated_experience", profile.get("years_experience"))
    target_years_match = re.search(r"\b(\d+)\s*\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:relevant\s+)?experience\b", job_description, re.I)
    sub_scores = []

    if target_years_match:
        target_years = int(target_years_match.group(1))
        if resume_years is None:
            sub_scores.append(0.0)
            explanations.append(f"The role asks for {target_years}+ years; resume experience duration was not available (0/100 for this criterion).")
        else:
            years_score = min(100.0, max(0.0, float(resume_years) / max(1, target_years) * 100.0))
            sub_scores.append(years_score)
            explanations.append(f"Experience: {resume_years} estimated years against {target_years}+ requested ({years_score:.0f}/100).")
    else:
        sub_scores.append(50.0)
        explanations.append("The job description has no explicit years-of-experience requirement; this criterion receives a neutral 50/100.")

    required_degrees = [term for term in _DEGREE_TERMS if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", job_description, re.I)]
    resume_degrees = [str(item).casefold() for item in profile.get("degrees", [])]
    if required_degrees:
        if not resume_degrees:
            degree_score = 0.0
            explanations.append("The job lists a degree qualification, but no degree was detected in the resume (0/100 for this criterion).")
        else:
            matches = any(any(term in degree for term in required_degrees) for degree in resume_degrees)
            degree_score = 100.0 if matches else 0.0
            explanations.append(f"Degree requirement: {'a matching degree was found' if matches else 'no matching degree was found'} ({degree_score:.0f}/100).")
        sub_scores.append(degree_score)
    else:
        sub_scores.append(50.0)
        explanations.append("No specific degree is requested; qualifications receive a neutral 50/100.")

    return sum(sub_scores) / len(sub_scores), explanations


def calculate_compatibility_score(
    skill_coverage: float,
    semantic_relevance: float,
    resume_profile: Mapping | None = None,
    job_description: str = "",
    weights: Mapping[str, float] | None = None,
) -> dict:
    """Blend normalized inputs and rule-based experience/qualification relevance.

    Input component values may be fractions (0..1) or percentages (0..100).
    Missing job criteria receive a neutral 50; a missing candidate value for an
    explicit job requirement receives 0 rather than being silently treated as a fit.
    """
    skill_score = _score_value(skill_coverage, "skill_coverage")
    semantic_score = _score_value(semantic_relevance, "semantic_relevance")
    experience_score, experience_explanations = _experience_and_qualification(resume_profile, job_description or "")
    component_scores = {
        "required_skill_coverage": round(skill_score, 2),
        "semantic_relevance": round(semantic_score, 2),
        "experience_qualifications": round(experience_score, 2),
    }
    active_weights = dict(weights or DEFAULT_WEIGHTS)
    if set(active_weights) != set(DEFAULT_WEIGHTS):
        raise ValueError(f"weights must contain exactly: {', '.join(DEFAULT_WEIGHTS)}")
    if any(float(value) < 0 for value in active_weights.values()) or sum(map(float, active_weights.values())) <= 0:
        raise ValueError("weights must be non-negative and have a positive sum.")
    total_weight = sum(map(float, active_weights.values()))
    normalized_weights = {key: float(value) / total_weight for key, value in active_weights.items()}
    score = round(sum(component_scores[key] * normalized_weights[key] for key in component_scores), 2)
    explanations = {
        "required_skill_coverage": f"{component_scores['required_skill_coverage']:.1f} × {normalized_weights['required_skill_coverage']:.0%} weight.",
        "semantic_relevance": f"{component_scores['semantic_relevance']:.1f} × {normalized_weights['semantic_relevance']:.0%} weight.",
        "experience_qualifications": experience_explanations,
    }
    return {
        "overall_score": score,
        "component_scores": component_scores,
        "weights": normalized_weights,
        "explanations": explanations,
        "disclaimer": "Indicative compatibility measure only; this is not a probability of getting hired.",
    }
