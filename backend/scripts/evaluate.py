import os
import datasets
from ragas import evaluate
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)

# Example placeholder dataset.
# In a real scenario, you would dynamically fetch the generated `answer`
# and `contexts` from your running FastAPI `query` endpoint based on the `question`.
data_samples = {
    "question": [
        "What is the capital of France?",
        "How much revenue did Apple report in 2023?"
    ],
    "answer": [
        "Paris is the capital of France.",
        "Apple reported $383 billion in revenue for 2023."
    ],
    "contexts": [
        ["France is a country in Western Europe. Its capital is Paris."],
        ["In the fiscal year 2023, Apple Inc. announced a total revenue of $383 billion."]
    ],
    "ground_truth": [
        "Paris",
        "$383 billion"
    ],
}

def main():
    print("Initializing RAGAS Evaluation...")
    print("Ensure OPENAI_API_KEY is set in your environment variables for the evaluator generator.")
    
    if not os.environ.get("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY is missing. Ragas metrics require an LLM to evaluate.")
        
    dataset = datasets.Dataset.from_dict(data_samples)

    print("\nRunning evaluation on sample dataset...")
    # Ragas requires these 4 core metrics for comprehensive RAG evaluation
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
