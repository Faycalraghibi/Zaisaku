"""Unit tests for AI Macro Scenario Stress-Tester & Monte Carlo Risk Simulator."""

from zaisaku.forensics.stress_tester import (
    ScenarioStressTester,
    StressSimulationRequest,
)


def test_scenario_presets_loaded():
    """Verify standard institutional macro shock presets are available."""
    tester = ScenarioStressTester()
    presets = tester.get_presets()
    assert len(presets) >= 4
    preset_ids = [p.id for p in presets]
    assert "taiwan_wafer_disruption" in preset_ids
    assert "hyperscaler_capex_pause" in preset_ids
    assert "export_restriction_escalation" in preset_ids
    assert "severe_dso_blowout" in preset_ids


def test_pro_forma_calculation_math():
    """Verify deterministic pro-forma shock calculations against hand-calculated values."""
    tester = ScenarioStressTester()
    baseline = tester.get_baseline_financials("NVDA")
    assert baseline.revenue > 0

    # Test with custom explicit parameters
    request = StressSimulationRequest(
        ticker="NVDA",
        revenue_shock_pct=-15.0,
        gross_margin_compression_bps=-450.0,
        opex_inflation_pct=8.0,
        dso_expansion_days=35.0,
        wacc_increase_bps=125.0,
        n_monte_carlo_runs=500,
        random_seed=42,
    )
    res = tester.simulate(request)

    # Base calculations:
    # shocked_revenue = baseline.revenue * 0.85
    expected_rev = round(baseline.revenue * 0.85, 2)
    assert round(res.pro_forma.shocked_revenue, 2) == expected_rev

    # shocked_gross_margin = baseline.gross_margin - (450 / 10000)
    expected_gm = round(baseline.gross_margin - 0.045, 4)
    assert round(res.pro_forma.shocked_gross_margin, 4) == expected_gm

    # Delta checks
    assert res.pro_forma.revenue_delta == round(res.pro_forma.shocked_revenue - baseline.revenue, 2)
    assert res.pro_forma.ebit_delta < 0
    assert res.pro_forma.fcf_delta < 0
    assert res.pro_forma.working_capital_drag > 0


def test_bounds_and_safety_checks():
    """Verify bounds protection against extreme shocks (e.g. -100% margin)."""
    tester = ScenarioStressTester()
    request = StressSimulationRequest(
        ticker="NVDA",
        revenue_shock_pct=-90.0,
        gross_margin_compression_bps=-10000.0,  # Extreme -100%
        opex_inflation_pct=100.0,
        dso_expansion_days=200.0,
        n_monte_carlo_runs=100,
        random_seed=42,
    )
    res = tester.simulate(request)
    assert res.pro_forma.shocked_gross_margin >= 0.01  # Floor clamped
    assert res.pro_forma.shocked_revenue > 0


def test_sensitivity_matrix_structure():
    """Verify sensitivity 2D matrix contains varying revenue and margin scenarios."""
    tester = ScenarioStressTester()
    request = StressSimulationRequest(
        ticker="NVDA",
        revenue_shock_pct=-10.0,
        gross_margin_compression_bps=-300.0,
        n_monte_carlo_runs=100,
        random_seed=42,
    )
    res = tester.simulate(request)
    assert len(res.sensitivity_matrix) >= 5
    for row in res.sensitivity_matrix:
        assert "revenue_shock_pct" in row
        assert "points" in row
        assert len(row["points"]) >= 4
        for pt in row["points"]:
            assert "margin_compression_bps" in pt
            assert "pro_forma_net_income" in pt
            assert "pro_forma_fcf" in pt


def test_monte_carlo_distribution_statistics():
    """Verify Monte Carlo simulation computes VaR, CVaR, standard deviation, and histogram."""
    tester = ScenarioStressTester()
    request = StressSimulationRequest(
        ticker="NVDA",
        revenue_shock_pct=-15.0,
        gross_margin_compression_bps=-450.0,
        opex_inflation_pct=8.0,
        dso_expansion_days=30.0,
        n_monte_carlo_runs=1000,
        random_seed=123,
    )
    res = tester.simulate(request)
    mc = res.monte_carlo

    assert mc.runs == 1000
    assert mc.mean_fcf < res.baseline.free_cash_flow
    assert mc.var_95 < mc.mean_fcf
    assert mc.var_99 <= mc.var_95
    assert mc.cvar_95 <= mc.var_95
    assert 0.0 <= mc.prob_negative_fcf <= 1.0
    assert len(mc.histogram_bins) >= 15

    # Check histogram totals equal n_runs
    total_frequency = sum(b.count for b in mc.histogram_bins)
    assert total_frequency == 1000


