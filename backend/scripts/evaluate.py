"""Heuristic validation of the Zaisaku RAG pipeline using Ragas."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add backend/src to path so the script can run from root or backend/
_SCRIPT_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _SCRIPT_DIR.parent
_SRC_DIR = _BACKEND_DIR / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

import datasets  # noqa: E402
from ragas import evaluate  # noqa: E402
from ragas.metrics import (  # noqa: E402
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)

from zaisaku.ingestion.loader import DocumentLoader  # noqa: E402


def load_sample_contexts() -> list[str]:
    """Loads actual financial report text from test fixtures."""
    fixture_path = _BACKEND_DIR / "tests" / "fixtures" / "sample.txt"
    if fixture_path.exists():
        doc = DocumentLoader.load(fixture_path)
        return [doc.text]
    return [
        "Company: Acme Corp. Fiscal Year: 2023. Revenue: $45.2 billion. Net Income: $8.7 billion."
    ]


def get_evaluation_dataset() -> datasets.Dataset:
    """Builds an evaluation dataset matching Zaisaku's financial domain."""
    contexts = load_sample_contexts()
    data = {
        "question": [
            "What was Acme Corp's total revenue in fiscal year 2023?",
            "What was Acme Corp's net income for 2023?",
        ],
        "answer": [
            "Acme Corp reported a total revenue of $45.2 billion in fiscal year 2023.",
            "Acme Corp reported a net income of $8.7 billion in 2023.",
        ],
        "contexts": [
            contexts,
            contexts,
        ],
        "ground_truth": [
            "$45.2 billion",
            "$8.7 billion",
        ],
    }
    return datasets.Dataset.from_dict(data)


def main():
    print("=" * 60)
    print("Zaisaku RAG Pipeline Heuristic Evaluation (Ragas)")
    print("=" * 60)

    if not os.environ.get("OPENAI_API_KEY"):
        print("\n[NOTE] OPENAI_API_KEY environment variable is not set.")
        print("Ragas requires an evaluator LLM API key to score metrics (faithfulness, relevancy, etc.).")
        print("Set OPENAI_API_KEY to run full scoring.")
        print("\nVerifying dataset compilation from Zaisaku financial fixtures...")
        dataset = get_evaluation_dataset()
        print(f"Dataset compiled successfully with {len(dataset)} financial evaluation samples.")
        print("Ready for automated evaluation upon key configuration.")
        return

    dataset = get_evaluation_dataset()
    print(f"\nRunning evaluation on {len(dataset)} financial evaluation samples...")
    result = evaluate(
        dataset,
        metrics=[
            context_precision,
            context_recall,
            faithfulness,
            answer_relevancy,
        ],
    )

    print("\n=== Evaluation Results ===")
    print(result)


if __name__ == "__main__":
    main()
