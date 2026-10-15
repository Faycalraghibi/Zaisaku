"""AI Macro Scenario Stress-Tester & Monte Carlo Risk Simulator for forensic due diligence."""

from __future__ import annotations

import math
import random
from typing import Any

from pydantic import BaseModel, Field


class MacroShockPreset(BaseModel):
    """Pre-configured institutional macro risk scenario."""

    id: str
    name: str
    category: str
    description: str
    revenue_shock_pct: float
    gross_margin_compression_bps: float
    opex_inflation_pct: float
    dso_expansion_days: float
    wacc_increase_bps: float


class BaselineFinancials(BaseModel):
    """Company baseline run-rate financials (values in USD Millions, margins as fractions)."""

    ticker: str
    period: str
    revenue: float
    gross_margin: float
    gross_profit: float
    opex: float
    ebit: float
    tax_rate: float
    net_income: float
    dso: float
    operating_cash_flow: float
    capex: float
    free_cash_flow: float


class ProFormaMetrics(BaseModel):
    """Calculated pro-forma financials following applied scenario shock."""

    shocked_revenue: float
    revenue_delta: float
    revenue_delta_pct: float
    shocked_gross_margin: float
    gross_margin_delta_bps: float
    shocked_gross_profit: float
    shocked_opex: float
    shocked_ebit: float
    ebit_delta: float
    ebit_margin: float
    shocked_net_income: float
    net_income_delta: float
    working_capital_drag: float
    shocked_fcf: float
    fcf_delta: float
    fcf_margin: float


class HistogramBin(BaseModel):
    """Histogram bin for Monte Carlo distribution visualization."""

    bin_start: float
    bin_end: float
    bin_center: float
    count: int
    density: float


class MonteCarloResult(BaseModel):
    """Monte Carlo 1,000-run simulation output and tail risk metrics."""

    runs: int
    mean_fcf: float
    median_fcf: float
    std_dev: float
    min_fcf: float
    max_fcf: float
    var_95: float
    var_99: float
    cvar_95: float
    prob_negative_fcf: float
    histogram_bins: list[HistogramBin]


class AICommentary(BaseModel):
    """AI forensic evaluation of capital buffer, rating impact, and hedging playbooks."""

    scenario_name: str
    executive_summary: str
    key_vulnerabilities: list[str]
    mitigation_actions: list[str]
    capital_rating_impact: str
    liquidity_runway_months: float


class StressSimulationRequest(BaseModel):
    """Input payload for scenario simulation."""

    ticker: str = Field(default="NVDA", description="Stock ticker symbol")
    scenario_preset_id: str | None = Field(default=None, description="Preset identifier to auto-populate shocks")
    revenue_shock_pct: float | None = Field(default=None, description="Pro-forma revenue shock percentage (e.g. -15.0)")
    gross_margin_compression_bps: float | None = Field(
        default=None, description="Gross margin compression in basis points (e.g. -450)"
    )
    opex_inflation_pct: float | None = Field(default=None, description="OpEx cost inflation percentage (e.g. 8.0)")
    dso_expansion_days: float | None = Field(
        default=None, description="Days Sales Outstanding increase in days (e.g. 35.0)"
    )
    wacc_increase_bps: float | None = Field(
        default=None, description="Weighted Average Cost of Capital expansion in bps (e.g. 125.0)"
    )
    n_monte_carlo_runs: int = Field(default=1000, ge=100, le=5000, description="Monte Carlo simulation iterations")
    random_seed: int | None = Field(default=None, description="Optional seed for deterministic simulation")


class StressSimulationResponse(BaseModel):
    """Consolidated stress-testing response containing pro-forma model, sensitivity matrix, and Monte Carlo."""

    ticker: str
    applied_preset: str
    baseline: BaselineFinancials
    pro_forma: ProFormaMetrics
    sensitivity_matrix: list[dict[str, Any]]
    monte_carlo: MonteCarloResult
    ai_commentary: AICommentary


