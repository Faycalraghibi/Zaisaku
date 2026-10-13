
from __future__ import annotations

import asyncio
import json
import math
import re

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from zaisaku.api.dependencies import ConfigDep, EmbedderDep, LLMDep, RerankerDep, StoreDep
from zaisaku.generation.prompt import STREAM_SYSTEM_PROMPT, SYSTEM_PROMPT, build_rag_prompt
from zaisaku.models import QueryResponse

router = APIRouter(tags=["generation"])


def _format_candidate_source(c: dict) -> str:
    meta = c.get("metadata", {})
    source = meta.get("source", "Unknown")
    page = meta.get("page")
    return f"{source} (p. {page})" if page is not None else str(source)


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

    sources_used = list(dict.fromkeys(_format_candidate_source(c) for c in candidates))

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

    raw_confidence = parsed.get("confidence", 0.0)
    try:
        confidence = float(raw_confidence)
    except (ValueError, TypeError):
        confidence = 0.0

    return QueryResponse(
        answer=parsed.get("answer", ""),
        confidence=confidence,
        sources=parsed.get("sources_used", sources_used),
        model=response_data.get("model", "unknown"),
        env=response_data.get("env", "unknown"),
    )


def _format_sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("/query/stream")
async def query_documents_stream(
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

    async def event_generator():
        # Step 1: Retrieval
        yield _format_sse("stage", {"stage": "retrieval", "message": "Searching indexed documents..."})
        try:
            q_vec = await asyncio.to_thread(embedder.embed_one, q)
            candidates = await asyncio.to_thread(store.search, q_vec, top_k=settings.retrieval_top_k)
        except Exception as e:
            yield _format_sse("error", {"detail": f"Retrieval failed: {str(e)}"})
            return

        # Step 2: Reranking
        yield _format_sse("stage", {"stage": "rerank", "message": "Scoring candidates with cross-encoder..."})
        if candidates:
            try:
                candidates = await asyncio.to_thread(reranker.rerank, q, candidates, top_k=settings.rerank_top_k)
            except Exception as e:
                yield _format_sse("error", {"detail": f"Reranking failed: {str(e)}"})
                return

        sources_used = list(dict.fromkeys(_format_candidate_source(c) for c in candidates))
        yield _format_sse("sources", {"sources": sources_used})

        confidence = 0.0
        if candidates:
            top_score = candidates[0].get("rerank_score")
            if top_score is not None:
                prob = 1.0 / (1.0 + math.exp(-float(top_score)))
                confidence = round(prob, 2)
            else:
                confidence = 0.85

        # Step 3: Generation
        yield _format_sse("stage", {"stage": "generating", "message": "Synthesizing answer..."})
        prompt = build_rag_prompt(q, candidates)

        full_answer: list[str] = []
        queue: asyncio.Queue[str | None | Exception] = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def stream_worker():
            try:
                if hasattr(llm, "generate_stream"):
                    for chunk in llm.generate_stream(prompt=prompt, system_prompt=STREAM_SYSTEM_PROMPT):
                        loop.call_soon_threadsafe(queue.put_nowait, chunk)
                else:
                    res = llm.generate(prompt=prompt, system_prompt=STREAM_SYSTEM_PROMPT)
                    text = res.get("text", "")
                    if text:
                        loop.call_soon_threadsafe(queue.put_nowait, text)
            except Exception as exc:
                loop.call_soon_threadsafe(queue.put_nowait, exc)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)

        asyncio.create_task(asyncio.to_thread(stream_worker))

        while True:
            item = await queue.get()
            if item is None:
                break
            if isinstance(item, Exception):
                yield _format_sse("error", {"detail": f"LLM generation failed: {str(item)}"})
                return
            full_answer.append(item)
            yield _format_sse("token", {"token": item})

        model = getattr(llm, "model", "unknown")
        env = getattr(llm, "env", "unknown")

        yield _format_sse(
            "complete",
            {
                "answer": "".join(full_answer),
                "confidence": confidence,
                "sources": sources_used,
                "model": model,
                "env": env,
            },
        )

    return StreamingResponse(event_generator(), media_type="text/event-stream")
