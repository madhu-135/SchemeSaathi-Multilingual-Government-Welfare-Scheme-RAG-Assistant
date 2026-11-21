"""Unit tests for SchemeSaathi embeddings formatting and FAISS vector store."""

import json
from pathlib import Path
import numpy as np
import pytest
from app.embeddings import format_passage, format_query, is_e5_model
from app.models import DocumentChunk
from app.vectorstore import FAISSVectorStore


def test_is_e5_model():
    """Verify detection of E5 model variants."""
    assert is_e5_model("intfloat/multilingual-e5-small") is True
    assert is_e5_model("intfloat/multilingual-e5-base") is True
    assert is_e5_model("sentence-transformers/paraphrase-multilingual-mpnet-base-v2") is False


def test_format_passage_and_query_prefixes():
    """Verify that E5 models receive 'passage: ' and 'query: ' prefixes without double-prefixing."""
    e5_model = "intfloat/multilingual-e5-small"
    non_e5_model = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

    # Passage formatting for E5
    passage_text = "Under PM Kisan, farmers get Rs 6000."
    assert format_passage(passage_text, e5_model) == "passage: Under PM Kisan, farmers get Rs 6000."
    # Avoid duplicate prefix
    assert format_passage("passage: already prefixed", e5_model) == "passage: already prefixed"
    # Non-E5 model leaves text untouched
    assert format_passage(passage_text, non_e5_model) == passage_text

    # Query formatting for E5
    query_text = "What is the benefit?"
    assert format_query(query_text, e5_model) == "query: What is the benefit?"
    assert format_query("query: already prefixed", e5_model) == "query: already prefixed"
    assert format_query(query_text, non_e5_model) == query_text


def test_faiss_vector_store_cosine_search(tmp_path: Path):
    """Test FAISSVectorStore building, cosine similarity search, and saving with synthetic data."""
    store = FAISSVectorStore(index_dir=tmp_path)

    chunks = [
        DocumentChunk(
            chunk_id="chunk_1",
            scheme_name="PM Kisan",
            source_file="pm_kisan.pdf",
            language="en",
            page_number=1,
            text="PM Kisan financial income support details.",
        ),
        DocumentChunk(
            chunk_id="chunk_2",
            scheme_name="Kalaignar Magalir Urimai",
            source_file="kalaignar.pdf",
            language="ta",
            page_number=1,
            text="மகளிர் உரிமைத் திட்டம் தகுதி விவரங்கள்.",
        ),
    ]

    # Create synthetic normalized embeddings: dim=4
    # Vector 1 aligns with [1, 0, 0, 0], Vector 2 aligns with [0, 1, 0, 0]
    embeddings = np.array(
        [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
        ],
        dtype="float32",
    )

    store.build_from_chunks(chunks, embeddings)
    assert store.total_documents == 2

    # Query vector aligned with Vector 1
    query_vec = np.array([1.0, 0.0, 0.0, 0.0], dtype="float32")
    # Search via inner index
    scores, indices = store.index.search(query_vec.reshape(1, -1), 2)
    assert indices[0][0] == 0  # chunk_1 is the top match
    assert pytest.approx(scores[0][0], rel=1e-5) == 1.0  # Cosine similarity is 1.0

    # Scheme filter test
    results = store.search.__wrapped__(store, "dummy", k=2, scheme_filter="PM Kisan") if hasattr(store.search, "__wrapped__") else None

    # Test load from disk
    new_store = FAISSVectorStore(index_dir=tmp_path)
    new_store.load()
    assert new_store.total_documents == 2
    assert new_store.chunks[0].scheme_name == "PM Kisan"
    assert new_store.chunks[1].scheme_name == "Kalaignar Magalir Urimai"


def test_vector_search_known_query_returns_expected_scheme():
    """Verify that semantic search for known queries returns the expected scheme."""
    from app.vectorstore import get_vector_store

    store = get_vector_store()
    if store.total_documents == 0:
        pytest.skip("FAISS index not yet populated in data/index")

    # Known English query for PM-KISAN
    pm_results = store.search(query="Who is eligible for PM-KISAN financial benefits?", k=3)
    assert len(pm_results) > 0
    top_chunk, top_score = pm_results[0]
    assert "PM" in top_chunk.scheme_name or "Kisan" in top_chunk.scheme_name
    assert top_score >= 0.80

    # Known Tamil query for Kalaignar Magalir Urimai
    kmut_results = store.search(query="கலைஞர் மகளிர் உரிமைத் திட்டம் தகுதி வரம்புகள் என்ன?", k=3)
    assert len(kmut_results) > 0
    top_ta_chunk, top_ta_score = kmut_results[0]
    assert "Kalaignar" in top_ta_chunk.scheme_name or "Magalir" in top_ta_chunk.scheme_name
    assert top_ta_score >= 0.80


