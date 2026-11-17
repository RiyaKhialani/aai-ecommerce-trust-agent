"""
Agent 8: Risk Scoring & Aggregation Agent
Combines signals from all detection agents into a single weighted trust score (0 to 100).
Categorizes listing into Low, Medium, and High risk tiers and compiles itemized evidence records.
"""

from typing import Dict, Any, List, Tuple
from agents.schemas import ProductListing, EvidenceItem, ExtractedClaim


class RiskScoringAggregationAgent:
    def __init__(self):
        self.agent_id = 8
        self.name = "Risk Scoring & Aggregation Agent"

        # Signal weights (total = 1.0)
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
        extracted_claims: List[ExtractedClaim]
    ) -> Tuple[float, str, List[EvidenceItem]]:

        # Weighted calculation
        raw_weighted = (
            (compliance_score * self.weight_compliance) +
            (authenticity_score * self.weight_authenticity) +
            (seller_score * self.weight_seller) +
            (image_score * self.weight_image)
        )

        overall_trust_score = round(raw_weighted * 100, 1)

        # Risk tier assignment
        if overall_trust_score >= 75.0:
            risk_tier = "LOW RISK"
        elif overall_trust_score >= 50.0:
            risk_tier = "MEDIUM RISK"
        else:
            risk_tier = "HIGH RISK"

        # Itemized evidence compilation
        evidence: List[EvidenceItem] = []

        # 0. Direct Customer Counterfeit / Fake Reports
        for r in listing.reviews:
            full_r = f"{r.title} {r.text}".lower()
            if any(term in full_r for term in ["fake product", "scam product", "counterfeit", "duplicate", "not safe to use"]):
                evidence.append(
                    EvidenceItem(
                        module="Direct Buyer Counterfeit Alert",
                        item_detected=f"Verified Buyer Report: \"{r.title}\"",
                        issue="Customers explicitly report receiving a fake/counterfeit and unsafe product",
                        risk_level="Critical",
                        explanation=f"Customer review confirms: \"{r.text[:160]}\"",
                        recommendation="Immediate marketplace catalog suspension and mandatory proof of authorization audit."
                    )
                )
                break

        # 1. Review Velocity Spike evidence
        if spike_info.get("spike_detected"):
            evidence.append(
                EvidenceItem(
                    module="Review Velocity Monitor",
                    item_detected=f"Review velocity spike: {spike_info.get('spike_count')} reviews in 48h ({spike_info.get('time_window')})",
                    issue="Unnatural burst volume exceeding baseline sales velocity by >3x",
                    risk_level="High",
                    explanation="Burst pattern + phrase duplication matches known incentivized-review manipulation signature.",
                    recommendation="Flag for manual seller audit; withhold 'Amazon's Choice' or verified badge pending audit."
                )
            )

        # 2. Phrasing duplication evidence
        if duplicate_phrases:
            phrases_str = ", ".join([f'"{p["phrase"]}" ({p["count"]} times)' for p in duplicate_phrases[:3]])
            evidence.append(
                EvidenceItem(
                    module="Review Authenticity Detector",
                    item_detected=f"Duplicate review templates detected: {phrases_str}",
                    issue="Multiple reviews across distinct accounts share identical sentence structure",
                    risk_level="High",
                    explanation="High clustering of repeated praise indicates automated bot generation or paid reviewer rings.",
                    recommendation="Quarantine reviews matching template hash and recalculate organic star rating."
                )
            )

        # 3. Compliance violations evidence
        for v in compliance_violations:
            if isinstance(v, dict):
                v_term = v.get("term", "Policy breach")
                v_issue = v.get("issue", "Policy violation")
                v_sev = v.get("severity", "Medium")
                v_cat = v.get("category", "Restricted Claims")
            else:
                v_term = str(v)
                v_issue = str(v)
                v_sev = "High" if any(w in str(v).lower() for w in ["cure", "fda", "prohibited", "illegal"]) else "Medium"
                v_cat = "Statutory Compliance"

            evidence.append(
                EvidenceItem(
                    module="Policy Compliance Classifier",
                    item_detected=f"Restricted term: \"{v_term}\"",
                    issue=v_issue,
                    risk_level=v_sev,
                    explanation=f"Product copy breaches marketplace catalog policy in category '{v_cat}'.",
                    recommendation="Apply catalog content warning and require seller to submit approved label documentation."
                )
            )

        # 4. Seller behavior evidence
        for flag in seller_flags:
            evidence.append(
                EvidenceItem(
                    module="Seller Behavioral Intelligence",
                    item_detected="Seller anomaly detected",
                    issue=flag,
                    risk_level="High" if "Inflation" in flag or "Crash" in flag else "Medium",
                    explanation="Seller velocity profile is inconsistent with organic merchant growth curves.",
                    recommendation="Place seller payout on 14-day hold pending identity and inventory verification."
                )
            )

        # 5. Image & counterfeit signals
        for iflag in image_flags:
            evidence.append(
                EvidenceItem(
                    module="Counterfeit & Image Inspector",
                    item_detected="Image anomaly",
                    issue=iflag,
                    risk_level="Medium",
                    explanation="Asset fingerprints indicate non-exclusive or synthetic media sourcing.",
                    recommendation="Request original product photography with serial number stamp."
                )
            )

        # If clean
        if not evidence:
            evidence.append(
                EvidenceItem(
                    module="Integrity Verification",
                    item_detected="Normal baseline operation",
                    issue="No significant policy, velocity, or seller anomalies detected",
                    risk_level="Low",
                    explanation="Listing patterns, review velocity curve, and seller account longevity adhere to marketplace trust guidelines.",
                    recommendation="Maintain standard catalog placement and badge eligibility."
                )
            )

        return overall_trust_score, risk_tier, evidence
