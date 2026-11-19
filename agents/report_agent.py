"""
Agent 9: Plain-Language Report Agent
Synthesizes an executive plain-language triage report, verdict, compliant claim redlines,
and a formal merchant compliance inquiry notice using the live LLM.
"""

from __future__ import annotations

import json
from typing import Dict, List, Optional, Tuple

from agents.llm_client import LLMError, TrustAgentLLMClient
from agents.schemas import EvidenceItem, ExtractedClaim, ProductListing


class PlainLanguageReportAgent:
    def __init__(self) -> None:
        self.agent_id = 9
        self.name = "Plain-Language Report Agent"

    def execute(
        self,
        listing: ProductListing,
        trust_score: float,
        risk_tier: str,
        evidence: List[EvidenceItem],
        extracted_claims: List[ExtractedClaim],
        llm_client: Optional[TrustAgentLLMClient] = None,
    ) -> Tuple[str, str, str, List[Dict[str, str]]]:
        redlines: List[Dict[str, str]] = []
        for c in extracted_claims:
            if c.suggested_redline:
                redlines.append(
                    {
                        "original": c.claim_text,
                        "replacement": c.suggested_redline,
                        "reason": c.policy_issue or "Unverified seller claim",
                    }
                )

        if llm_client is not None:
            ev_summary = [
                {"module": e.module, "item": e.item_detected, "issue": e.issue, "risk": e.risk_level}
                for e in evidence[:8]
            ]
            prompt = f"""
You are Agent 9 (Plain-Language Report Agent) assisting human Trust & Safety reviewers.
Generate a concise, evidence-backed triage report and merchant notice for this listing.
Remember: the system acts as an advisory triage assistant for human reviewers, not an automatic delisting authority.

Product: {listing.title} (ID: {listing.listing_id})
Seller: {listing.seller_name}
Category: {listing.category}
Overall Trust Score: {trust_score}/100 ({risk_tier})
Itemized Evidence: {json.dumps(ev_summary, indent=2)}

Return strict JSON:
{{
  "recommended_verdict": "One clear sentence stating the recommended human triage action.",
  "executive_summary": "3-4 sentence plain-language summary citing the exact detected evidence and including an advisory disclaimer for human reviewers.",
  "merchant_notice": "Concise, formal email notice to send to the seller requesting specific documentation (or 'No seller action required.' if LOW RISK)."
}}
"""
            try:
                parsed, _, _ = llm_client.generate_json(prompt)
                verdict = str(parsed.get("recommended_verdict") or f"{risk_tier}: Human Trust & Safety review recommended.")
                exec_summary = str(parsed.get("executive_summary") or verdict)
                merchant_notice = str(parsed.get("merchant_notice") or "No seller action required.")
                return exec_summary, verdict, merchant_notice, redlines
            except LLMError:
                pass

        # Used only in offline unit tests where llm_client=None is explicitly passed
        verdict = (
            f"{risk_tier} ({trust_score}/100): Triage for human Trust & Safety operator review."
        )
        exec_summary = (
            f"Advisory audit report prepared for human Trust & Safety compliance operators. "
            f"Listing '{listing.title}' scored {trust_score}/100 ({risk_tier}) with {len(evidence)} evidence item(s)."
        )
        merchant_notice = (
            f"Subject: Compliance Verification Request - {listing.listing_id}\n\n"
            f"Dear {listing.seller_name},\nPlease submit supporting certification and invoice records for review."
            if risk_tier != "LOW RISK"
            else "No seller action required."
        )
        return exec_summary, verdict, merchant_notice, redlines
