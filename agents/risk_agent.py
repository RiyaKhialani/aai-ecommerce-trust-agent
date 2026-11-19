"""
Agent 8: Risk Scoring & Aggregation Agent
Aggregates the four specialist agent scores using a transparent weighted formula:
    Trust Score = 100 * (0.25 * Compliance + 0.35 * Authenticity + 0.25 * Seller + 0.15 * Image)
Assigns risk tiers (LOW / MEDIUM / HIGH RISK) and compiles itemized evidence records.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from agents.schemas import EvidenceItem, ExtractedClaim, ProductListing


class RiskScoringAggregationAgent:
    def __init__(self) -> None:
        self.agent_id = 8
        self.name = "Risk Scoring & Aggregation Agent"
        self.weight_compliance = 0.25
        self.weight_authenticity = 0.35
        self.weight_seller = 0.25
        self.weight_image = 0.15

    def execute(
        self,
        listing: ProductListing,
        compliance_score: float,
        compliance_violations: List[Dict[str, Any]],
        authenticity_score: float,
        duplicate_phrases: List[Dict[str, Any]],
        spike_info: Dict[str, Any],
        seller_score: float,
        seller_flags: List[str],
        image_score: float,
        image_flags: List[str],
        extracted_claims: List[ExtractedClaim],
    ) -> Tuple[float, str, List[EvidenceItem]]:
        raw_weighted = (
            compliance_score * self.weight_compliance
            + authenticity_score * self.weight_authenticity
            + seller_score * self.weight_seller
            + image_score * self.weight_image
        )
        overall_trust_score = round(raw_weighted * 100.0, 1)

        if overall_trust_score >= 75.0:
            risk_tier = "LOW RISK"
        elif overall_trust_score >= 50.0:
            risk_tier = "MEDIUM RISK"
        else:
            risk_tier = "HIGH RISK"

        evidence: List[EvidenceItem] = []

        # 1. Compliance Violations
        for v in compliance_violations:
            evidence.append(
                EvidenceItem(
                    module="Agent 3: Listing Compliance",
                    item_detected=str(v.get("term") or v.get("category") or "Policy Claim"),
                    issue=str(v.get("issue") or "Policy violation flagged"),
                    risk_level=str(v.get("severity") or "Medium"),
                    explanation=f"Flagged under {v.get('category', 'Compliance Policy')}.",
                    recommendation="Require merchant documentation or enforce claim redline before publishing.",
                )
            )

        # 2. Review Velocity Burst
        if spike_info.get("spike_detected"):
            evidence.append(
                EvidenceItem(
                    module="Agent 2: Review Cohorts",
                    item_detected=f"Velocity Spike ({spike_info.get('time_window', 'Recent')})",
                    issue=str(spike_info.get("warning") or "Abnormal review burst detected"),
                    risk_level="High",
                    explanation=(
                        f"{spike_info.get('spike_count')} reviews vs {spike_info.get('baseline_average')} baseline "
                        f"({spike_info.get('multiplier')}x multiplier)."
                    ),
                    recommendation="Hold promotional badges and audit reviewer cohort authenticity.",
                )
            )

        # 3. Duplicate Review Phrases
        if duplicate_phrases:
            top_phrases = ", ".join(f"'{p['phrase']}' ({p['count']}x)" for p in duplicate_phrases[:3])
            evidence.append(
                EvidenceItem(
                    module="Agent 5: Review Authenticity",
                    item_detected="Repeated 4-Gram Phrase Clusters",
                    issue=f"Templated phrasing across multiple reviews: {top_phrases}",
                    risk_level="High" if len(duplicate_phrases) >= 3 else "Medium",
                    explanation="Exact multi-word sequences repeated across distinct reviews indicate potential review manipulation.",
                    recommendation="Flag review cluster for Trust & Safety anti-spam investigation.",
                )
            )

        # 4. Seller Behavior Flags
        for sf in seller_flags:
            is_high = any(k in sf.lower() for k in ["inflation", "dumping", "unauthorized"])
            evidence.append(
                EvidenceItem(
                    module="Agent 6: Seller Behavior",
                    item_detected=f"Merchant: {listing.seller_name}",
                    issue=sf,
                    risk_level="High" if is_high else "Medium",
                    explanation="Derived from merchant pricing, tenure, and storefront metadata.",
                    recommendation="Verify authorized distributor invoices and seller KYC history.",
                )
            )

        # 5. Image & Packaging Signals
        for imf in image_flags:
            is_high = "defect" in imf.lower() or "counterfeit" in imf.lower()
            evidence.append(
                EvidenceItem(
                    module="Agent 7: Image & Packaging Signal",
                    item_detected="Listing Visual / Packaging Audit",
                    issue=imf,
                    risk_level="High" if is_high else "Medium",
                    explanation="Derived from listing media availability and buyer packaging reports.",
                    recommendation="Request high-resolution batch-code and packaging certification photos.",
                )
            )

        # 6. High-Risk Unverified Claims
        for cl in extracted_claims:
            if not cl.is_verified and cl.risk_level in ("High", "Medium") and cl.policy_issue:
                evidence.append(
                    EvidenceItem(
                        module="Agent 4: Claim Extraction",
                        item_detected=cl.claim_text,
                        issue=cl.policy_issue,
                        risk_level=cl.risk_level,
                        explanation=f"Verification status: {cl.verification_source}.",
                        recommendation=f"Redline to: {cl.suggested_redline}" if cl.suggested_redline else "Request third-party certificate.",
                    )
                )

        return overall_trust_score, risk_tier, evidence
