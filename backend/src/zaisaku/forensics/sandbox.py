from __future__ import annotations

import re

from pydantic import BaseModel, Field

MODEL_PRICING: dict[str, tuple[float, float, float, float]] = {
    # model: (prompt_per_m, completion_per_m, baseline_tps, base_latency_ms)
    "llama3.3-70b-instruct": (0.40, 0.80, 58.0, 420.0),
    "claude-3-5-sonnet": (3.00, 15.00, 44.0, 680.0),
    "gpt-4o": (2.50, 10.00, 65.0, 510.0),
    "gpt-4o-mini": (0.15, 0.60, 110.0, 240.0),
    "mistral-large": (2.00, 6.00, 48.0, 590.0),
    "qwen-2.5-coder-32b": (0.35, 0.70, 72.0, 380.0),
}


class BenchmarkRequest(BaseModel):
    prompt: str = Field(..., description="User query or financial analysis prompt")
    system_prompt: str = Field(
        default="You are a Wall Street forensic equity analyst specializing in SEC disclosures.",
        description="System prompt defining persona and constraints",
    )
    model: str = Field(default="llama3.3-70b-instruct", description="Target LLM architecture")
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    ticker: str | None = Field(default=None, description="Optional stock ticker context")
    use_rag: bool = Field(default=True, description="Whether to augment prompt with vector retrieval context")
    rag_context: str | None = Field(default=None, description="Optional explicit RAG context")


class RetrievalChunk(BaseModel):
    id: str
    source: str
    score: float
    content: str


class EvaluationMetrics(BaseModel):
    groundedness_score: float = Field(..., description="Retrieval-grounded factual consistency (0.0 - 1.0)")
    hallucination_risk: str = Field(..., description="LOW | MODERATE | HIGH")
    factual_density: float = Field(..., description="Proportion of quantitative assertions (0.0 - 1.0)")
    financial_domain_alignment: float = Field(..., description="Financial terminology alignment (0.0 - 1.0)")


class BenchmarkResponse(BaseModel):
    model: str
    prompt: str
    generated_response: str
    latency_ms: float
    tokens_per_second: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    retrieval_chunks: list[RetrievalChunk]
    eval_metrics: EvaluationMetrics


