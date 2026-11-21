"""FAISS vector store management for SchemeSaathi.

Builds, persists, loads, and queries a FAISS index using normalized vectors
and Inner Product (IndexFlatIP) to achieve exact Cosine Similarity.
Provides a CLI to build the index from chunks.jsonl.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Pre-load torch on Windows to initialize OpenMP runtime for FAISS
try:
    import torch  # noqa: F401
except ImportError:
    pass

import faiss
import numpy as np
from app.config import get_settings
from app.embeddings import embed_passages, embed_query
from app.models import DocumentChunk

logger = logging.getLogger("schemesaathi.vectorstore")


class FAISSVectorStore:
    """Manages a FAISS vector index with associated DocumentChunk metadata."""

    def __init__(self, index_dir: Optional[Path] = None):
        self.settings = get_settings()
        self.index_dir = Path(index_dir) if index_dir else self.settings.INDEX_DATA_DIR
        self.index_file = self.index_dir / "faiss_index.bin"
        self.metadata_file = self.index_dir / "chunks_metadata.json"

        self.index: Optional[faiss.Index] = None
        self.chunks: List[DocumentChunk] = []

        # Automatically load index if files are already persisted
        if self.index_file.exists() and self.metadata_file.exists():
            self.load()

    @property
    def total_documents(self) -> int:
        """Return the number of vectors stored in the index."""
        if self.index is not None:
            return self.index.ntotal
        return len(self.chunks)

    def build_from_chunks(
        self, chunks: List[DocumentChunk], embeddings: np.ndarray
    ) -> None:
        """Create and populate a new FAISS IndexFlatIP index with normalized vectors."""
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Mismatch: received {len(chunks)} chunks and {len(embeddings)} embeddings"
            )

        dimension = embeddings.shape[1]
        # Inner product on L2-normalized vectors is exact cosine similarity
        index = faiss.IndexFlatIP(dimension)
        index.add(embeddings.astype("float32"))

        self.index = index
        self.chunks = chunks
        self.save()
        logger.info(
            "Built FAISS index: %d vectors, dim=%d at %s",
            index.ntotal,
            dimension,
            self.index_dir,
        )

    def build_from_jsonl(
        self,
        jsonl_path: Optional[Path] = None,
        batch_size: int = 32,
    ) -> int:
        """Read chunks from chunks.jsonl, generate embeddings, and build the index.

        Args:
            jsonl_path: Path to chunks.jsonl (defaults to settings.INDEX_DATA_DIR / 'chunks.jsonl').
            batch_size: Batch size for sentence-transformers encoding.

        Returns:
            int: Number of chunks indexed.
        """
        source_file = Path(jsonl_path) if jsonl_path else (self.index_dir / "chunks.jsonl")
        if not source_file.exists():
            raise FileNotFoundError(
                f"Chunks JSONL file not found at {source_file}. Please run ingest.py first."
            )

        chunks: List[DocumentChunk] = []
        with open(source_file, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                clean_line = line.strip()
                if not clean_line:
                    continue
                try:
                    data = json.loads(clean_line)
                    chunks.append(DocumentChunk(**data))
                except Exception as exc:
                    logger.warning("Skipping malformed JSON at line %d: %s", line_no, exc)

        if not chunks:
            logger.warning("No valid chunks found in %s to index.", source_file)
            return 0

        logger.info("Generating embeddings for %d chunk passages...", len(chunks))
        texts = [chunk.text for chunk in chunks]
        embeddings = embed_passages(texts, batch_size=batch_size)

        self.build_from_chunks(chunks, embeddings)
        return len(chunks)

    def search(
        self,
        query: str,
        k: Optional[int] = None,
        scheme_filter: Optional[str] = None,
    ) -> List[Tuple[DocumentChunk, float]]:
        """Search the FAISS index for the top-k most similar chunks.

        Args:
            query: Query string in English or Tamil.
            k: Number of nearest neighbors to retrieve (default: settings.TOP_K).
            scheme_filter: Optional filter to restrict results to a specific scheme.

        Returns:
            List of (DocumentChunk, score) tuples ordered by highest cosine similarity.
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Search attempted on an empty or unloaded FAISS index.")
            return []

        top_k = k or self.settings.TOP_K
        fetch_k = min(self.index.ntotal, top_k * 3 if scheme_filter else top_k)

        # Generate normalized query vector with 'query: ' prefix
        query_vec = embed_query(query).reshape(1, -1).astype("float32")
        scores, indices = self.index.search(query_vec, fetch_k)

        results: List[Tuple[DocumentChunk, float]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.chunks):
                continue
            chunk = self.chunks[idx]
            if (
                scheme_filter
                and chunk.scheme_name.lower() != scheme_filter.lower()
            ):
                continue
            results.append((chunk, float(score)))
            if len(results) >= top_k:
                break

        return results

    def save(self) -> None:
        """Persist FAISS index binary and metadata JSON to disk."""
        self.index_dir.mkdir(parents=True, exist_ok=True)
        if self.index is not None:
            faiss.write_index(self.index, str(self.index_file))

        with open(self.metadata_file, "w", encoding="utf-8") as f:
            data = [chunk.model_dump() for chunk in self.chunks]
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info("Persisted FAISS index and metadata to %s", self.index_dir)

    def load(self) -> None:
        """Load persisted FAISS index binary and metadata JSON from disk."""
        try:
            self.index = faiss.read_index(str(self.index_file))
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.chunks = [DocumentChunk(**item) for item in data]
            logger.info(
                "Successfully loaded FAISS index (%d vectors) and %d chunk metadata records from %s",
                self.index.ntotal,
                len(self.chunks),
                self.index_dir,
            )
        except Exception as exc:
            logger.error("Failed to load FAISS index from %s: %s", self.index_dir, exc)
            self.index = None
            self.chunks = []


