"""
Agent 3: Listing Compliance Classifier
Checks listing text and origin attributes against marketplace policy guidelines.
Flags prohibited keywords, unverified medical claims, origin/brand discrepancies, and hazardous cosmetic alerts.
"""

import re
from typing import Dict, Any, List, Tuple
from agents.schemas import ProductListing


class ListingComplianceClassifier:
    def __init__(self):
        self.agent_id = 3
        self.name = "Listing Compliance Classifier"

        self.banned_medical_patterns = [
            (r"\bcures?\s+(?:diabetes|cancer|hypertension|covid|obesity|metabolic)\b", "Severe: Prohibited disease cure claim"),
            (r"\bmiracle\b", "Warning: Exaggerated miracle efficacy claim"),
            (r"\bmelt(?:s)?\s+\d+\s*(?:kg|lbs|pounds)\b", "High: Unrealistic rapid weight loss promise"),
            (r"\b100%\s*(?:cure|guarantee|doctor\s+recommended)\b", "High: Unsubstantiated absolute medical claim"),
            (r"\bfda\s+(?:approved|compliant)\b", "Warning: Misuse of regulatory endorsement without NDC/510k registration"),
        ]

        self.restricted_marketing_buzzwords = [
            (r"\bmilitary[- ]grade\b", "Misleading marketing buzzword without defense specification (MIL-STD)"),
            (r"\bspace[- ]grade\b", "Unsubstantiated aerospace grade claim"),
            (r"\bguaranteed\s+safe\s+for\s+flight\b", "Aviation safety claim without IATA/UN38.3 test certs"),
        ]

    def execute(self, listing: ProductListing, llm_client=None) -> Tuple[float, List[Dict[str, Any]]]:
        text = f"{listing.title}\n{listing.description}\n{str(listing.specs)}"
        violations: List[Dict[str, Any]] = []

        # 1. Rule-based policy scan
        for pattern, issue in self.banned_medical_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                violations.append({
                    "category": "Medical / Health Compliance",
                    "term": matches[0],
                    "issue": issue,
                    "severity": "Critical" if "disease" in issue.lower() else "High"
                })

        for pattern, issue in self.restricted_marketing_buzzwords:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                violations.append({
                    "category": "Restricted Jargon / Claims",
                    "term": matches[0],
                    "issue": issue,
                    "severity": "Medium"
                })

        # 2. Brand Origin vs Stated Country of Origin Discrepancy
        origin = listing.specs.get("Country of Origin", "").lower()
        brand_lower = listing.brand.lower()
        if "rhode" in brand_lower and "india" in origin:
            violations.append({
                "category": "Brand Origin Discrepancy",
                "term": f"Brand: {listing.brand} | Stated Origin: India",
                "issue": "High Risk: Rhode Skin is exclusively formulated and distributed in the USA/Europe; domestic Indian manufacture indicates unauthorized replica.",
                "severity": "Critical"
            })

        # 3. Customer Safety Hazard Reports in Reviews
        for r in listing.reviews:
            if re.search(r"\bnot safe to use\b|\bchemical burn\b|\ballergic reaction\b|\btoxic\b", r.text, re.IGNORECASE):
                violations.append({
                    "category": "Consumer Safety Hazard",
                    "term": "Buyer report: 'not safe to use'",
                    "issue": "Critical: Customers explicitly report product is unsafe for cosmetic application.",
                    "severity": "Critical"
                })
                break

        # Calculate compliance score
        score = 1.0
        for v in violations:
            if v["severity"] == "Critical":
                score -= 0.35
            elif v["severity"] == "High":
                score -= 0.20
            elif v["severity"] == "Medium":
                score -= 0.10

        score = max(0.1, min(1.0, round(score, 2)))
        return score, violations