class ScenarioStressTester:
    """Forensic engine simulating macro stress shocks and Monte Carlo capital distributions."""

    PRESETS: list[MacroShockPreset] = [
        MacroShockPreset(
            id="taiwan_wafer_disruption",
            name="Foundry / Packaging Constraint",
            category="Supply Chain Bottleneck",
            description=(
                "Geopolitical or natural bottleneck at leading-edge foundry / CoWoS packaging facilities, "
                "throttling wafer throughput and triggering supply rationing."
            ),
            revenue_shock_pct=-18.5,
            gross_margin_compression_bps=-520.0,
            opex_inflation_pct=9.5,
            dso_expansion_days=40.0,
            wacc_increase_bps=150.0,
        ),
        MacroShockPreset(
            id="hyperscaler_capex_pause",
            name="Tier-1 Hyperscaler Capex Pause",
            category="Demand Digestion",
            description=(
                "Major cloud service providers (Microsoft, Alphabet, Meta, Amazon) institute a 2-quarter capex "
                "digestion pause following aggressive infrastructure buildup."
            ),
            revenue_shock_pct=-22.0,
            gross_margin_compression_bps=-380.0,
            opex_inflation_pct=4.0,
            dso_expansion_days=25.0,
            wacc_increase_bps=100.0,
        ),
        MacroShockPreset(
            id="export_restriction_escalation",
            name="Geopolitical Export Controls Escalation",
            category="Regulatory Sanctions",
            description=(
                "Expansion of semiconductor export control thresholds prohibiting high-bandwidth enterprise "
                "accelerators to previously compliant secondary regions."
            ),
            revenue_shock_pct=-14.0,
            gross_margin_compression_bps=-260.0,
            opex_inflation_pct=6.0,
            dso_expansion_days=30.0,
            wacc_increase_bps=80.0,
        ),
        MacroShockPreset(
            id="severe_dso_blowout",
            name="Customer Liquidity & DSO Blowout",
            category="Working Capital Drag",
            description=(
                "Slowing sovereign and tier-2 cloud customer payment cycles, causing channel inventory "
                "stagnation and working capital immobilization."
            ),
            revenue_shock_pct=-6.0,
            gross_margin_compression_bps=-180.0,
            opex_inflation_pct=5.0,
            dso_expansion_days=55.0,
            wacc_increase_bps=90.0,
        ),
    ]

    BASELINES: dict[str, BaselineFinancials] = {
        "NVDA": BaselineFinancials(
            ticker="NVDA",
            period="FY2025/2026 Annualized",
            revenue=130500.0,
            gross_margin=0.748,
            gross_profit=97614.0,
            opex=14200.0,
            ebit=83414.0,
            tax_rate=0.125,
            net_income=72987.25,
            dso=48.0,
            operating_cash_flow=64500.0,
            capex=4800.0,
            free_cash_flow=59700.0,
        ),
        "AAPL": BaselineFinancials(
            ticker="AAPL",
            period="FY2025 Annualized",
            revenue=391000.0,
            gross_margin=0.462,
            gross_profit=180642.0,
            opex=57000.0,
            ebit=123642.0,
            tax_rate=0.148,
            net_income=105343.0,
            dso=32.0,
            operating_cash_flow=118000.0,
            capex=9500.0,
            free_cash_flow=108500.0,
        ),
        "MSFT": BaselineFinancials(
            ticker="MSFT",
            period="FY2025 Annualized",
            revenue=245000.0,
            gross_margin=0.698,
            gross_profit=171010.0,
            opex=61000.0,
            ebit=110010.0,
            tax_rate=0.190,
            net_income=89108.1,
            dso=54.0,
            operating_cash_flow=112000.0,
            capex=44000.0,
            free_cash_flow=68000.0,
        ),
    }

    def get_presets(self) -> list[MacroShockPreset]:
        """Return list of predefined macro shock scenarios."""
        return self.PRESETS

    def get_baseline_financials(self, ticker: str) -> BaselineFinancials:
        """Retrieve baseline financials for given ticker or generate realistic peer baseline."""
        t = ticker.strip().upper()
        if t in self.BASELINES:
            return self.BASELINES[t]

        # Generic institutional large-cap baseline fallback
        rev = 50000.0
        gm = 0.55
        gp = rev * gm
        opex = 12000.0
        ebit = gp - opex
        tax = 0.15
        net = ebit * (1.0 - tax)
        ocf = net * 1.15
        capex = 3500.0
        fcf = ocf - capex
        return BaselineFinancials(
            ticker=t,
            period="LTM Institutional Baseline",
            revenue=rev,
            gross_margin=gm,
            gross_profit=gp,
            opex=opex,
            ebit=ebit,
            tax_rate=tax,
            net_income=net,
            dso=45.0,
            operating_cash_flow=ocf,
            capex=capex,
            free_cash_flow=fcf,
        )

    def simulate(self, request: StressSimulationRequest) -> StressSimulationResponse:
        """Compute full pro-forma shock, sensitivity matrix, and Monte Carlo tail distribution."""
        baseline = self.get_baseline_financials(request.ticker)

        # Resolve shock values: preset fallback or custom overrides
        preset = None
        if request.scenario_preset_id:
            preset = next((p for p in self.PRESETS if p.id == request.scenario_preset_id), None)

        rev_shock_pct = request.revenue_shock_pct
        if rev_shock_pct is None:
            rev_shock_pct = preset.revenue_shock_pct if preset else -15.0

        gm_comp_bps = request.gross_margin_compression_bps
        if gm_comp_bps is None:
            gm_comp_bps = preset.gross_margin_compression_bps if preset else -450.0

        opex_inf_pct = request.opex_inflation_pct
        if opex_inf_pct is None:
            opex_inf_pct = preset.opex_inflation_pct if preset else 8.0

        dso_exp_days = request.dso_expansion_days
        if dso_exp_days is None:
            dso_exp_days = preset.dso_expansion_days if preset else 35.0

        wacc_inc_bps = request.wacc_increase_bps
        if wacc_inc_bps is None:
            wacc_inc_bps = preset.wacc_increase_bps if preset else 125.0

        preset_name = preset.name if preset else "Custom Scenario Shock"

        # 1. Pro-forma shock calculation with safety bounds
        pro_forma = self._calculate_pro_forma(
            baseline=baseline,
            rev_shock_pct=rev_shock_pct,
            gm_comp_bps=gm_comp_bps,
            opex_inf_pct=opex_inf_pct,
            dso_exp_days=dso_exp_days,
        )

        # 2. 2D Sensitivity Grid (Revenue Shock vs Gross Margin Compression)
        sensitivity_matrix = self._generate_sensitivity_matrix(baseline)

        # 3. Monte Carlo Simulation
        monte_carlo = self._run_monte_carlo(
            baseline=baseline,
            rev_shock_pct=rev_shock_pct,
            gm_comp_bps=gm_comp_bps,
            opex_inf_pct=opex_inf_pct,
            dso_exp_days=dso_exp_days,
            n_runs=request.n_monte_carlo_runs,
            seed=request.random_seed,
        )

        # 4. AI Strategic Commentary & Hedging Actions
        ai_commentary = self._generate_commentary(
            baseline=baseline,
            pro_forma=pro_forma,
            monte_carlo=monte_carlo,
            preset_name=preset_name,
        )

        return StressSimulationResponse(
            ticker=baseline.ticker,
            applied_preset=preset_name,
            baseline=baseline,
            pro_forma=pro_forma,
            sensitivity_matrix=sensitivity_matrix,
            monte_carlo=monte_carlo,
            ai_commentary=ai_commentary,
        )

    def _calculate_pro_forma(
        self,
        baseline: BaselineFinancials,
        rev_shock_pct: float,
        gm_comp_bps: float,
        opex_inf_pct: float,
        dso_exp_days: float,
    ) -> ProFormaMetrics:
        """Perform exact arithmetic calculation of pro-forma income statement and cash flows."""
        # Revenue
        revenue_multiplier = max(0.05, 1.0 + (rev_shock_pct / 100.0))
        shocked_rev = baseline.revenue * revenue_multiplier
        rev_delta = shocked_rev - baseline.revenue
        rev_delta_pct = (rev_delta / baseline.revenue * 100.0) if baseline.revenue else 0.0

        # Margin bounded between 1.0% and 99.0%
        gm_delta_frac = gm_comp_bps / 10000.0
        shocked_gm = max(0.01, min(0.99, baseline.gross_margin + gm_delta_frac))
        shocked_gp = shocked_rev * shocked_gm

        # OpEx bounded floor
        opex_multiplier = max(0.5, 1.0 + (opex_inf_pct / 100.0))
        shocked_opex = baseline.opex * opex_multiplier

        # EBIT & Net Income
        shocked_ebit = shocked_gp - shocked_opex
        ebit_delta = shocked_ebit - baseline.ebit
        ebit_margin = (shocked_ebit / shocked_rev) if shocked_rev > 0 else 0.0

        tax_rate = max(0.05, min(0.35, baseline.tax_rate))
        shocked_net = shocked_ebit * (1.0 - tax_rate)
        net_delta = shocked_net - baseline.net_income

        # Working Capital Drag from DSO Expansion: (dso_expansion / 365) * shocked_revenue
        # Clamped so it cannot be negative if DSO reduced
        wc_drag = max(0.0, (dso_exp_days / 365.0) * shocked_rev)

        # Free Cash Flow impact
        # Base FCF adjusts by after-tax EBIT delta minus incremental working capital drag
        ebit_delta_after_tax = ebit_delta * (1.0 - tax_rate)
        shocked_fcf = baseline.free_cash_flow + ebit_delta_after_tax - wc_drag
        fcf_delta = shocked_fcf - baseline.free_cash_flow
        fcf_margin = (shocked_fcf / shocked_rev) if shocked_rev > 0 else 0.0

        return ProFormaMetrics(
            shocked_revenue=round(shocked_rev, 2),
            revenue_delta=round(rev_delta, 2),
            revenue_delta_pct=round(rev_delta_pct, 2),
            shocked_gross_margin=round(shocked_gm, 4),
            gross_margin_delta_bps=round(gm_comp_bps, 1),
            shocked_gross_profit=round(shocked_gp, 2),
            shocked_opex=round(shocked_opex, 2),
            shocked_ebit=round(shocked_ebit, 2),
            ebit_delta=round(ebit_delta, 2),
            ebit_margin=round(ebit_margin, 4),
            shocked_net_income=round(shocked_net, 2),
            net_income_delta=round(net_delta, 2),
            working_capital_drag=round(wc_drag, 2),
            shocked_fcf=round(shocked_fcf, 2),
            fcf_delta=round(fcf_delta, 2),
            fcf_margin=round(fcf_margin, 4),
        )

    def _generate_sensitivity_matrix(self, baseline: BaselineFinancials) -> list[dict[str, Any]]:
        """Compute 2D matrix evaluating Net Income and FCF under varying revenue and margin shocks."""
        rev_steps = [-30.0, -20.0, -10.0, 0.0, 10.0]
        margin_steps = [-600.0, -400.0, -200.0, 0.0]

        matrix: list[dict[str, Any]] = []
        for r in rev_steps:
            row_points: list[dict[str, Any]] = []
            for m in margin_steps:
                pf = self._calculate_pro_forma(
                    baseline=baseline,
                    rev_shock_pct=r,
                    gm_comp_bps=m,
                    opex_inf_pct=5.0,
                    dso_exp_days=20.0,
                )
                row_points.append({
                    "margin_compression_bps": m,
                    "pro_forma_net_income": pf.shocked_net_income,
                    "pro_forma_fcf": pf.shocked_fcf,
                    "fcf_margin": pf.fcf_margin,
                })
            matrix.append({
                "revenue_shock_pct": r,
                "points": row_points,
            })
        return matrix

    def _run_monte_carlo(
        self,
        baseline: BaselineFinancials,
        rev_shock_pct: float,
        gm_comp_bps: float,
        opex_inf_pct: float,
        dso_exp_days: float,
        n_runs: int = 1000,
        seed: int | None = None,
    ) -> MonteCarloResult:
        """Execute Monte Carlo distribution sampling and calculate tail risk statistics."""
        rng = random.Random(seed)

        # Standard deviations proportional to shock severity
        rev_sigma = max(2.0, abs(rev_shock_pct) * 0.35)
        gm_sigma = max(40.0, abs(gm_comp_bps) * 0.30)
        opex_sigma = max(1.5, abs(opex_inf_pct) * 0.25)
        dso_sigma = max(5.0, abs(dso_exp_days) * 0.25)

        simulated_fcf: list[float] = []

        for _ in range(n_runs):
            # Sample shocks from Gaussian distribution
            sample_rev_shock = rng.gauss(rev_shock_pct, rev_sigma)
            sample_gm_comp = rng.gauss(gm_comp_bps, gm_sigma)
            sample_opex_inf = rng.gauss(opex_inf_pct, opex_sigma)
            sample_dso_exp = rng.gauss(dso_exp_days, dso_sigma)

            pf = self._calculate_pro_forma(
                baseline=baseline,
                rev_shock_pct=sample_rev_shock,
                gm_comp_bps=sample_gm_comp,
                opex_inf_pct=sample_opex_inf,
                dso_exp_days=sample_dso_exp,
            )
            simulated_fcf.append(pf.shocked_fcf)

        simulated_fcf.sort()

        # Summary statistics
        mean_fcf = sum(simulated_fcf) / n_runs
        median_fcf = simulated_fcf[n_runs // 2]
        variance = sum((x - mean_fcf) ** 2 for x in simulated_fcf) / n_runs
        std_dev = math.sqrt(variance)

        min_fcf = simulated_fcf[0]
        max_fcf = simulated_fcf[-1]

        # Value at Risk: 5th and 1st percentiles
        idx_95 = max(0, int(0.05 * n_runs))
        idx_99 = max(0, int(0.01 * n_runs))

        var_95 = simulated_fcf[idx_95]
        var_99 = simulated_fcf[idx_99]

        # Conditional VaR (Expected Shortfall): Mean of worst 5% outcomes
        tail_count = max(1, idx_95)
        cvar_95 = sum(simulated_fcf[:tail_count]) / tail_count

        negative_runs = sum(1 for x in simulated_fcf if x < 0)
        prob_neg_fcf = round(negative_runs / n_runs, 4)

        # Histogram generation: 20 bins
        num_bins = 20
        span = max(1.0, max_fcf - min_fcf)
        bin_width = span / num_bins

        histogram_bins: list[HistogramBin] = []
        bin_counts = [0] * num_bins

        for val in simulated_fcf:
            idx = int((val - min_fcf) / bin_width)
            if idx >= num_bins:
                idx = num_bins - 1
            bin_counts[idx] += 1

        for i in range(num_bins):
            b_start = min_fcf + i * bin_width
            b_end = b_start + bin_width
            b_center = (b_start + b_end) / 2.0
            count = bin_counts[i]
            density = count / (n_runs * bin_width) if bin_width > 0 else 0.0
            histogram_bins.append(
                HistogramBin(
                    bin_start=round(b_start, 2),
                    bin_end=round(b_end, 2),
                    bin_center=round(b_center, 2),
                    count=count,
                    density=round(density, 6),
                )
            )

        return MonteCarloResult(
            runs=n_runs,
            mean_fcf=round(mean_fcf, 2),
            median_fcf=round(median_fcf, 2),
            std_dev=round(std_dev, 2),
            min_fcf=round(min_fcf, 2),
            max_fcf=round(max_fcf, 2),
            var_95=round(var_95, 2),
            var_99=round(var_99, 2),
            cvar_95=round(cvar_95, 2),
            prob_negative_fcf=prob_neg_fcf,
            histogram_bins=histogram_bins,
        )

    def _generate_commentary(
        self,
        baseline: BaselineFinancials,
        pro_forma: ProFormaMetrics,
        monte_carlo: MonteCarloResult,
        preset_name: str,
    ) -> AICommentary:
        """Synthesize institutional AI commentary with credit rating implications and mitigation roadmap."""
        fcf_drawdown_pct = abs(pro_forma.fcf_delta / baseline.free_cash_flow * 100.0) if baseline.free_cash_flow else 0

        # Assess credit/capital buffer rating impact
        if pro_forma.shocked_fcf <= 0 or fcf_drawdown_pct > 50.0:
            rating_impact = "Severe Downgrade Risk"
        elif fcf_drawdown_pct > 25.0:
            rating_impact = "Moderate Outlook Revision"
        else:
            rating_impact = "Stable Buffer"

        # Runway calculation: assumes $15B cash buffer for mega-caps
        cash_buffer = 15000.0
        monthly_burn = abs(pro_forma.shocked_fcf) / 12.0 if pro_forma.shocked_fcf < 0 else 0.0
        runway_months = 999.0 if monthly_burn == 0 else round(cash_buffer / monthly_burn, 1)

        summary = (
            f"Institutional stress test under the '{preset_name}' scenario projects a "
            f"${abs(pro_forma.revenue_delta):,.0f}M ({pro_forma.revenue_delta_pct:.1f}%) top-line shock "
            f"and {abs(pro_forma.gross_margin_delta_bps):.0f} bps gross margin compression. Pro-forma Free Cash Flow "
            f"contracts from ${baseline.free_cash_flow:,.0f}M to ${pro_forma.shocked_fcf:,.0f}M, representing a "
            f"{fcf_drawdown_pct:.1f}% liquidity drawdown. Monte Carlo tail simulation (1,000 iterations) indicates "
            f"a 95% Value-at-Risk (VaR) floor of ${monte_carlo.var_95:,.0f}M with a "
            f"{monte_carlo.prob_negative_fcf * 100:.1f}% probability of negative cash generation."
        )

        base_ebit_pct = (baseline.ebit / baseline.revenue * 100.0) if baseline.revenue else 0.0
        vulnerabilities = [
            (
                f"Working capital drag of ${pro_forma.working_capital_drag:,.0f}M immobilized "
                "due to extended customer collection cycles."
            ),
            (
                f"Operating leverage deleveraging: EBIT margin declines from "
                f"{base_ebit_pct:.1f}% to {pro_forma.ebit_margin * 100:.1f}%."
            ),
            (
                f"5% tail risk outcome (Expected Shortfall / CVaR 95%) projects adverse FCF generation "
                f"down to ${monte_carlo.cvar_95:,.0f}M."
            ),
        ]

        mitigations = [
            "Execute bilateral foundry multi-sourcing and take-or-pay wafer pre-allocation covenants.",
            (
                "Implement synthetic receivable factoring facilities to arrest DSO blowout and "
                "preserve $2.5B+ working capital."
            ),
            "Establish dynamic variable capex throttle indexed to trailing quarterly order-to-bill velocity.",
            "Initiate structural hedge collar on high-bandwidth memory (HBM) procurement prices.",
        ]

        return AICommentary(
            scenario_name=preset_name,
            executive_summary=summary,
            key_vulnerabilities=vulnerabilities,
            mitigation_actions=mitigations,
            capital_rating_impact=rating_impact,
            liquidity_runway_months=runway_months,
        )
