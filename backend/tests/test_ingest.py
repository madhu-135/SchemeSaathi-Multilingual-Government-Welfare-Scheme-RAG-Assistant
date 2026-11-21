"""Unit tests for SchemeSaathi document ingestion and chunking pipeline."""

from pathlib import Path
import pytest
from app.ingest import (
    clean_scheme_name,
    clean_whitespace,
    detect_language,
    estimate_tokens,
    split_into_sentences,
    chunk_sentences,
    remove_headers_footers_and_pagination,
)


def test_detect_language():
    """Verify language detection for English and Tamil text."""
    en_text = "Pradhan Mantri Kisan Samman Nidhi is a central sector scheme."
    ta_text = "கலைஞர் மகளிர் உரிமைத் திட்டம் குடும்பத் தலைவிகளுக்கானது."
    assert detect_language(en_text) == "en"
    assert detect_language(ta_text) == "ta"


def test_clean_scheme_name():
    """Verify formatting of file stems into readable scheme names."""
    assert clean_scheme_name("pm_kisan") == "PM Kisan"
    assert clean_scheme_name("kalaignar_magalir_urimai") == "Kalaignar Magalir Urimai"
    assert clean_scheme_name("pmay_housing_guidelines") == "PMAY Housing Guidelines"


def test_clean_whitespace():
    """Verify cleanup of multiple spaces, non-breaking characters, and excess blank lines."""
    raw = "Header line\u00a0with\tnon-breaking  spaces\n\n\n\nBody line with   spaces."
    cleaned = clean_whitespace(raw)
    assert "\u00a0" not in cleaned
    assert "  " not in cleaned
    assert "\n\n\n" not in cleaned


def test_remove_headers_footers_and_pagination():
    """Verify stripping of repeated headers, footers, and page numbers."""
    headers = {"Official Government Scheme Guidelines"}
    footers = {"Ministry of Rural Development"}
    text = (
        "Official Government Scheme Guidelines\n"
        "Page 1 of 5\n"
        "Actual policy content here.\n"
        "Ministry of Rural Development"
    )
    cleaned = remove_headers_footers_and_pagination(text, headers, footers)
    assert "Official Government Scheme Guidelines" not in cleaned
    assert "Page 1 of 5" not in cleaned
    assert "Ministry of Rural Development" not in cleaned
    assert "Actual policy content here." in cleaned


def test_split_into_sentences_english():
    """Verify sentence splitting for English with abbreviations."""
    text = "The applicant must submit Doc No. 12. The scheme pays Rs. 6000. Is Aadhaar mandatory? Yes, it is."
    sentences = split_into_sentences(text)
    assert len(sentences) >= 3
    # Ensure 'No.' did not cause split
    assert any("Doc No. 12" in s for s in sentences)


def test_split_into_sentences_tamil():
    """Verify sentence splitting for Tamil with danda and Tamil abbreviations."""
    text = "விண்ணப்பதாரர் தமிழ்நாட்டில் வசிக்க வேண்டும். ஆண்டு வருமானம் ரூ. 2.50 லட்சத்திற்குள் இருக்க வேண்டும்."
    sentences = split_into_sentences(text)
    assert len(sentences) == 2


def test_chunk_sentences_with_overlap():
    """Verify chunk generation with token limits and sentence overlap."""
    sentences = [
        f"Sentence number {i} provides detailed information about government welfare criteria and eligibility rules."
        for i in range(25)
    ]
    chunks = chunk_sentences(sentences, target_tokens=100, overlap_tokens=25)
    assert len(chunks) > 1
    # Check that chunks contain meaningful text
    for chunk in chunks:
        assert len(chunk.strip()) > 0


def test_chunking_overlap_consecutive_chunks():
    """Verify that consecutive chunks share sentences as designated by overlap_tokens."""
    sentences = [
        f"Sentence_{i} provides official welfare assistance to all eligible farming families."
        for i in range(8)
    ]
    chunks = chunk_sentences(sentences, target_tokens=30, overlap_tokens=15)
    assert len(chunks) >= 3

    # Verify boundary overlap: at least one sentence from chunk[i] appears in chunk[i+1]
    for i in range(len(chunks) - 1):
        chunk_i_sents = [s for s in sentences if s in chunks[i]]
        chunk_next_sents = [s for s in sentences if s in chunks[i + 1]]
        shared = set(chunk_i_sents).intersection(set(chunk_next_sents))
        assert len(shared) > 0, f"Chunk {i} and Chunk {i+1} do not share overlap sentences"


def test_chunk_metadata_preservation():
    """Verify that DocumentChunk keeps scheme_name, source_file, page_number, chunk_id, and metadata."""
    from app.models import DocumentChunk
    from app.ingest import estimate_tokens

    text = "Pradhan Mantri Kisan Samman Nidhi provides Rs. 6000 annual support to eligible farmers."
    tok_count = estimate_tokens(text)
    chunk = DocumentChunk(
        chunk_id="pm_kisan_p1_c0",
        scheme_name="PM Kisan",
        source_file="pm_kisan.pdf",
        language="en",
        page_number=1,
        text=text,
        metadata={
            "token_count": tok_count,
            "char_count": len(text),
        },
    )

    assert chunk.scheme_name == "PM Kisan"
    assert chunk.source_file == "pm_kisan.pdf"
    assert chunk.page_number == 1
    assert chunk.chunk_id == "pm_kisan_p1_c0"
    assert chunk.language == "en"
    assert chunk.metadata["token_count"] == tok_count
    assert chunk.metadata["char_count"] == len(text)


