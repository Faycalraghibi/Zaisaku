
from __future__ import annotations

import asyncio
import json
import re

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from zaisaku.api.dependencies import ConfigDep, EmbedderDep, LLMDep, RerankerDep, StoreDep
from zaisaku.generation.prompt import SYSTEM_PROMPT, build_rag_prompt
from zaisaku.models import QueryResponse

router = APIRouter(tags=["generation"])


class QueryRequest(BaseModel):
    question: str
    filter: dict | None = None


@router.post("/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    settings: ConfigDep,
    embedder: EmbedderDep,
    store: StoreDep,
    reranker: RerankerDep,
    llm: LLMDep,
):
    q = request.question.strip()
    if not q:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty.",
        )

    try:
        q_vec = await asyncio.to_thread(embedder.embed_one, q)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to embed query: {str(e)}",
        ) from e

    try:
        candidates = await asyncio.to_thread(store.search, q_vec, top_k=settings.retrieval_top_k)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ChromaDB search failed: {str(e)}",
        ) from e

    if candidates:
        try:
            candidates = await asyncio.to_thread(reranker.rerank, q, candidates, top_k=settings.rerank_top_k)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Reranking failed: {str(e)}",
            ) from e
            
    sources_used = list({c["metadata"].get("source", "Unknown") for c in candidates})

    prompt = build_rag_prompt(q, candidates)

    try:
        response_data = await asyncio.to_thread(llm.generate, prompt=prompt, system_prompt=SYSTEM_PROMPT)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM generation failed: {str(e)}",
        ) from e

    raw_text = response_data.get("text", "{}").strip()

    # Extract JSON body if wrapped in markdown code blocks (e.g. ```json ... ``` or ``` ... ```)
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
    raw_text = match.group(1).strip() if match else raw_text.strip("` \n\r\t")

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
