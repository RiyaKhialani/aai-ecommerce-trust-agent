"""
Agent 3: Listing Compliance Classifier
Combines deterministic regulatory pattern checks (FDA DSHEA, FTC superlatives, UL/BIS marks)
with live LLM compliance auditing.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from agents.llm_client import LLMError, TrustAgentLLMClient
from agents.schemas import ProductListing


class ListingComplianceClassifier:
    def __init__(self) -> None:
        self.agent_id = 3
        self.name = "Listing Compliance Classifier"

        self.banned_medical_patterns = [
            (r"\bcures?\s+(?:diabetes|cancer|hypertension|covid|obesity|metabolic)\b", "Prohibited disease cure claim (FDA DSHEA / Drugs Act)"),
            (r"\bmiracle\b", "Exaggerated efficacy claim ('miracle')"),
            (r"\bmelt(?:s)?\s+\d+\s*(?:kg|lbs|pounds)\b", "Unrealistic rapid weight-loss promise"),
            (r"\b100%\s*(?:cure|guarantee|doctor\s+recommended)\b", "Unsubstantiated absolute medical claim"),
            (r"\bfda\s+(?:approved|compliant)\b", "Potential misuse of FDA endorsement without drug/device registration"),
        ]

        self.restricted_marketing_patterns = [
            (r"\bmilitary[- ]grade\b", "Marketing buzzword without verifiable MIL-STD test report"),
            (r"\bspace[- ]grade\b", "Unsubstantiated aerospace-grade claim"),
            (r"\bguaranteed\s+safe\s+for\s+flight\b", "Aviation battery safety claim without UN38.3 / IATA proof"),
        ]

    def execute(
        self,
        listing: ProductListing,
        llm_client: Optional[TrustAgentLLMClient] = None,
    ) -> Tuple[float, List[Dict[str, Any]], Dict[str, Any]]:
        text = f"{listing.title}\n{listing.description}\n{json.dumps(listing.specs)}"
        violations: List[Dict[str, Any]] = []

        for pattern, issue in self.banned_medical_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                violations.append(
                    {
                        "category": "Medical / Statutory Compliance",
                        "term": str(matches[0]),
                        "issue": issue,
                        "severity": "Critical" if "disease" in issue.lower() else "High",
                    }
                )

        for pattern, issue in self.restricted_marketing_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                violations.append(
                    {
                        "category": "Restricted Marketing Claim",
                        "term": str(matches[0]),
                        "issue": issue,
                        "severity": "Medium",
                    }
                )

        # Deterministic baseline score
        score = 1.0
        for v in violations:
            if v["severity"] == "Critical":
                score -= 0.45
            elif v["severity"] == "High":
                score -= 0.25
            else:
                score -= 0.12
        score = max(0.05, min(1.0, round(score, 2)))

        llm_meta: Dict[str, Any] = {}
        if llm_client is not None:
            prompt = f"""
You are Agent 3 (Listing Compliance Classifier) in an E-Commerce Trust & Safety system.
Audit this product listing for regulatory violations (FDA DSHEA disease claims, unauthorized UL/CE/BIS/FSSAI marks, brand-origin mismatches, or deceptive superlatives).

Title: {listing.title}
Brand: {listing.brand}
Category: {listing.category}
Specs: {json.dumps(listing.specs)}
Description: {listing.description[:1500]}

Return strict JSON:
{{
  "compliance_score": 0.0,
  "violations": [
    {{"category": "Policy Category", "term": "Exact phrase", "issue": "Why it violates policy", "severity": "Low|Medium|High|Critical"}}
  ],
  "rationale": "1-2 sentence audit rationale"
}}
"""
            try:
                parsed, model_used, lat_ms = llm_client.generate_json(prompt)
                if "compliance_score" in parsed:
                    llm_score = max(0.05, min(1.0, float(parsed["compliance_score"])))
                    score = round(min(score, llm_score), 2)
                for item in parsed.get("violations") or []:
                    if isinstance(item, dict) and item.get("issue"):
                        if not any(v["issue"] == item["issue"] for v in violations):
                            violations.append(
                                {
                                    "category": str(item.get("category") or "LLM Policy Audit"),
                                    "term": str(item.get("term") or "Listing Text"),
                                    "issue": str(item["issue"]),
                                    "severity": str(item.get("severity") or "Medium"),
                                }
                            )
                llm_meta = {
                    "model": model_used,
                    "llm_latency_ms": lat_ms,
                    "rationale": parsed.get("rationale", ""),
                }
            except LLMError as exc:
                llm_meta = {
                    "model": "heuristic_fallback",
                    "llm_latency_ms": 0.0,
                    "rationale": f"Deterministic statutory regex audit applied: {exc}",
                }

        return score, violations, llm_meta
