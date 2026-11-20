"""Cached, strictly local Sentence Transformers encoder."""
from functools import lru_cache
from typing import Sequence

from careerlens.config import MODEL_NAME


class SemanticModelUnavailable(RuntimeError):
    """Raised when the embedding model has not been downloaded to the local cache."""


@lru_cache(maxsize=1)
def _load_model():
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise SemanticModelUnavailable("Install sentence-transformers to enable embedding similarity.") from exc
    try:
        # local_files_only is deliberate: analysis never makes network requests.
        return SentenceTransformer(MODEL_NAME, local_files_only=True)
    except Exception as exc:
        raise SemanticModelUnavailable(
            f"The local model {MODEL_NAME!r} is not available. Download it once using the README instructions."
        ) from exc


def encode(texts: Sequence[str]):
    """Return normalized embeddings for a batch of strings using the local model."""
    if not texts:
        return []
    return _load_model().encode(list(texts), normalize_embeddings=True, convert_to_numpy=True)
