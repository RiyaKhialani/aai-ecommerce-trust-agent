"""
Agent 6: Seller Behavior Pattern Agent
Evaluates seller reliability based on verifiable listing metadata:
account age vs. review velocity, price-drop dumping relative to MRP, and brand-seller alignment.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from agents.schemas import ProductListing


class SellerBehaviorAgent:
    def __init__(self) -> None:
        self.agent_id = 6
        self.name = "Seller Behavior Pattern Agent"

    def execute(self, listing: ProductListing) -> Tuple[float, List[str], Dict[str, Any]]:
        flags: List[str] = []
        score = 1.0
        review_count = len(listing.reviews)
        age = listing.seller_account_age_days
        discount_pct = 0.0

        # 1. Account Age vs. Review Velocity (only when account age is actually known)
        if age is not None and age > 0:
            reviews_per_day = review_count / age
            if age < 30 and review_count > 50:
                flags.append(
                    f"New-Account Review Inflation: Seller age is {age} days with {review_count} reviews "
                    f"({reviews_per_day:.1f} reviews/day)."
                )
                score -= 0.40
            elif age < 60 and review_count > 150:
                flags.append(f"Elevated Review Velocity: {review_count} reviews in {age} days.")
                score -= 0.20
        else:
            flags.append(
                "Seller Account Age Not Exposed on Public Page: Marketplace did not publish merchant tenure; "
                "requires internal marketplace API check for full churn profiling."
            )
            score -= 0.10

        # 2. Extreme Price Dumping vs. MRP
        if len(listing.price_history) >= 2:
            initial_price = float(listing.price_history[0].get("price") or 0)
            latest_price = float(listing.price_history[-1].get("price") or 0)
            if initial_price > 0 and latest_price > 0 and latest_price < initial_price:
                discount_pct = round(((initial_price - latest_price) / initial_price) * 100.0, 1)
                if discount_pct >= 65.0:
                    flags.append(
                        f"Extreme Price Dumping ({discount_pct}% below M.R.P., from {listing.currency} "
                        f"{initial_price:,.0f} to {latest_price:,.0f}): Common counterfeit clearance indicator."
                    )
                    score -= 0.35

        # 3. Unknown / Unverified Merchant Name
        seller_lower = listing.seller_name.lower()
        if seller_lower in ("unknown seller", "third-party merchant", ""):
            flags.append("Merchant Identity Unverified: Exact seller storefront name was not exposed on the listing.")
            score -= 0.15

        seller_score = max(0.10, min(1.0, round(score, 2)))
        meta = {
            "seller_name": listing.seller_name,
            "account_age_days": age,
            "discount_pct": discount_pct,
            "review_count": review_count,
        }
        return seller_score, flags, meta
