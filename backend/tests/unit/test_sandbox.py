from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from zaisaku.api.app import create_app
from zaisaku.forensics.sandbox import BenchmarkRequest, BenchmarkResponse, SandboxBenchmark


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_sandbox_benchmark_execution():
    sandbox = SandboxBenchmark()
    req = BenchmarkRequest(
        prompt="Analyze revenue recognition policies and deferred revenue changes.",
        model="llama3.3-70b-instruct",
        temperature=0.2,
        ticker="NVDA",
        use_rag=True,
    )
    res = sandbox.run_benchmark(req)
    assert isinstance(res, BenchmarkResponse)
    assert res.model == "llama3.3-70b-instruct"
    assert len(res.generated_response) > 50
    assert res.latency_ms > 0
    assert res.input_tokens > 0
    assert res.output_tokens > 0
    assert res.total_tokens == res.input_tokens + res.output_tokens
    assert res.tokens_per_second > 0
    assert res.estimated_cost_usd > 0
    assert len(res.retrieval_chunks) > 0
    assert 0.0 <= res.eval_metrics.groundedness_score <= 1.0


def test_sandbox_benchmark_pricing_models():
    sandbox = SandboxBenchmark()
    req_llama = BenchmarkRequest(
        prompt="Explain inventory valuation under FIFO vs LIFO.",
        model="llama3.3-70b-instruct",
    )
    req_claude = BenchmarkRequest(
        prompt="Explain inventory valuation under FIFO vs LIFO.",
        model="claude-3-5-sonnet",
    )
    res_llama = sandbox.run_benchmark(req_llama)
    res_claude = sandbox.run_benchmark(req_claude)

    # Claude 3.5 Sonnet per-token price is substantially higher than Llama 3.3 70B
    assert res_claude.estimated_cost_usd > res_llama.estimated_cost_usd


def test_sandbox_benchmark_eval_metrics():
    sandbox = SandboxBenchmark()
    req = BenchmarkRequest(
        prompt="What are the unrecorded off-balance-sheet commitments?",
        temperature=0.7,
        ticker="TSLA",
    )
    res = sandbox.run_benchmark(req)
    assert res.eval_metrics.hallucination_risk in ("LOW", "MODERATE", "HIGH")
    assert 0.0 <= res.eval_metrics.factual_density <= 1.0
    assert 0.0 <= res.eval_metrics.financial_domain_alignment <= 1.0


def test_sandbox_api_endpoint(client):
    payload = {
        "prompt": "Evaluate operating margin sustainability.",
        "model": "gpt-4o",
        "temperature": 0.1,
        "ticker": "NVDA",
        "use_rag": True,
    }
    res = client.post("/api/forensics/sandbox/benchmark", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["model"] == "gpt-4o"
    assert "generated_response" in data
    assert "latency_ms" in data
    assert "eval_metrics" in data