class SandboxBenchmark:
    """Benchmark engine for evaluating latency, token consumption, cost, and factual density across models."""

    def __init__(self) -> None:
        pass

    def run_benchmark(self, request: BenchmarkRequest) -> BenchmarkResponse:
        model = request.model.lower().strip()
        pricing = MODEL_PRICING.get(model, (1.00, 3.00, 50.0, 450.0))
        input_price_per_m, output_price_per_m, baseline_tps, base_latency = pricing

        # 1. Retrieve or generate RAG context
        chunks = self._get_context_chunks(request) if request.use_rag else []

        # 2. Approximate input tokens
        full_input = f"{request.system_prompt}\n\nContext:\n"
        for c in chunks:
            full_input += f"[{c.source}] {c.content}\n"
        full_input += f"\nUser Query: {request.prompt}"
        input_tokens = max(len(full_input.split()) * 4 // 3, len(full_input) // 4)

        # 3. Generate response text
        response_text = self._synthesize_response(request, chunks)
        output_tokens = max(len(response_text.split()) * 4 // 3, len(response_text) // 4)
        total_tokens = input_tokens + output_tokens

        # 4. Compute timing and latency metrics
        # Adjust TPS slightly based on temperature and output tokens
        temp_factor = 1.0 + (request.temperature - 0.2) * 0.05
        tps = round(baseline_tps * temp_factor, 1)
        generation_time_sec = output_tokens / max(tps, 1.0)
        retrieval_overhead = 85.0 if request.use_rag else 0.0
        latency_ms = round(base_latency + retrieval_overhead + (generation_time_sec * 1000.0), 1)

        # 5. Compute cost
        cost_usd = (input_tokens * (input_price_per_m / 1_000_000.0)) + (
            output_tokens * (output_price_per_m / 1_000_000.0)
        )
        estimated_cost = round(cost_usd, 6)

        # 6. Evaluation metrics
        eval_metrics = self._calculate_eval_metrics(request, response_text, chunks)

        return BenchmarkResponse(
            model=request.model,
            prompt=request.prompt,
            generated_response=response_text,
            latency_ms=latency_ms,
            tokens_per_second=tps,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=estimated_cost,
            retrieval_chunks=chunks,
            eval_metrics=eval_metrics,
        )

    def _get_context_chunks(self, req: BenchmarkRequest) -> list[RetrievalChunk]:
        if req.rag_context:
            return [
                RetrievalChunk(
                    id="ctx-1",
                    source="User Provided Context",
                    score=0.98,
                    content=req.rag_context[:400],
                )
            ]

        ticker = (req.ticker or "NVDA").upper()
        if ticker == "NVDA":
            return [
                RetrievalChunk(
                    id="nvda-10k-item7",
                    source="NVDA FY2024 Form 10-K (Item 7 MD&A)",
                    score=0.934,
                    content=(
                        "Compute & Networking revenue was $47.41B, up 215%, reflecting higher shipments of the NVIDIA "
                        "HGX platform based on Hopper architecture. Customer concentration: Customer A accounted for "
                        "19% of total revenue. Deferred revenue was $3.12B."
                    ),
                ),
                RetrievalChunk(
                    id="nvda-10k-note3",
                    source="NVDA FY2024 Form 10-K (Note 3 Revenue Recognition)",
                    score=0.887,
                    content=(
                        "Revenue from contracts with customers is recognized when control of the promised goods or "
                        "services is transferred to customers. Unbilled receivables and non-cancelable commitments "
                        "stood at $14.2B at year-end."
                    ),
                ),
            ]
        elif ticker == "TSLA":
            return [
                RetrievalChunk(
                    id="tsla-10k-item7",
                    source="TSLA FY2023 Form 10-K (Item 7 MD&A)",
                    score=0.912,
                    content=(
                        "Automotive regulatory credits recognized totaled $1.79B in 2023. Automotive gross margin "
                        "contracted to 17.1% from 26.2% due to price reductions across Model 3 and Model Y fleets."
                    ),
                )
            ]
        else:
            return [
                RetrievalChunk(
                    id=f"{ticker.lower()}-filing",
                    source=f"{ticker} Recent SEC Disclosures",
                    score=0.895,
                    content=(
                        f"Financial results for {ticker} demonstrated ongoing operations with audited internal "
                        "controls over financial reporting in compliance with Sarbanes-Oxley Act section 404."
                    ),
                )
            ]

    def _synthesize_response(self, req: BenchmarkRequest, chunks: list[RetrievalChunk]) -> str:
        prompt_lower = req.prompt.lower()
        ticker = (req.ticker or "the company").upper()

        if "revenue" in prompt_lower or "deferred" in prompt_lower:
            return (
                f"### Executive Forensic Assessment: Revenue Recognition & Quality for {ticker}\n\n"
                f"Based on regulatory disclosures, {ticker}'s revenue acceleration presents key focal points:\n\n"
                "1. **Contract Structure & Unbilled Balances:** Disclosed contract terms show that revenue is "
                "recognized upon transfer of control. However, analysts should scrutinize the growth in unbilled "
                "receivables and customer concentration against DSO (Days Sales Outstanding) trends.\n"
                "2. **Deferred Revenue Mechanics:** Deferred liabilities reflect multi-year software licensing and "
                "enterprise commitments. An expanding deferred balance signals healthy forward demand, though "
                "cancellation provisions require close audit.\n"
                "3. **Grounded Disclosures:** Citations from audited Form 10-K disclosures verify that top customer "
                "concentration carries counterparty risk that must be modeled in credit sensitivity assessments."
            )
        elif "margin" in prompt_lower or "sustainability" in prompt_lower:
            return (
                f"### Margin Sustainability Analysis for {ticker}\n\n"
                "Evaluating operating margin resilience under macroeconomic and supply chain dynamics:\n\n"
                "1. **Gross Margin Drivers:** Pricing leverage is supported by architectural leadership, but "
                "input material inflation and wafer allocation premiums create upward cost pressure.\n"
                "2. **Operating Leverage:** SG&A and R&D absorption remain favorable as revenue scale expands faster "
                "than headcount additions, driving structural operating margins to multi-year highs.\n"
                "3. **Downside Scenarios:** Should supply constraints ease or competitor architectures narrow the "
                "performance gap, gross margin compression of 200-350 bps remains the primary sensitivity risk."
            )
        else:
            return (
                f"### Institutional Forensic Finding: {ticker}\n\n"
                f"In response to the inquiry regarding: *\"{req.prompt}\"*\n\n"
                "The analysis was cross-referenced against audited regulatory filings and notes to consolidated\n"
                "financial statements. Key institutional takeaways include:\n\n"
                "- **Grounded Evidence:** Documented filings provide rigorous evidentiary support without signs of "
                "material unrecorded liabilities.\n"
                "- **Accounting Prudence:** Conservatism in accrual accounting and working capital ratios matches "
                "sector peers with minimal aggressive capitalization flags.\n"
                "- **Recommendation:** Maintain monitoring of subsequent quarterly disclosures for revisions in "
                "contingent liabilities or key customer master purchase agreements."
            )

    def _calculate_eval_metrics(
        self, req: BenchmarkRequest, response_text: str, chunks: list[RetrievalChunk]
    ) -> EvaluationMetrics:
        # Groundedness score based on presence of citation context and low temperature
        groundedness = 0.95 if chunks else 0.75
        if req.temperature > 0.7:
            groundedness = max(0.5, groundedness - (req.temperature - 0.7) * 0.4)

        groundedness = round(min(1.0, max(0.1, groundedness)), 2)

        # Hallucination risk
        if groundedness >= 0.85:
            risk = "LOW"
        elif groundedness >= 0.65:
            risk = "MODERATE"
        else:
            risk = "HIGH"

        # Factual density: presence of numbers, percentages, currency, and financial terms
        num_matches = len(re.findall(r"\b\d+(\.\d+)?%?|\$\d+", response_text))
        factual_density = round(min(1.0, max(0.4, 0.3 + (num_matches * 0.05))), 2)

        # Financial domain alignment
        fin_terms = ["revenue", "margin", "receivables", "accrual", "capitalization", "10-k", "sox", "dso"]
        term_hits = sum(1 for term in fin_terms if term in response_text.lower())
        fin_alignment = round(min(1.0, max(0.5, 0.5 + (term_hits * 0.08))), 2)

        return EvaluationMetrics(
            groundedness_score=groundedness,
            hallucination_risk=risk,
            factual_density=factual_density,
            financial_domain_alignment=fin_alignment,
        )
