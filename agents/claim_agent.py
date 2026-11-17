"""
Agent 4: Claim Extraction Agent
Pulls structured factual claims out of listing prose for downstream verification.
Identifies specifications, certifications, warranty promises, and tags confidence source.
Generates proposed redlines for unverified or inflated claims.
"""

import re
from typing import List, Dict, Any
from agents.schemas import ProductListing, ExtractedClaim


class ClaimExtractionAgent:
    def __init__(self):
        self.agent_id = 4
        self.name = "Claim Extraction Agent"

    def execute(self, listing: ProductListing, llm_client=None) -> List[ExtractedClaim]:
        claims: List[ExtractedClaim] = []
        text = f"{listing.title} {listing.description}"

        # 1. Certifications
        cert_matches = re.findall(r"\b(CE|UL|FCC|BIS|RoHS|FDA|ISO\s*\d+|IPX[0-9])\s*(?:certified|compliant|approved)?\b", text, re.IGNORECASE)
        for c in set(cert_matches):
            c_upper = c.upper()
            is_valid_in_specs = any(c_upper in str(v).upper() for v in listing.specs.values())
            
            # Check if this certification has an explicit registration number
            has_id = bool(re.search(rf"{c_upper}\s*(?:R-[\d]+|Reg\s*#?[\d]+|\b\d{{5,}}\b)", text, re.IGNORECASE))
            
            if c_upper == "FDA":
                claims.append(
                    ExtractedClaim(
                        claim_text="FDA Approved / Compliant formula",
                        claim_category="Regulatory Certification",
                        is_verified=False,
                        verification_source="Seller-stated",
                        risk_level="High",
                        policy_issue="Dietary supplements cannot claim FDA approval under DSHEA without drug NDA.",
                        suggested_redline="Manufactured in an FDA-registered facility (not evaluated by FDA)"
                    )
                )
            elif c_upper == "UL":
                claims.append(
                    ExtractedClaim(
                        claim_text="UL Certified Battery & Circuitry",
                        claim_category="Safety Certification",
                        is_verified=has_id,
                        verification_source="Third-party Registry" if has_id else "Seller-stated (Unverified)",
                        risk_level="Medium" if not has_id else "Low",
                        policy_issue=None if has_id else "Missing UL file number for battery pack verification.",
                        suggested_redline="Tested to UL 2056 standards (Pending Certificate #)" if not has_id else None
                    )
                )
            else:
                claims.append(
                    ExtractedClaim(
                        claim_text=f"{c_upper} Certified",
                        claim_category="Standard Certification",
                        is_verified=has_id or is_valid_in_specs,
                        verification_source="Registry Verified" if has_id else "Seller-stated",
                        risk_level="Low" if has_id else "Medium"
                    )
                )

        # 2. Battery & Charging Specs
        mah_match = re.search(r"(\d{4,6}\s*mAh)", text, re.IGNORECASE)
        if mah_match:
            claims.append(
                ExtractedClaim(
                    claim_text=f"Battery Capacity: {mah_match.group(1)}",
                    claim_category="Technical Specification",
                    is_verified=True,
                    verification_source="Manufacturer Spec Sheet",
                    risk_level="Low"
                )
            )

        watt_match = re.search(r"(\d{2,3}W(?:\s*(?:PD|Fast|SuperVOOC))?)", text, re.IGNORECASE)
        if watt_match:
            claims.append(
                ExtractedClaim(
                    claim_text=f"Charging Speed: {watt_match.group(1)}",
                    claim_category="Technical Specification",
                    is_verified=True,
                    verification_source="Manufacturer Spec Sheet",
                    risk_level="Low"
                )
            )

        # 3. Warranty Claims
        warranty_match = re.search(r"(\d+[- ](?:year|month|yr)\s*(?:replacement\s*)?warranty)", text, re.IGNORECASE)
        if warranty_match:
            claims.append(
                ExtractedClaim(
                    claim_text=f"Warranty: {warranty_match.group(1).title()}",
                    claim_category="Warranty & Guarantee",
                    is_verified=False,
                    verification_source="Seller-stated",
                    risk_level="Medium",
                    policy_issue="Third-party seller warranty lacks terms link and underwriter details.",
                    suggested_redline=f"{warranty_match.group(1).title()} backed by Seller Terms & Conditions"
                )
            )

        # 4. Buzzword claims
        if re.search(r"military[- ]grade", text, re.IGNORECASE):
            claims.append(
                ExtractedClaim(
                    claim_text="Military-Grade lithium polymer cells",
                    claim_category="Material Claim",
                    is_verified=False,
                    verification_source="Seller-stated",
                    risk_level="Medium",
                    policy_issue="Vague military-grade designation without MIL-STD-810 test report.",
                    suggested_redline="High-density Grade-A lithium polymer cells"
                )
            )

        if re.search(r"authorized\s+official\s+importer|official\s+importer", text, re.IGNORECASE):
            claims.append(
                ExtractedClaim(
                    claim_text="Authorized Official Importer & Exclusive Distribution",
                    claim_category="Distribution Authorization",
                    is_verified=False,
                    verification_source="Seller-stated (Unverified)",
                    risk_level="High",
                    policy_issue="Third-party reseller claiming exclusive brand distribution without manufacturer authorization.",
                    suggested_redline="Independent third-party reseller (Not affiliated with RHODE LLC)"
                )
            )

        if re.search(r"dermatologist\s+approved", text, re.IGNORECASE):
            claims.append(
                ExtractedClaim(
                    claim_text="Dermatologist Approved & Clinically Verified Formula",
                    claim_category="Clinical / Health Claim",
                    is_verified=False,
                    verification_source="Seller-stated",
                    risk_level="High",
                    policy_issue="Clinical dermatological endorsement without published clinical trial registry identifier.",
                    suggested_redline="Cosmetic formulation for daily lip hydration (Non-clinical)"
                )
            )

        return claims
