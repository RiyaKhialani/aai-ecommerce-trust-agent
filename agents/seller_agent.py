"""
Agent 6: Seller Behavior Pattern Agent
Compares current seller activity against known fraud/counterfeit behavior patterns.
Checks account age vs review velocity ratio, listing churn, authorized distribution, and pricing anomalies.
Computes Seller Reliability Score (0.0 to 1.0).
"""

from typing import Dict, Any, List, Tuple
from agents.schemas import ProductListing


class SellerBehaviorAgent:
    def __init__(self):
        self.agent_id = 6
        self.name = "Seller Behavior Pattern Agent"

    def execute(self, listing: ProductListing) -> Tuple[float, List[str], Dict[str, Any]]:
        flags: List[str] = []
        score = 1.0
        review_count = len(listing.reviews)
        account_age_days = listing.seller_account_age_days

        # 1. New-Account Review Inflation Ratio
        reviews_per_day = review_count / max(1, account_age_days)
        if account_age_days < 30 and review_count > 100:
            flags.append(
                f"New-Account Review Inflation: Seller created {account_age_days} days ago, "
                f"already accumulated {review_count} reviews ({round(reviews_per_day, 1)} reviews/day)."
            )
            score -= 0.40
        elif account_age_days < 60 and review_count > 200:
            flags.append(
                f"Elevated Review Velocity: {review_count} reviews in {account_age_days} days."
            )
            score -= 0.20

        # 2. Sudden Price Crash / Dumping Behavior (or massive discount vs MRP)
        if len(listing.price_history) >= 2:
            initial_price = listing.price_history[0]["price"]
            latest_price = listing.price_history[-1]["price"]
            if initial_price > 0 and latest_price <= (initial_price * 0.4):
                drop_pct = round(((initial_price - latest_price) / initial_price) * 100)
                flags.append(
                    f"Drastic Price Crash ({drop_pct}% markdown from ₹{initial_price:,.0f} to ₹{latest_price:,.0f}): "
                    f"Typical of counterfeit clearance dumping."
                )
                score -= 0.35

        # 3. Unauthorized Merchant Selling Exclusive Import Brand
        seller_lower = listing.seller_name.lower()
        brand_lower = listing.brand.lower()
        if "rhode" in brand_lower and "official" not in seller_lower:
            flags.append(
                f"Unauthorized Distribution Channel: Merchant '{listing.seller_name}' is an unauthorized "
                f"reseller for exclusive import brand '{listing.brand}'."
            )
            score -= 0.30

        # 4. Disposable shell merchant indicators
        if any(term in seller_lower for term in ["global", "direct", "quickmart", "flashmart", "superdeal", "textiles"]):
            if account_age_days < 45 or "rhode" in brand_lower:
                flags.append("Entity matches shell reseller profile commonly associated with unauthorized cosmetic imports.")
                score -= 0.15

        seller_score = max(0.1, min(1.0, round(score, 2)))
        meta = {
            "seller_id": listing.seller_id,
            "seller_name": listing.seller_name,
            "account_age_days": account_age_days,
            "reviews_per_day": round(reviews_per_day, 1),
            "seller_score": seller_score
        }

        return seller_score, flags, meta
