"""Multilingual embedding service for SchemeSaathi.

Loads multilingual embedding models (default: intfloat/multilingual-e5-small)
and manages required 'query: ' and 'passage: ' prefixes for asymmetric retrieval.
All generated vectors are L2-normalized so inner product equals cosine similarity.
"""

import logging
import os
from typing import List, Optional
import numpy as np
from app.config import get_settings

# Prefer cached local models and prevent network timeout delays if offline
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

logger = logging.getLogger("schemesaathi.embeddings")

# Global singleton model cache
_model_instance = None


def is_e5_model(model_name: str) -> bool:
    """Check if the configured model is an E5 variant requiring prefix formatting."""
    return "e5" in model_name.lower()


def get_embedding_model():
    """Lazy-load and return the SentenceTransformer model singleton."""
    global _model_instance
    if _model_instance is None:
        from sentence_transformers import SentenceTransformer

        settings = get_settings()
        logger.info("Loading embedding model: %s", settings.EMBED_MODEL)
        try:
            # Prefer loading directly from local HuggingFace cache if available
            _model_instance = SentenceTransformer(
                settings.EMBED_MODEL,
                model_kwargs={"local_files_only": True},
            )
        except Exception:
            # Fall back to online download if not already cached
            _model_instance = SentenceTransformer(settings.EMBED_MODEL)

        logger.info("Embedding model loaded successfully.")
    return _model_instance


def format_passage(text: str, model_name: str) -> str:
    """Format passage text with required prefix if model is E5."""
    clean = text.strip()
    if is_e5_model(model_name) and not clean.startswith("passage:"):
        return f"passage: {clean}"
    return clean


def format_query(query: str, model_name: str) -> str:
    """Format query text with required prefix if model is E5."""
    clean = query.strip()
    if is_e5_model(model_name) and not clean.startswith("query:"):
        return f"query: {clean}"
    return clean


def embed_passages(texts: List[str], batch_size: int = 32) -> np.ndarray:
    """Generate normalized embeddings for document passages with 'passage: ' prefix.

    Args:
        texts: List of text chunk passages.
        batch_size: Batch size for sentence-transformers encoding.

    Returns:
        numpy.ndarray: 2D array of L2-normalized float32 vectors.
    """
    if not texts:
        return np.empty((0, 384), dtype="float32")

    settings = get_settings()
    model = get_embedding_model()

    # Prepend 'passage: ' for E5 models
    prefixed_texts = [format_passage(t, settings.EMBED_MODEL) for t in texts]

    embeddings = model.encode(
        prefixed_texts,
        batch_size=batch_size,
        show_progress_bar=len(texts) > 100,
        normalize_embeddings=True,
    )
    return np.asarray(embeddings, dtype="float32")


def embed_query(query: str) -> np.ndarray:
    """Generate normalized 1D embedding for a search query with 'query: ' prefix.

    Args:
        query: User question in English or Tamil.

    Returns:
        numpy.ndarray: 1D normalized float32 embedding vector.
    """
    settings = get_settings()
    model = get_embedding_model()

    # Prepend 'query: ' for E5 models
    prefixed_query = format_query(query, settings.EMBED_MODEL)

    embedding = model.encode(
        prefixed_query,
        normalize_embeddings=True,
    )
    return np.asarray(embedding, dtype="float32")


# Backwards compatibility alias
def embed_texts(texts: List[str], batch_size: int = 32) -> np.ndarray:
    """Alias for embed_passages."""
    return embed_passages(texts, batch_size=batch_size)
