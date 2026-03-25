"""System prompts and RAG template builders."""

from __future__ import annotations

# The system prompt instructs the LLM on its persona and strict JSON output format.
SYSTEM_PROMPT = """You are Zaisaku, a precise financial AI assistant designed to answer questions based *only* on the provided context documents.

Your response MUST be a valid JSON object with EXACTLY this schema:
{
  "answer": "Your detailed answer here, synthesizing the context. Do not use outside knowledge. If the context does not contain the answer, say 'I cannot answer this based on the provided documents.'",
  "confidence": 0.95,  // A float between 0.0 and 1.0 indicating your confidence
  "sources_used": ["source_doc_name.pdf", "another.html"] // List of filenames from the context that you actually used
}

Do not include markdown blocks around the JSON (e.g. ```json). Output raw JSON only.
"""


def build_rag_prompt(query: str, chunks: list[dict]) -> str:
    """Construct the final user prompt injecting the retrieved chunks.

    Args:
        query: The user's question.
        chunks: List of retrieved text chunks (expected keys: 'text', 'metadata').

    Returns:
        The formatted prompt string to send to the LLM.
    """
    if not chunks:
        context_str = "No relevant documents found."
    else:
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            text = chunk.get("text", "")
            meta = chunk.get("metadata", {})
            source = meta.get("source", "Unknown Source")
            
            # Format each chunk nicely
            part = f"--- Document {i} ---\nSource: {source}\n\n{text}\n"
            context_parts.append(part)
            
        context_str = "\n".join(context_parts)

    prompt = (
        f"Answer the following question using ONLY the context provided below.\n\n"
        f"QUESTION:\n{query}\n\n"
        f"CONTEXT:\n{context_str}\n"
    )
    return prompt
