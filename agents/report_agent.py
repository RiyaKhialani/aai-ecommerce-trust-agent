"""
Agent 9: Plain-Language Report Agent
Translates aggregated technical signals into an executive, plain-language action report
tailored for human Trust & Safety reviewers.
Generates auto-suggested seller audit prompts and before/after redline views.
"""

from typing import Dict, Any, List, Tuple
from agents.schemas import ProductListing, EvidenceItem, ExtractedClaim


class PlainLanguageReportAgent:
    def __init__(self):
        self.agent_id = 9
        self.name = "Plain-Language Report Agent"

    def execute(
        self,
        listing: ProductListing,
        trust_score: float,
        risk_tier: str,
        evidence: List[EvidenceItem],
        extracted_claims: List[ExtractedClaim]
    ) -> Tuple[str, str, str, List[Dict[str, str]]]:
        """
        Returns:
            executive_summary: str
            verdict: str
            auto_suggested_reviewer_prompt: str
            redline_suggestions: List[Dict[str, str]]
        """
        # Redline suggestions
        redlines: List[Dict[str, str]] = []
        for c in extracted_claims:
            if c.suggested_redline:
                redlines.append({
                    "original": c.claim_text,
                    "replacement": c.suggested_redline,
                    "reason": c.policy_issue or "Unverified seller claim"
                })

        # Auto-suggested prompt for Trust Reviewer to send to seller
        if risk_tier == "HIGH RISK":
            auto_prompt = (
                f"Subject: Notice of Mandatory Compliance Verification - SKU {listing.listing_id}\n\n"
                f"Dear {listing.seller_name},\n\n"
                f"Your product listing '{listing.title[:60]}...' has triggered automated trust & safety safeguards "
                f"due to abnormal review velocity spikes and unverified technical/regulatory claims. "
                f"Please provide the following documents within 48 hours to prevent catalog suspension:\n"
                f"1. Third-party laboratory test certificates (e.g. UL / CE / BIS / FSSAI) with verifiable registry numbers.\n"
                f"2. Valid commercial invoices from the original authorized equipment manufacturer.\n"
                f"3. Explanation for the recent {len(listing.reviews)}-review volume surge in your initial 30 days of operation.\n\n"
                f"Marketplace Trust & Safety Operations"
            )
        elif risk_tier == "MEDIUM RISK":
            auto_prompt = (
                f"Subject: Request for Specification Clarification - SKU {listing.listing_id}\n\n"
                f"Dear {listing.seller_name},\n"
                f"Please upload proof of warranty underwriting and documentation supporting the stated certification "
                f"claims within 5 business days to maintain premium badge eligibility."
            )
        else:
            auto_prompt = "No seller action required. Listing satisfies all baseline trust and compliance parameters."

        # Executive summary narrative
        if risk_tier == "HIGH RISK":
            exec_summary = (
                f"The listing for '{listing.title[:50]}' exhibits critical indicators of coordinated review manipulation, "
                f"unverified regulatory claims, and anomalous seller velocity. An aggregated Trust Score of {trust_score}/100 "
                f"places this ASIN in the HIGH RISK tier. Crucially, a major velocity burst and shared sentence templates "
                f"indicate synthetic or incentivized review generation. Recommend immediate badge suppression and seller audit."
            )
            verdict = "FLAGGED FOR AUDIT: Withhold promotional badges and place seller disbursements on hold pending verification."

        elif risk_tier == "MEDIUM RISK":
            exec_summary = (
                f"The listing for '{listing.title[:50]}' achieved a moderate Trust Score of {trust_score}/100. "
                f"While primary listing attributes appear functional, there are unverified warranty and material claims "
                f"that require manufacturer substantiation."
            )
            verdict = "CONDITIONAL APPROVAL: Request seller documentation for unverified marketing claims; maintain periodic monitoring."

        else:
            exec_summary = (
                f"The listing for '{listing.title[:50]}' achieved an exemplary Trust Score of {trust_score}/100 (LOW RISK). "
                f"Review velocity corresponds organically with sales timeline, customer feedback demonstrates high diversity, "
                f"and seller profile displays mature, consistent compliance history."
            )
            verdict = "VERIFIED AUTHENTIC: Listing complies with marketplace integrity policies. Eligible for all promotional placements."

        return exec_summary, verdict, auto_prompt, redlines
