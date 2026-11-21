"""Sanity check retrieval quality for SchemeSaathi.

Executes 5 sample English and Tamil queries against the FAISS vector index,
printing the top-3 retrieved chunks with cosine similarity scores and citations.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path so app modules are resolvable
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.config import get_settings
from app.vectorstore import FAISSVectorStore


# 5 Test queries covering English and Tamil government scheme topics
SAMPLE_QUERIES = [
    {
        "id": 1,
        "language": "English",
        "query": "What is the financial assistance provided under PM Kisan?",
        "expected_topic": "PM Kisan Rs. 6000/- per year in three installments",
    },
    {
        "id": 2,
        "language": "Tamil (தமிழ்)",
        "query": "கலைஞர் மகளிர் உரிமைத் திட்டத்திற்கு விண்ணப்பிக்கும் தகுதி மற்றும் நிபந்தனைகள் என்ன?",
        "expected_topic": "மகளிர் உரிமைத் திட்டம் குடும்ப அட்டை, ஆண்டு வருமானம் ரூ. 2.50 லட்சம் வரம்பு",
    },
    {
        "id": 3,
        "language": "English",
        "query": "Who are the excluded categories not eligible for PM Kisan scheme benefits?",
        "expected_topic": "Exclusion: institutional landholders, ministers, government employees",
    },
    {
        "id": 4,
        "language": "Tamil (தமிழ்)",
        "query": "மகளிர் உரிமைத் தொகை திட்டத்தின் கீழ் மாதம் எவ்வளவு நிதி உதவி வழங்கப்படுகிறது?",
        "expected_topic": "மாதம் தோறும் ரூ. 1,000 உரிமைத் தொகை DBT மூலம் வழங்கல்",
    },
    {
        "id": 5,
        "language": "English",
        "query": "How are beneficiaries identified and how can grievances be registered for PM Kisan?",
        "expected_topic": "State/UT identification, Aadhaar mandatory, toll-free 155261",
    },
]


def run_sanity_check(k: int = 3):
    """Run search for each sample query and print results with formatted output."""
    settings = get_settings()
    store = FAISSVectorStore()

    if store.total_documents == 0:
        print("\n❌ FAISS index is empty or not found at:", store.index_file)
        print("Please build the index first using:")
        print("  python -m app.vectorstore --build\n")
        return

    print("\n" + "=" * 78)
    print(" 🔍 SchemeSaathi Semantic Retrieval Sanity Check (English & Tamil)")
    print(f" Embedding Model:  {settings.EMBED_MODEL} (E5 with 'query:' and 'passage:' prefixes)")
    print(f" Total Chunks:     {store.total_documents}")
    print(f" Top-k per Query:  {k}")
    print("=" * 78)

    for item in SAMPLE_QUERIES:
        q_id = item["id"]
        lang = item["language"]
        q_text = item["query"]
        expected = item["expected_topic"]

        print(f"\n──────────────────────────────────────────────────────────────────────────────")
        print(f" [Query {q_id}/5] [{lang}]")
        print(f" Query:    \"{q_text}\"")
        print(f" Expected: {expected}")
        print(f"──────────────────────────────────────────────────────────────────────────────")

        results = store.search(query=q_text, k=k)

        if not results:
            print("  ⚠️  No matching chunks found in index.")
            continue

        for rank, (chunk, score) in enumerate(results, start=1):
            # Highlight top match with higher visibility
            badge = "⭐ TOP MATCH" if rank == 1 else f"  Result #{rank}"
            print(f"\n  {badge} | Cosine Similarity Score: {score:.4f}")
            print(f"  Scheme:      {chunk.scheme_name}")
            print(f"  Source File: {chunk.source_file} (Page {chunk.page_number}) [ID: {chunk.chunk_id}]")
            print(f"  Language:    {chunk.language}")
            
            # Format preview snippet cleanly
            snippet = chunk.text.replace("\n", " ").strip()
            if len(snippet) > 200:
                snippet = snippet[:200] + "..."
            print(f"  Text Excerpt: \"{snippet}\"")

    print("\n" + "=" * 78)
    print(" ✅ Sanity check completed successfully.")
    print("=" * 78 + "\n")


if __name__ == "__main__":
    top_k = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    run_sanity_check(k=top_k)

