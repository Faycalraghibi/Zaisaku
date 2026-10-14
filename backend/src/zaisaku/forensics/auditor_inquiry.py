"""Adversarial Big 4 / SEC Enforcement Cross-Examination Studio for forensic accounting."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CrossExamineRequest(BaseModel):
    """Payload to trigger adversarial audit cross-examination."""

    ticker: str = Field(default="NVDA", description="Stock ticker symbol")


class AuditorQuestion(BaseModel):
    """Adversarial forensic inquiry challenging corporate accounting disclosures."""

    id: str
    topic: str
    severity: str = Field(
        ...,
        description="'CRITICAL_DEFICIENCY', 'MATERIAL_WEAKNESS_RISK', 'SUBPOENA_VULNERABILITY', etc.",
    )
    interrogation_prompt: str
    management_defense_posture: str
    required_evidentiary_documents: list[str]
    recommended_counsel_rebuttal: str
    statutory_rule_citation: str


class AuditorCrossExamineResponse(BaseModel):
    """Complete adversarial auditor cross-examination dossier."""

    ticker: str
    company_name: str
    audit_firm: str
    risk_index: int = Field(..., ge=0, le=100)
    overall_posture: str
    inquiries: list[AuditorQuestion]
    enforcement_risk_summary: str


class AuditorCrossExaminer:
    """Adversarial forensic simulator challenging management accounting disclosures."""

    def cross_examine(self, request: CrossExamineRequest) -> AuditorCrossExamineResponse:
        """Generate high-intensity legal cross-examination based on company filings."""
        t = request.ticker.strip().upper()
        if t == "NVDA":
            return self._nvda_cross_examination()
        if t == "AAPL":
            return self._aapl_cross_examination()
        return self._generic_cross_examination(t)

    def _nvda_cross_examination(self) -> AuditorCrossExamineResponse:
        inquiries = [
            AuditorQuestion(
                id="inq_rev_cutoff",
                topic="Bill-and-Hold & Channel Transfer of Control",
                severity="SUBPOENA_VULNERABILITY",
                interrogation_prompt=(
                    "Under ASC 606-10-55-83, revenue cannot be recognized prior to physical transfer of control unless "
                    "all four bill-and-hold criteria are rigorously substantiated. Given that Customer A represents "
                    "13% of total revenue and products were staged at third-party overseas distribution hubs in Taiwan "
                    "and Singapore prior to customs clearance, by what specific legal mechanism did management verify "
                    "that the customer obtained the substantive ability to direct the use of and obtain substantially "
                    "all remaining benefits from the hardware?"
                ),
                management_defense_posture="Vulnerable to Reclassification",
                required_evidentiary_documents=[
                    "Signed Customer Bilateral Acceptance Certificates",
                    "Third-party ODM Warehouse Transfer Slips",
                    "FOB Shipping Point Invoices with Specific Risk-of-Loss Endorsements",
                    "Customer Inspection Waiver Memoranda",
                ],
                recommended_counsel_rebuttal=(
                    "Substantiate that title and risk of loss transferred at FOB origin point under master purchase "
                    "agreement Section 14.2, and that buyer has separate custodial contracts."
                ),
                statutory_rule_citation="ASC 606-10-25-14 & ASC 606-10-55-83 (Bill-and-Hold Arrangements)",
            ),
            AuditorQuestion(
                id="inq_customer_subsidies",
                topic="Related-Party Equity Stakes & Customer Reciprocal Arrangements",
                severity="CRITICAL_DEFICIENCY",
                interrogation_prompt=(
                    "SEC Regulation S-X Rule 4-08(k) mandates comprehensive disclosure of material related-party "
                    "transactions, including direct or indirect equity stakes in commercial customers. Management "
                    "participated in convertible debt and venture equity funding rounds for emerging cloud "
                    "hyperscaler and AI startup customers. Were any GPU hardware purchases conditioned, directly or "
                    "indirectly, upon management's co-investment covenants or vendor cloud-credit grants?"
                ),
                management_defense_posture="Under-Disclosed Reciprocal Commitments",
                required_evidentiary_documents=[
                    "Corporate Venture Capital (NVentures) Term Sheets",
                    "Side Letters and Commercial GPU Supply Reservation Agreements",
                    "Cloud Credit Grant Valuations and ASC 606-10-32-25 Consideration Payable analyses",
                    "Independent Fair Market Value (FMV) Appraisals",
                ],
                recommended_counsel_rebuttal=(
                    "Demonstrate that venture capital investments were executed at arm's length by separate investment "
                    "committees without preferential hardware delivery side letters or pricing concessions."
                ),
                statutory_rule_citation="SEC Regulation S-X Rule 4-08(k) & ASC 850 (Related Party Disclosures)",
            ),
            AuditorQuestion(
                id="inq_fab_commitments",
                topic="Off-Balance Sheet Take-or-Pay Purchase Commitments",
                severity="MATERIAL_WEAKNESS_RISK",
                interrogation_prompt=(
                    "Note 13 discloses multi-billion dollar non-cancelable inventory purchase obligations and "
                    "long-term wafer supply commitments with leading foundries. If end-market demand undergoes a "
                    "cyclical digestion phase, under ASC 330-10-S99-2, what is the maximum unreserved loss exposure "
                    "if management cannot draw the contractual wafer allocations, and why has no accrual for firm "
                    "purchase commitment loss been recorded?"
                ),
                management_defense_posture="Defensible Pending Market Demand",
                required_evidentiary_documents=[
                    "Master Foundry Wafer Supply Agreements (Take-or-Pay Schedules)",
                    "Rolling 8-Quarter Bottom-Up Demand Forecasting Models",
                    "ASC 330 Inventory Firm Purchase Commitment Impairment Workpapers",
                    "Contractual Termination Penalty Matrices",
                ],
                recommended_counsel_rebuttal=(
                    "Cite historical backlog visibility, customer advance deposits, and structural demand exceeding "
                    "committed foundry run-rates to prove no net realizable value deficit exists under ASC 330."
                ),
                statutory_rule_citation="ASC 330-10-S99-2 & ASC 440-10-50 (Firm Purchase Commitments)",
            ),
            AuditorQuestion(
                id="inq_inventory_capitalization",
                topic="WIP Packaging Capitalization & Pre-Release Qualification Costs",
                severity="SIGNIFICANT_SCRUTINY",
                interrogation_prompt=(
                    "Work-in-process inventory grew significantly faster than finished goods over trailing quarters. "
                    "Did management capitalize early-spin silicon or advanced packaging wafers that had not yet "
                    "achieved final production qualification signoff, in potential contravention of ASC 330?"
                ),
                management_defense_posture="Defensible with Technical Qualification Signoffs",
                required_evidentiary_documents=[
                    "Engineering Sample (ES) vs Production Silicon Fab Run Orders",
                    "Commercial Tape-Out Signoff Certificates",
                    "Yield Curve Ramp Telemetry Reports",
                    "Quarter-End Physical WIP Reconciliation Audits",
                ],
                recommended_counsel_rebuttal=(
                    "Provide physical yield qualification audit logs certifying that all capitalized wafer WIP met "
                    "commercial specification thresholds prior to inventory recognition."
                ),
                statutory_rule_citation="ASC 330-10-30 (Inventory Cost Basis & Pre-Production Scrutiny)",
            ),
        ]

        summary = (
            "Adversarial cross-examination identifies two elevated scrutiny areas: (1) bill-and-hold transfer of "
            "control verifications across overseas transit staging hubs under ASC 606, and (2) disclosure of "
            "reciprocal cloud venture investments in hardware purchasers under SEC Regulation S-X Rule 4-08(k). "
            "Overall defense posture is defensible provided bilateral shipment title certificates and arm's-length "
            "term sheets are maintained in audit workpapers."
        )

        return AuditorCrossExamineResponse(
            ticker="NVDA",
            company_name="NVIDIA Corporation",
            audit_firm="PricewaterhouseCoopers LLP / PCAOB Enforcement Division",
            risk_index=32,
            overall_posture="Robust Technical Defense / Documentation Substantiation Required",
            inquiries=inquiries,
            enforcement_risk_summary=summary,
        )

    def _aapl_cross_examination(self) -> AuditorCrossExamineResponse:
        inquiries = [
            AuditorQuestion(
                id="inq_aapl_services",
                topic="Services Revenue Gross vs. Net Principal-Agent Accounting",
                severity="CRITICAL_DEFICIENCY",
                interrogation_prompt=(
                    "Under ASC 606-10-55-36 through 55-40, an entity is an agent if it does not control the specified "
                    "good or service before transfer to the customer. On App Store digital transactions, by what "
                    "explicit analysis does management justify recognizing gross transaction commissions while "
                    "developers bear developer refunds, support, and content liability?"
                ),
                management_defense_posture="Established Policy / High Regulatory Scrutiny",
                required_evidentiary_documents=[
                    "Standard Developer License Agreement Terms",
                    "ASC 606 Gross vs Net Technical Accounting Position Papers",
                    "App Store Refund & Chargeback Reserve Analyses",
                ],
                recommended_counsel_rebuttal=(
                    "Reiterate that Apple controls the distribution platform, access rights, payment processing, "
                    "and security protocols, establishing principal control over the marketplace transaction service."
                ),
                statutory_rule_citation="ASC 606-10-55-36 (Principal vs. Agent Considerations)",
            ),
            AuditorQuestion(
                id="inq_aapl_tax",
                topic="Foreign Tax Contingency Reserves & State Aid Litigation",
                severity="MATERIAL_WEAKNESS_RISK",
                interrogation_prompt=(
                    "Following European Court of Justice rulings on historic state-aid tax benefits, what is the "
                    "maximum undisclosed exposure on European IP restructuring, and does the reserve under ASC 740 "
                    "reflect all probable and estimable liabilities?"
                ),
                management_defense_posture="Reserved Under ASC 740",
                required_evidentiary_documents=[
                    "Independent Legal Counsel Audit Inquiry Letters",
                    "ASC 740 Uncertain Tax Position (UTP) Workpapers",
                    "European Commission Decision Notices",
                ],
                recommended_counsel_rebuttal=(
                    "Confirm full settlement escrow deposits eliminate unreserved liability risk."
                ),
                statutory_rule_citation="ASC 740-10 (Income Taxes - Uncertain Tax Positions)",
            ),
        ]

        return AuditorCrossExamineResponse(
            ticker="AAPL",
            company_name="Apple Inc.",
            audit_firm="Ernst & Young LLP / SEC Division of Corporation Finance",
            risk_index=26,
            overall_posture="Established Institutional Defense / Ongoing Antitrust Exposure",
            inquiries=inquiries,
            enforcement_risk_summary=(
                "High regulatory scrutiny focused on App Store gross vs. net accounting and EU tax settlement escrow."
            ),
        )

    def _generic_cross_examination(self, ticker: str) -> AuditorCrossExamineResponse:
        inquiries = [
            AuditorQuestion(
                id=f"inq_{ticker.lower()}_1",
                topic="Revenue Recognition & Quarter-End Cut-Off",
                severity="MATERIAL_WEAKNESS_RISK",
                interrogation_prompt=(
                    f"Under ASC 606, provide evidentiary workpapers proving that {ticker} did not offer "
                    "unwritten side agreements, extended payment concessions, or return rights to accelerate "
                    "quarter-end closing figures."
                ),
                management_defense_posture="Standard Defense",
                required_evidentiary_documents=[
                    "Quarter-End Cut-Off Sampling Tests",
                    "Management Anti-Fraud Confirmation Letters",
                    "Subsequent Period Credit Memo Logs",
                ],
                recommended_counsel_rebuttal="Produce signed standard terms confirming no verbal side covenants exist.",
                statutory_rule_citation="ASC 606-10-25-1",
            ),
            AuditorQuestion(
                id=f"inq_{ticker.lower()}_2",
                topic="Impairment Testing of Goodwill & Long-Lived Assets",
                severity="SIGNIFICANT_SCRUTINY",
                interrogation_prompt=(
                    f"Given recent interest rate increases and macroeconomic compression, what discount rate was "
                    f"applied in {ticker}'s annual ASC 350 goodwill impairment testing, and why was no "
                    "partial write-down recorded?"
                ),
                management_defense_posture="Defensible Pending Valuation Multiples",
                required_evidentiary_documents=[
                    "Third-Party Valuation Specialist DCF Models",
                    "Weighted Average Cost of Capital (WACC) Calculation Worksheets",
                ],
                recommended_counsel_rebuttal="Cite headroom between reporting unit fair value and carrying value.",
                statutory_rule_citation="ASC 350-20-35 (Goodwill Subsequent Measurement)",
            ),
            AuditorQuestion(
                id=f"inq_{ticker.lower()}_3",
                topic="Internal Controls Over Financial Reporting (ICFR) Deficiencies",
                severity="CRITICAL_DEFICIENCY",
                interrogation_prompt=(
                    "Under SOX Section 404, what compensating controls exist to prevent unauthorized manual "
                    "journal entries at period close without secondary supervisory approval?"
                ),
                management_defense_posture="Clean SOX 404 Audit Opinion",
                required_evidentiary_documents=[
                    "IT General Controls (ITGC) User Access Reviews",
                    "Manual Journal Entry Log Approvals",
                ],
                recommended_counsel_rebuttal=(
                    "Demonstrate automated ERP workflow enforcement prohibiting solo journal postings."
                ),
                statutory_rule_citation="SOX Section 404 & PCAOB AS 2201",
            ),
        ]

        return AuditorCrossExamineResponse(
            ticker=ticker,
            company_name=f"{ticker} Corporation",
            audit_firm="Big 4 Independent Audit Committee / SEC Enforcement",
            risk_index=35,
            overall_posture="Standard Audit Scrutiny",
            inquiries=inquiries,
            enforcement_risk_summary=(
                f"Standard forensic inquiries challenging {ticker} on revenue recognition cut-off, goodwill, and ICFR."
            ),
        )
