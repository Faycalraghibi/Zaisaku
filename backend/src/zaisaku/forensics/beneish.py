"""Beneish M-Score mathematical model for forensic accounting and earnings manipulation detection."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class BeneishMetrics:
    sales_t: float
    sales_t_prev: float
    cogs_t: float
    cogs_t_prev: float
    receivables_t: float
    receivables_t_prev: float
    current_assets_t: float
    current_assets_t_prev: float
    ppe_t: float
    ppe_t_prev: float
    total_assets_t: float
    total_assets_t_prev: float
    depreciation_t: float
    depreciation_t_prev: float
    sga_t: float
    sga_t_prev: float
    long_term_debt_t: float
    long_term_debt_t_prev: float
    net_income_t: float
    operating_cash_flow_t: float


@dataclass
class BeneishResult:
    m_score: float
    is_manipulator_probable: bool
    risk_level: str  # SAFE, ELEVATED, HIGH_RISK
    indices: dict[str, float]
    flagged_indices: list[str] = field(default_factory=list)
    interpretation: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class BeneishCalculator:
    """Calculates the 8-variable Beneish M-Score (1999) to quantify earnings manipulation probability."""

    THRESHOLD: float = -1.78

    @classmethod
    def calculate(cls, data: BeneishMetrics) -> BeneishResult:
        def safe_div(n: float, d: float, default: float = 1.0) -> float:
            return n / d if d != 0 else default

        # 1. DSRI - Days Sales in Receivables Index
        dsri_curr = safe_div(data.receivables_t, data.sales_t)
        dsri_prev = safe_div(data.receivables_t_prev, data.sales_t_prev)
        dsri = round(safe_div(dsri_curr, dsri_prev), 4)

        # 2. GMI - Gross Margin Index
        gm_prev = safe_div(data.sales_t_prev - data.cogs_t_prev, data.sales_t_prev)
        gm_curr = safe_div(data.sales_t - data.cogs_t, data.sales_t)
        gmi = round(safe_div(gm_prev, gm_curr), 4)

        # 3. AQI - Asset Quality Index
        non_current_curr = 1.0 - safe_div(data.current_assets_t + data.ppe_t, data.total_assets_t)
        non_current_prev = 1.0 - safe_div(data.current_assets_t_prev + data.ppe_t_prev, data.total_assets_t_prev)
        aqi = round(safe_div(non_current_curr, non_current_prev), 4)

        # 4. SGI - Sales Growth Index
        sgi = round(safe_div(data.sales_t, data.sales_t_prev), 4)

        # 5. DEPI - Depreciation Index
        depr_rate_prev = safe_div(data.depreciation_t_prev, data.ppe_t_prev + data.depreciation_t_prev)
        depr_rate_curr = safe_div(data.depreciation_t, data.ppe_t + data.depreciation_t)
        depi = round(safe_div(depr_rate_prev, depr_rate_curr), 4)

        # 6. SGAI - Sales, General & Administrative Expenses Index
        sga_ratio_curr = safe_div(data.sga_t, data.sales_t)
        sga_ratio_prev = safe_div(data.sga_t_prev, data.sales_t_prev)
        sgai = round(safe_div(sga_ratio_curr, sga_ratio_prev), 4)

        # 7. LVGI - Leverage Index
        lev_curr = safe_div(data.long_term_debt_t, data.total_assets_t)
        lev_prev = safe_div(data.long_term_debt_t_prev, data.total_assets_t_prev)
        lvgi = round(safe_div(lev_curr, lev_prev), 4)

        # 8. TATA - Total Accruals to Total Assets
        total_accruals = data.net_income_t - data.operating_cash_flow_t
        tata = round(safe_div(total_accruals, data.total_assets_t), 4)

        # Beneish 8-variable formula:
        m_score = (
            -4.84
            + (0.920 * dsri)
            + (0.528 * gmi)
            + (0.404 * aqi)
            + (0.892 * sgi)
            + (0.115 * depi)
            - (0.172 * sgai)
            + (4.037 * tata)
            + (0.0327 * lvgi)
        )
        m_score = round(m_score, 3)

        is_manipulator = m_score > cls.THRESHOLD
        if m_score > -1.49:
            risk_level = "HIGH_RISK"
        elif m_score > cls.THRESHOLD:
            risk_level = "ELEVATED"
        else:
            risk_level = "SAFE"

        flagged: list[str] = []
        if dsri > 1.2:
            flagged.append("DSRI > 1.2: Accounts receivable grew faster than revenues (Channel Stuffing warning)")
        if gmi > 1.2:
            flagged.append("GMI > 1.2: Gross margins deteriorating, increasing pressure to massage numbers")
        if aqi > 1.25:
            flagged.append("AQI > 1.25: Growing capitalization of operating expenses into non-current assets")
        if depi > 1.2:
            flagged.append("DEPI > 1.2: Depreciation slowed, artificially boosting accounting profit")
        if tata > 0.05:
            flagged.append("TATA > 0.05: Surging accruals with lagging operating cash flow (Earnings Quality Red Flag)")
        if lvgi > 1.25:
            flagged.append("LVGI > 1.25: Rising debt leverage increases financial distress risk")

        indices = {
            "DSRI": dsri,
            "GMI": gmi,
            "AQI": aqi,
            "SGI": sgi,
            "DEPI": depi,
            "SGAI": sgai,
            "LVGI": lvgi,
            "TATA": tata,
        }

        if is_manipulator:
            interpretation = (
                f"Beneish M-Score of {m_score} exceeds the {cls.THRESHOLD} threshold. "
                "Significant probability of aggressive accounting or earnings manipulation."
            )
        else:
            interpretation = (
                f"Beneish M-Score of {m_score} is below the {cls.THRESHOLD} threshold. "
                "Financial reporting exhibits normal earnings quality."
            )

        return BeneishResult(
            m_score=m_score,
            is_manipulator_probable=is_manipulator,
            risk_level=risk_level,
            indices=indices,
            flagged_indices=flagged,
            interpretation=interpretation,
        )
