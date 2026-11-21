"""Document ingestion and chunking pipeline for SchemeSaathi.

Extracts text from official scheme PDF documents (English and Tamil) using PyMuPDF,
cleans repeated headers/footers and extra whitespace, splits into ~500-token chunks
with 80-token overlap on sentence boundaries, and saves the chunks with metadata
to data/index/chunks.jsonl.
"""

import argparse
import json
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    import pymupdf as fitz
except ImportError:
    import fitz

from app.config import get_settings
from app.models import DocumentChunk

# Configure module logger
logger = logging.getLogger("schemesaathi.ingest")

# Common abbreviations in English and Tamil that should not trigger a sentence split
ABBREVIATIONS = {
    "dr.", "mr.", "mrs.", "ms.", "prof.", "govt.", "no.", "vol.", "dept.",
    "e.g.", "i.e.", "vs.", "approx.", "est.", "sec.", "art.", "p.m.", "a.m.",
    "ரூ.", "திரு.", "திருமதி.", "எண்.", "பக்.", "திட்டம்.", "அரசு.",
}


# ==============================================================================
# Helper Functions: Language, Token Estimation, Cleaning
# ==============================================================================

def detect_language(text: str) -> str:
    """Detect whether text is primarily Tamil or English."""
    # Tamil Unicode block: \u0B80 - \u0BFF
    tamil_chars = len(re.findall(r"[\u0B80-\u0BFF]", text))
    total_alpha = len(re.findall(r"[a-zA-Z\u0B80-\u0BFF]", text))
    if total_alpha > 0 and (tamil_chars / total_alpha) > 0.2:
        return "ta"
    return "en"


def estimate_tokens(text: str) -> int:
    """Estimate token count for multilingual English and Tamil text.

    English tokens are typically ~1.3 per word. Tamil script has rich morphology
    and subword tokenization, yielding roughly 1 token per 3.5 characters or
    ~2 subwords per word.
    """
    if not text.strip():
        return 0

    words = text.split()
    word_count = len(words)
    tamil_chars = len(re.findall(r"[\u0B80-\u0BFF]", text))

    if tamil_chars > 0:
        # Multilingual / Tamil estimation
        char_based_estimate = int(len(text) / 3.5)
        return max(word_count, char_based_estimate)
    else:
        # English estimation
        return max(1, int(word_count * 1.3))


def clean_whitespace(text: str) -> str:
    """Normalize whitespace, tabs, and non-breaking characters."""
    # Replace non-breaking spaces and unicode zero-width spaces
    text = text.replace("\u00a0", " ").replace("\u200b", "").replace("\ufeff", "")
    # Normalize carriage returns
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Replace multiple spaces/tabs within a line with a single space
    text = re.sub(r"[ \t]+", " ", text)
    # Strip whitespace from each individual line
    lines = [line.strip() for line in text.split("\n")]
    # Replace 3 or more consecutive blank lines with a double newline
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def extract_repeating_headers_footers(
    doc: fitz.Document,
) -> Tuple[Set[str], Set[str]]:
    """Scan PDF pages to identify repeated header and footer lines across pages.

    Lines that appear in the top 2 lines or bottom 2 lines across multiple pages
    (>= 40% of pages in docs with >= 3 pages) are treated as repeating boilerplate.
    """
    header_counts: Dict[str, int] = {}
    footer_counts: Dict[str, int] = {}
    total_pages = len(doc)

    if total_pages < 2:
        return set(), set()

    for page in doc:
        raw_text = page.get_text("text").strip()
        if not raw_text:
            continue
        lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
        if not lines:
            continue

        # Inspect top 2 non-empty lines
        for top_line in lines[:2]:
            if len(top_line) > 3 and not top_line.isdigit():
                header_counts[top_line] = header_counts.get(top_line, 0) + 1

        # Inspect bottom 2 non-empty lines
        for btm_line in lines[-2:]:
            if len(btm_line) > 3 and not btm_line.isdigit():
                footer_counts[btm_line] = footer_counts.get(btm_line, 0) + 1

    threshold = max(2, int(total_pages * 0.4))
    headers = {line for line, cnt in header_counts.items() if cnt >= threshold}
    footers = {line for line, cnt in footer_counts.items() if cnt >= threshold}

    return headers, footers


def remove_headers_footers_and_pagination(
    text: str,
    repeated_headers: Set[str],
    repeated_footers: Set[str],
) -> str:
    """Remove repeating document headers, footers, and standalone page numbers."""
    lines = text.split("\n")
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append("")
            continue

        # Remove repeated headers or footers
        if stripped in repeated_headers or stripped in repeated_footers:
            continue

        # Remove standalone page numbers (e.g. "Page 5", "5", "பக்கம் 5", "5 of 12")
        if re.match(
            r"^(?:page|பக்கம்)?\s*\d+\s*(?:of|/|-)?\s*\d*$",
            stripped,
            re.IGNORECASE,
        ):
            continue

        cleaned_lines.append(stripped)

    return "\n".join(cleaned_lines)


# ==============================================================================
# Sentence Splitting & Overlap Chunking
# ==============================================================================

