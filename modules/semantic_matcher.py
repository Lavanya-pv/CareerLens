"""Local MiniLM embedding and cosine-similarity helpers."""
from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from careerlens.embeddings.similarity import similarity_matrix, text_similarity


def _validate_text(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string.")
    return value.strip()


def calculate_semantic_similarity(text_a: str, text_b: str) -> float:
    """Return a 0..1 similarity. Uses cached local MiniLM when available.

    If the model has not been downloaded, the engine uses its offline TF-IDF
    fallback; no hosted service is contacted.
    """
    left, right = _validate_text(text_a, "text_a"), _validate_text(text_b, "text_b")
    if not left or not right:
        return 0.0
    score, _method = text_similarity(left, right)
    return max(0.0, min(1.0, float(score)))


def semantic_comparison(text_a: str, text_b: str) -> dict[str, float | str]:
    """Return similarity and the local method used, for explainable UI output."""
    left, right = _validate_text(text_a, "text_a"), _validate_text(text_b, "text_b")
    if not left or not right:
        return {"similarity": 0.0, "method": "empty-input"}
    score, method = text_similarity(left, right)
    return {"similarity": max(0.0, min(1.0, float(score))), "method": method}


def batch_similarity(
    resume_statements: Sequence[str],
    job_requirements: Sequence[str],
) -> pd.DataFrame:
    """Compare each resume statement to each requirement in one batch.

    The returned dataframe has columns ``resume_statement``, ``job_requirement``,
    and ``similarity``. Empty inputs produce an empty dataframe with those columns.
    """
    columns = ["resume_statement", "job_requirement", "similarity"]
    left = [_validate_text(item, "resume statement") for item in resume_statements]
    right = [_validate_text(item, "job requirement") for item in job_requirements]
    if not left or not right:
        return pd.DataFrame(columns=columns)
    scores, _method = similarity_matrix(left, right)
    rows = [
        {"resume_statement": statement, "job_requirement": requirement, "similarity": float(scores[i, j])}
        for i, statement in enumerate(left)
        for j, requirement in enumerate(right)
    ]
    return pd.DataFrame(rows, columns=columns)


def compare_resume_to_job_description(resume_text: str, job_description: str) -> float:
    """Convenience wrapper for whole-document semantic relevance."""
    return calculate_semantic_similarity(resume_text, job_description)
