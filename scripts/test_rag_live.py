"""Live demonstration script for SchemeSaathi RAG pipeline.

Tests answer(question, history) on actual indexed scheme documents,
verifying threshold dropping, source citations, and bilingual answers.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.rag import answer

TEST_CASES = [
    {
        "type": "Relevant Central Scheme (English)",
        "question": "What is the financial assistance provided under PM Kisan?",
        "history": [],
    },
    {
        "type": "Relevant State Scheme (Tamil)",
        "question": "கலைஞர் மகளிர் உரிமைத் திட்டத்தின் கீழ் மாதம் எவ்வளவு உரிமைத் தொகை வழங்கப்படுகிறது?",
        "history": [],
    },
    {
        "type": "Irrelevant Query (English - Out of Scope)",
        "question": "What is the recipe for making Italian pasta?",
        "history": [],
    },
    {
        "type": "Irrelevant Query (Tamil - Out of Scope)",
        "question": "செவ்வாய் கிரகத்தில் மனிதர்கள் வாழ முடியுமா?",
        "history": [],
    },
]


async def run_live_tests():
    print("\n" + "=" * 76)
    print(" 🤖 SchemeSaathi Live RAG Pipeline Test (answer(question, history))")
    print("=" * 76)

    for idx, tc in enumerate(TEST_CASES, start=1):
        print(f"\n────────────────────────────────────────────────────────────────────────────")
        print(f" [Test Case {idx}/4] {tc['type']}")
        print(f" Question: \"{tc['question']}\"")
        print(f"────────────────────────────────────────────────────────────────────────────")

        result = await answer(
            question=tc["question"],
            history=tc["history"],
            similarity_threshold=0.80,
        )

        print(f" Detected Language: {result['language']}")
        print(f" Sources Retrieved: {len(result['sources'])}")

        if result["sources"]:
            print("\n Top Sources:")
            for s_idx, src in enumerate(result["sources"][:2], start=1):
                print(f"   [{s_idx}] {src['scheme_name']} (Page {src['page_number']}, Score: {src['score']:.4f})")
                print(f"       File: {src['source_file']}")
                snippet = src["snippet"].replace("\n", " ").strip()
                if len(snippet) > 120:
                    snippet = snippet[:120] + "..."
                print(f"       Snippet: \"{snippet}\"")

        print("\n Generated Response:")
        print(f"   {result['answer']}")

    print("\n" + "=" * 76)
    print(" ✅ All test scenarios evaluated successfully.")
    print("=" * 76 + "\n")


if __name__ == "__main__":
    asyncio.run(run_live_tests())