def test_ai_commentary_and_hedging():
    """Verify AI strategic commentary and mitigation playbooks are generated."""
    tester = ScenarioStressTester()
    request = StressSimulationRequest(
        ticker="NVDA",
        scenario_preset_id="taiwan_wafer_disruption",
        n_monte_carlo_runs=100,
    )
    res = tester.simulate(request)
    assert len(res.ai_commentary.executive_summary) > 50
    assert len(res.ai_commentary.key_vulnerabilities) >= 2
    assert len(res.ai_commentary.mitigation_actions) >= 2
    assert res.ai_commentary.capital_rating_impact in [
        "Severe Downgrade Risk",
        "Moderate Outlook Revision",
        "Stable Buffer",
    ]


def test_stress_api_endpoints():
    """Verify GET /presets and POST /simulate endpoints."""
    from fastapi.testclient import TestClient

    from zaisaku.api.app import create_app

    client = TestClient(create_app())

    # Presets endpoint
    res_presets = client.get("/api/forensics/stress/presets")
    assert res_presets.status_code == 200
    presets = res_presets.json()
    assert isinstance(presets, list)
    assert len(presets) >= 4

    # Simulation endpoint
    payload = {
        "ticker": "NVDA",
        "scenario_preset_id": "taiwan_wafer_disruption",
        "n_monte_carlo_runs": 200,
    }
    res_sim = client.post("/api/forensics/stress/simulate", json=payload)
    assert res_sim.status_code == 200
    sim_data = res_sim.json()
    assert sim_data["ticker"] == "NVDA"
    assert "pro_forma" in sim_data
    assert "sensitivity_matrix" in sim_data
    assert "monte_carlo" in sim_data
    assert "ai_commentary" in sim_data
    assert sim_data["monte_carlo"]["runs"] == 200


def test_zero_revenue_baseline_safety():
    """Verify zero division safety when baseline revenue is 0.0."""
    from zaisaku.forensics.stress_tester import (
        BaselineFinancials,
        ScenarioStressTester,
    )

    tester = ScenarioStressTester()
    custom_baseline = BaselineFinancials(
        ticker="PRE_REV",
        period="FY2024",
        revenue=0.0,
        gross_margin=0.0,
        gross_profit=0.0,
        opex=500.0,
        ebit=-500.0,
        tax_rate=0.21,
        net_income=-500.0,
        dso=0.0,
        operating_cash_flow=-450.0,
        capex=50.0,
        free_cash_flow=-500.0,
    )

    # 1. Pro-forma must not divide by zero
    pro_forma = tester._calculate_pro_forma(
        baseline=custom_baseline,
        rev_shock_pct=-20.0,
        gm_comp_bps=-450.0,
        opex_inf_pct=8.0,
        dso_exp_days=30.0,
    )
    assert pro_forma.shocked_revenue == 0.0
    assert pro_forma.revenue_delta == 0.0
    assert pro_forma.revenue_delta_pct == 0.0

    # 2. Commentary generation must not divide by zero
    from zaisaku.forensics.stress_tester import MonteCarloResult

    mock_mc = MonteCarloResult(
        runs=100,
        mean_fcf=-550.0,
        median_fcf=-540.0,
        std_dev=40.0,
        min_fcf=-700.0,
        max_fcf=-400.0,
        var_95=-650.0,
        var_99=-690.0,
        cvar_95=-670.0,
        prob_negative_fcf=1.0,
        histogram_bins=[],
    )
    commentary = tester._generate_commentary(
        baseline=custom_baseline,
        pro_forma=pro_forma,
        monte_carlo=mock_mc,
        preset_name="Stagflationary Supply Squeeze",
    )
    assert isinstance(commentary.key_vulnerabilities, list)
    assert len(commentary.key_vulnerabilities) > 0


