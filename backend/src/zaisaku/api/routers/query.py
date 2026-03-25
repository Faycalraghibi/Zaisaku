"""RAG generation endpoint."""

from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from zaisaku.api.dependencies import ConfigDep, EmbedderDep, LLMDep, RerankerDep, StoreDep
from zaisaku.generation.prompt import SYSTEM_PROMPT, build_rag_prompt
from zaisaku.models import QueryResponse

router = APIRouter(tags=["generation"])


class QueryRequest(BaseModel):
    question: str
    filter: Optional[dict] = None


@router.post("/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    settings: ConfigDep,
    embedder: EmbedderDep,
    store: StoreDep,
    reranker: RerankerDep,
    llm: LLMDep,
):
    """Query the RAG pipeline."""
    q = request.question.strip()
    if not q:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty.",
        )

    # 1. Embed user query
    try:
        q_vec = embedder.embed_one(q)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to embed query: {str(e)}",
        )

    # 2. Retrieve top_k from vector store
    try:
        candidates = store.search(q_vec, top_k=settings.retrieval_top_k)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ChromaDB search failed: {str(e)}",
        )

    # 3. Rerank the candidates
    if candidates:
        try:
            candidates = reranker.rerank(q, candidates, top_k=settings.rerank_top_k)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Reranking failed: {str(e)}",
            )
            
    # Keep track of unique sources matching the final candidates
    sources_used = list({c["metadata"].get("source", "Unknown") for c in candidates})

    # 4. Build prompt
    prompt = build_rag_prompt(q, candidates)

    # 5. Generate answer
    try:
        response_data = llm.generate(prompt=prompt, system_prompt=SYSTEM_PROMPT)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM generation failed: {str(e)}",
        )

    # 6. Parse JSON output
    raw_text = response_data.get("text", "{}").strip()
    
    # Sometimes LLMs prepend/append markdown backticks despite instructions.
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]
    raw_text = raw_text.strip()

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        # Graceful fallback if LLM disobeys JSON schema
        parsed = {
            "answer": raw_text,
            "confidence": 0.0,
            "sources_used": sources_used,
        }

    return QueryResponse(
        answer=parsed.get("answer", ""),
        confidence=float(parsed.get("confidence", 0.0)),
        sources=parsed.get("sources_used", sources_used),
        model=response_data.get("model", "unknown"),
        env=response_data.get("env", "unknown"),
    )