def split_into_sentences(text: str) -> List[str]:
    """Split text on sentence boundaries for English and Tamil.

    Respects periods (.), question marks (?), exclamation marks (!),
    and danda (| or ।) without splitting on known abbreviations or decimal numbers.
    """
    # Regex splits on sentence-ending punctuation followed by whitespace and a capital/Tamil letter/digit
    # Use negative lookbehind for known abbreviations and numbers
    raw_sentences = re.split(r"(?<=[.!?।|])\s+(?=[A-Z\u0B80-\u0BFF0-9\"'(\[])", text)

    sentences: List[str] = []
    buffer = ""

    for seg in raw_sentences:
        seg_clean = seg.strip()
        if not seg_clean:
            continue

        if buffer:
            combined = buffer + " " + seg_clean
        else:
            combined = seg_clean

        # Check if the combined ends with an abbreviation like 'No.' or 'ரூ.'
        last_word = combined.split()[-1].lower() if combined.split() else ""
        if last_word in ABBREVIATIONS:
            buffer = combined
            continue

        sentences.append(combined)
        buffer = ""

    if buffer:
        sentences.append(buffer)

    return sentences if sentences else ([text] if text else [])


def chunk_sentences(
    sentences: List[str],
    target_tokens: int = 500,
    overlap_tokens: int = 80,
) -> List[str]:
    """Group sentences into chunks of about target_tokens with overlap_tokens."""
    if not sentences:
        return []

    chunks: List[str] = []
    current_sentences: List[str] = []
    current_token_count = 0

    idx = 0
    total_sentences = len(sentences)

    while idx < total_sentences:
        sentence = sentences[idx]
        sent_tokens = estimate_tokens(sentence)

        # If a single sentence exceeds target_tokens, split it by words
        if sent_tokens > target_tokens and not current_sentences:
            words = sentence.split()
            word_target = int(target_tokens / 1.3)
            word_overlap = int(overlap_tokens / 1.3)
            start = 0
            while start < len(words):
                end = min(start + word_target, len(words))
                sub_chunk = " ".join(words[start:end])
                chunks.append(sub_chunk)
                if end == len(words):
                    break
                start += max(1, word_target - word_overlap)
            idx += 1
            continue

        if current_token_count + sent_tokens > target_tokens and current_sentences:
            # Finalize current chunk
            chunk_text = " ".join(current_sentences).strip()
            chunks.append(chunk_text)

            # Determine sentences to retain for overlap
            overlap_accum = 0
            overlap_sentences: List[str] = []
            for back_sent in reversed(current_sentences):
                st_tok = estimate_tokens(back_sent)
                if overlap_accum + st_tok <= overlap_tokens or not overlap_sentences:
                    overlap_sentences.insert(0, back_sent)
                    overlap_accum += st_tok
                else:
                    break

            current_sentences = list(overlap_sentences)
            current_token_count = sum(estimate_tokens(s) for s in current_sentences)

        current_sentences.append(sentence)
        current_token_count += sent_tokens
        idx += 1

    if current_sentences:
        final_chunk = " ".join(current_sentences).strip()
        # Avoid duplicating an identical overlap-only chunk
        if not chunks or final_chunk != chunks[-1]:
            chunks.append(final_chunk)

    return chunks


# ==============================================================================
# PDF Ingestion Core
# ==============================================================================

def clean_scheme_name(file_stem: str) -> str:
    """Format PDF filename stem into a clean human-readable scheme name."""
    clean = re.sub(r"[_\-]+", " ", file_stem)
    # Title-case words while keeping known acronyms uppercase
    words = clean.split()
    formatted = []
    for w in words:
        if w.upper() in {"PM", "PMAY", "PMUY", "TN", "CM", "RAG", "DBT", "AAY"}:
            formatted.append(w.upper())
        else:
            formatted.append(w.capitalize())
    return " ".join(formatted)


