"""Explainable exact and semantic skill-gap classification."""
from collections.abc import Mapping, Sequence


def analyze_gaps(
    found: list[dict],
    required: Sequence[str],
    preferred: Sequence[str] | None = None,
    similarities: Mapping[str, tuple[str, float]] | None = None,
    partial_threshold: float = .72,
) -> list[dict]:
    """Classify target skills as matched, partial (related evidence), or missing.

    ``similarities`` maps each target skill to its closest resume skill and cosine
    score. Supplying it is optional so callers can still do taxonomy-only checks.
    """
    have = {skill["name"].casefold(): skill for skill in found}
    preferred = list(preferred or [])
    required = list(required)
    targets = list(dict.fromkeys([*required, *preferred]))
    result = []
    for name in targets:
        exact = have.get(name.casefold())
        related_name, related_score = (similarities or {}).get(name, ("", 0.0))
        related = have.get(related_name.casefold())
        if exact:
            status, confidence, evidence = "matched", 1.0, exact.get("evidence", name)
        elif related_score >= partial_threshold:
            status, confidence = "partial", float(related_score)
            evidence = f"Related resume skill: {related_name}"
        else:
            status, confidence, evidence = "missing", 0.0, ""
        result.append({
            "name": name,
            "status": status,
            "confidence": round(confidence, 3),
            "category": exact.get("category", "General") if exact else related.get("category", "General") if related else "General",
            "required": name in required,
            "evidence": evidence,
        })
    return result