# Singleton accessor
_vector_store_instance: Optional[FAISSVectorStore] = None


def get_vector_store() -> FAISSVectorStore:
    """Retrieve or initialize the singleton FAISS vector store."""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = FAISSVectorStore()
    return _vector_store_instance


# ==============================================================================
# CLI Entry Point
# ==============================================================================

def main():
    """CLI runner to build and test the FAISS index."""
    parser = argparse.ArgumentParser(
        description="SchemeSaathi FAISS Vector Store Builder",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--build",
        action="store_true",
        default=True,
        help="Build FAISS index from data/index/chunks.jsonl",
    )
    parser.add_argument(
        "--jsonl",
        type=str,
        default=None,
        help="Custom path to chunks.jsonl file",
    )
    parser.add_argument(
        "--index-dir",
        type=str,
        default=None,
        help="Directory to save the FAISS index",
    )
    parser.add_argument(
        "--search",
        type=str,
        default=None,
        help="Optional test query to run after building",
    )
    parser.add_argument(
        "-k",
        type=int,
        default=3,
        help="Number of results to return for test query",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    settings = get_settings()
    store = FAISSVectorStore(
        index_dir=Path(args.index_dir) if args.index_dir else settings.INDEX_DATA_DIR
    )

    jsonl_path = Path(args.jsonl) if args.jsonl else (store.index_dir / "chunks.jsonl")
    count = store.build_from_jsonl(jsonl_path=jsonl_path)

    print("\n" + "=" * 65)
    print(" ⚡ SchemeSaathi FAISS Vector Index Summary")
    print("=" * 65)
    print(f" Source JSONL:       {jsonl_path}")
    print(f" Chunks Indexed:     {count}")
    print(f" Embedding Model:    {settings.EMBED_MODEL}")
    print(f" Similarity Metric:  Cosine Similarity (IndexFlatIP on normalized vectors)")
    print(f" Output FAISS File:  {store.index_file}")
    print("=" * 65 + "\n")

    if args.search:
        print(f"🔎 Testing search for query: '{args.search}' (top {args.k}):\n")
        results = store.search(args.search, k=args.k)
        for i, (chunk, score) in enumerate(results, 1):
            print(f"[{i}] Score: {score:.4f} | Scheme: {chunk.scheme_name} (Page {chunk.page_number})")
            print(f"    Excerpt: {chunk.text[:180]}...\n")


if __name__ == "__main__":
    main()