def process_single_pdf(
    pdf_path: Path,
    target_tokens: int = 500,
    overlap_tokens: int = 80,
) -> Tuple[List[DocumentChunk], int, int]:
    """Extract, clean, and chunk all pages of a single PDF file.

    Returns:
        Tuple: (chunks_list, total_pages, scanned_empty_pages_count)
    """
    scheme_name = clean_scheme_name(pdf_path.stem)
    chunks: List[DocumentChunk] = []
    scanned_empty_count = 0

    try:
        doc = fitz.open(pdf_path)
    except Exception as exc:
        logger.error("Could not open PDF file %s: %s", pdf_path.name, exc)
        return [], 0, 0

    total_pages = len(doc)
    if total_pages == 0:
        logger.warning("PDF file %s has 0 pages.", pdf_path.name)
        doc.close()
        return [], 0, 0

    # Pass 1: Identify repeating headers and footers across pages
    rep_headers, rep_footers = extract_repeating_headers_footers(doc)

    # Pass 2: Extract and clean each page
    for page_idx in range(total_pages):
        page_num = page_idx + 1
        page = doc[page_idx]

        raw_text = page.get_text("text")
        cleaned = clean_whitespace(raw_text)
        cleaned = remove_headers_footers_and_pagination(cleaned, rep_headers, rep_footers)
        cleaned = clean_whitespace(cleaned)

        # Scanned or empty page verification: fewer than 15 alphanumeric/tamil chars
        meaningful_chars = len(re.findall(r"[a-zA-Z0-9\u0B80-\u0BFF]", cleaned))
        if meaningful_chars < 15:
            logger.warning(
                "Page %d of '%s' appears empty or scanned (no extractable text).",
                page_num,
                pdf_path.name,
            )
            scanned_empty_count += 1
            continue

        # Split page into sentences, then group into ~500-token chunks with 80 overlap
        sentences = split_into_sentences(cleaned)
        page_chunks = chunk_sentences(
            sentences,
            target_tokens=target_tokens,
            overlap_tokens=overlap_tokens,
        )

        for chunk_idx, chunk_text in enumerate(page_chunks):
            chunk_id = f"{pdf_path.stem}_p{page_num}_c{chunk_idx}"
            lang = detect_language(chunk_text)
            tok_count = estimate_tokens(chunk_text)

            chunk = DocumentChunk(
                chunk_id=chunk_id,
                scheme_name=scheme_name,
                source_file=pdf_path.name,
                language=lang,
                page_number=page_num,
                text=chunk_text,
                metadata={
                    "token_count": tok_count,
                    "char_count": len(chunk_text),
                },
            )
            chunks.append(chunk)

    doc.close()
    return chunks, total_pages, scanned_empty_count


def ingest_all_pdfs(
    raw_dir: Optional[Path] = None,
    output_file: Optional[Path] = None,
    target_tokens: int = 500,
    overlap_tokens: int = 80,
) -> Dict[str, Any]:
    """Load all PDFs from raw_dir, chunk them, and save to chunks.jsonl.

    Args:
        raw_dir: Directory containing input PDF files (default: data/raw).
        output_file: Path to output JSONL file (default: data/index/chunks.jsonl).
        target_tokens: Desired token length per chunk (~500).
        overlap_tokens: Overlap tokens between consecutive chunks (~80).

    Returns:
        Dict summarizing processing statistics.
    """
    settings = get_settings()
    source_dir = Path(raw_dir) if raw_dir else settings.RAW_DATA_DIR
    target_jsonl = Path(output_file) if output_file else (settings.INDEX_DATA_DIR / "chunks.jsonl")

    # Ensure output directory exists
    target_jsonl.parent.mkdir(parents=True, exist_ok=True)

    # Discover PDFs
    pdf_files = sorted(list(source_dir.glob("*.pdf")) + list(source_dir.glob("*/*.pdf")))

    total_pdfs = len(pdf_files)
    total_pages = 0
    total_scanned_empty = 0
    all_chunks: List[DocumentChunk] = []

    logger.info("Starting ingestion: scanning %d PDF(s) in %s", total_pdfs, source_dir)

    for pdf_path in pdf_files:
        logger.info("Processing: %s", pdf_path.name)
        chunks, pages, scanned_empty = process_single_pdf(
            pdf_path,
            target_tokens=target_tokens,
            overlap_tokens=overlap_tokens,
        )
        all_chunks.extend(chunks)
        total_pages += pages
        total_scanned_empty += scanned_empty

    # Write all chunks to JSONL format
    with open(target_jsonl, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            record = chunk.model_dump()
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    summary = {
        "pdf_count": total_pdfs,
        "total_pages": total_pages,
        "scanned_empty_pages": total_scanned_empty,
        "total_chunks": len(all_chunks),
        "output_file": str(target_jsonl),
    }

    return summary


# ==============================================================================
# CLI Entry Point
# ==============================================================================

def main():
    """CLI runner for SchemeSaathi document ingestion."""
    parser = argparse.ArgumentParser(
        description="SchemeSaathi PDF Ingestion Pipeline (PyMuPDF -> chunks.jsonl)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--raw-dir",
        type=str,
        default=None,
        help="Path to folder containing source scheme PDFs (default: data/raw)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output chunks.jsonl file (default: data/index/chunks.jsonl)",
    )
    parser.add_argument(
        "--target-tokens",
        type=int,
        default=500,
        help="Target tokens per chunk",
    )
    parser.add_argument(
        "--overlap-tokens",
        type=int,
        default=80,
        help="Overlap tokens between chunks",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose debug logging",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    summary = ingest_all_pdfs(
        raw_dir=Path(args.raw_dir) if args.raw_dir else None,
        output_file=Path(args.output) if args.output else None,
        target_tokens=args.target_tokens,
        overlap_tokens=args.overlap_tokens,
    )

    # Print clean formatted summary to console
    print("\n" + "=" * 60)
    print(" 📜 SchemeSaathi Document Ingestion Summary")
    print("=" * 60)
    print(f" PDF Files Processed:    {summary['pdf_count']}")
    print(f" Total Pages Read:       {summary['total_pages']}")
    print(f" Scanned / Empty Pages:  {summary['scanned_empty_pages']} (logged as warnings)")
    print(f" Total Chunks Generated: {summary['total_chunks']}")
    print(f" Saved Destination:      {summary['output_file']}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
