"""Embedding-first similarity with a fully local TF-IDF fallback."""
from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from careerlens.embeddings.encoder import encode


def cosine_similarity(left, right) -> np.ndarray:
    """Cosine similarity for already normalized or arbitrary vector matrices."""
    left, right = np.asarray(left), np.asarray(right)
    left = left / np.maximum(np.linalg.norm(left, axis=1, keepdims=True), 1e-12)
    right = right / np.maximum(np.linalg.norm(right, axis=1, keepdims=True), 1e-12)
    return left @ right.T


def similarity_matrix(left: Sequence[str], right: Sequence[str]) -> tuple[np.ndarray, str]:
    """Compare text batches; prefer MiniLM and gracefully fall back to TF-IDF.

    Returns (scores, method). A score is a cosine similarity from 0 to 1.
    Neither implementation accesses a hosted service.
    """
    if not left or not right:
        return np.zeros((len(left), len(right))), "empty"
    try:
        vectors = encode([*left, *right])
        return cosine_similarity(vectors[:len(left)], vectors[len(left):]), "all-MiniLM-L6-v2"
    except Exception:
        # TF-IDF keeps the app useful if the optional local model is not installed
        # or has not yet been downloaded. It is a lexical baseline, not an embedding.
        from sklearn.feature_extraction.text import TfidfVectorizer

        try:
            vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
            combined = vectorizer.fit_transform([*left, *right])
            return (combined[:len(left)] @ combined[len(left):].T).toarray(), "tfidf-fallback"
        except ValueError:
            return np.zeros((len(left), len(right))), "tfidf-fallback"


def text_similarity(left: str, right: str) -> tuple[float, str]:
    """Return one text-to-text similarity and identify the method used."""
    scores, method = similarity_matrix([left], [right])
    return float(scores[0, 0]), method
