"""
Agent 4: Claim Extraction Agent
Extracts structured factual claims (certifications, specs, warranties, health assertions)
from the listing and proposes compliant before/after redlines via live LLM + regex checks.
"""

from __future__ import annotations

import json
import re
from typing import List, Optional

from agents.llm_client import LLMError, TrustAgentLLMClient
from agents.schemas import ExtractedClaim, ProductListing


class ClaimExtractionAgent:
    def __init__(self) -> None:
        self.agent_id = 4
        self.name = "Claim Extraction Agent"

    def execute(
        self,
        listing: ProductListing,
        llm_client: Optional[TrustAgentLLMClient] = None,
    ) -> List[ExtractedClaim]:
        claims: List[ExtractedClaim] = []
        text = f"{listing.title} {listing.description} {json.dumps(listing.specs)}"

        # 1. Deterministic certification mark extraction
        cert_matches = re.findall(
            r"\b(CE|UL|FCC|BIS|RoHS|FDA|FSSAI|ISO\s*\d+|IPX[0-9])\b",
            text,
            re.IGNORECASE,
        )
        for cert in sorted(set(c.upper() for c in cert_matches)):
            has_reg_id = bool(re.search(rf"{cert}\s*(?:R-[\d]+|Reg\s*#?[\d]+|\b\d{{5,}}\b)", text, re.IGNORECASE))
            if cert == "FDA":
                claims.append(
                    ExtractedClaim(
                        claim_text="FDA Approved / Compliant",
                        claim_category="Regulatory Certification",
                        is_verified=False,
                        verification_source="Seller-stated (Unverified)",
                        risk_level="High",
                        policy_issue="Supplements and cosmetics cannot claim FDA approval without formal NDA/premarket clearance.",
                        suggested_redline="Manufactured in an FDA-registered facility (not evaluated by the FDA)",
                    )
                )
            else:
                claims.append(
                    ExtractedClaim(
                        claim_text=f"{cert} Certified / Compliant",
                        claim_category="Safety / Regulatory Certification",
                        is_verified=has_reg_id,
                        verification_source="Registration # Present" if has_reg_id else "Seller-stated (Unverified)",
                        risk_level="Low" if has_reg_id else "Medium",
                        policy_issue=None if has_reg_id else f"No verifiable {cert} certificate or registration number listed.",
                        suggested_redline=None if has_reg_id else f"Tested to {cert} standards (Registration # pending verification)",
                    )
                )

        # 2. Live LLM structured claim & redline extraction
        if llm_client is not None:
            prompt = f"""
You are Agent 4 (Claim Extraction Agent) in an E-Commerce Trust & Safety pipeline.
Extract up to 5 concrete factual claims (technical specs, certifications, warranty promises, or health/efficacy claims)
explicitly stated in this product listing. For any unverified or policy-violating claim, provide a compliant redline replacement.

Product: {listing.title}
Category: {listing.category}
Specs: {json.dumps(listing.specs)}
Description: {listing.description[:1500]}

Return strict JSON:
{{
  "claims": [
    {{
      "claim_text": "Exact claim from listing",
      "claim_category": "Technical Spec | Regulatory Certification | Warranty | Health/Efficacy",
      "is_verified": false,
      "verification_source": "Seller-stated | Spec Sheet | Unverified",
      "risk_level": "Low | Medium | High",
      "policy_issue": "Concise issue or null",
      "suggested_redline": "Compliant replacement wording or null"
    }}
  ]
}}
"""
            try:
                parsed, _, _ = llm_client.generate_json(prompt)
                seen_texts = {c.claim_text.lower() for c in claims}
                raw_claims = parsed if isinstance(parsed, list) else (parsed.get("claims") if isinstance(parsed, dict) else [])
                for item in raw_claims or []:
                    if not isinstance(item, dict) or not item.get("claim_text"):
                        continue
                    ct = str(item["claim_text"]).strip()
                    if ct.lower() in seen_texts:
                        continue
                    seen_texts.add(ct.lower())
                    claims.append(
                        ExtractedClaim(
                            claim_text=ct,
                            claim_category=str(item.get("claim_category") or "Technical Spec"),
                            is_verified=bool(item.get("is_verified", False)),
                            verification_source=str(item.get("verification_source") or "Seller-stated"),
                            risk_level=str(item.get("risk_level") or "Low"),
                            policy_issue=item.get("policy_issue") or None,
                            suggested_redline=item.get("suggested_redline") or None,
                        )
                    )
            except Exception:
                pass

        return claims
