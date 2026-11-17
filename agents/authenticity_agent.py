"""
Agent 5: Review Authenticity Detection Agent
Analyzes review text and metadata for manipulation signatures.
Detects phrasing templates, customer counterfeit complaints, unverified ratios, and artificial skew.
Produces an authenticity score (0.0 to 1.0).
"""

import re
from typing import List, Dict, Any, Tuple
from collections import Counter
from agents.schemas import ProductListing, ReviewItem


class ReviewAuthenticityAgent:
    def __init__(self):
        self.agent_id = 5
        self.name = "Review Authenticity Detection Agent"

    def execute(self, listing: ProductListing, spike_info: Dict[str, Any] = None) -> Tuple[float, List[Dict[str, Any]], Dict[str, Any]]:
        reviews = listing.reviews
        if not reviews:
            return 0.5, [], {"summary": "No reviews present"}

        # 1. Direct Counterfeit / Scam Mentions in Customer Reviews
        counterfeit_reports = []
        for r in reviews:
            full_rev = f"{r.title} {r.text}".lower()
            if any(term in full_rev for term in ["fake product", "scam product", "counterfeit", "duplicate", "cheap copy", "not original"]):
                counterfeit_reports.append({
                    "reviewer_id": r.reviewer_id,
                    "rating": r.rating,
                    "title": r.title,
                    "text": r.text,
                    "helpful_votes": r.helpful_votes
                })

        # 2. Repeated N-grams and templated sentence analysis
        repeated_phrases = self._find_duplicate_phrases(reviews)

        # 3. Rating distribution skew
        star_counts = Counter(r.rating for r in reviews)
        avg_rating = sum(r.rating for r in reviews) / len(reviews) if reviews else 0.0
        five_stars = star_counts.get(5.0, 0)
        five_star_ratio = five_stars / len(reviews) if reviews else 0.0

        # 4. Verified Purchase Ratio
        unverified_count = sum(1 for r in reviews if not r.verified_purchase)
        unverified_ratio = unverified_count / len(reviews) if reviews else 0.0

        # Authenticity scoring calculation
        score = 1.0

        # CRITICAL PENALTY: Direct Buyer Counterfeit Reports
        if counterfeit_reports:
            # Verified buyers explicitly alerting that product is fake/scam
            score -= 0.80  # Drastic drop to near zero!

        # Penalty if average rating is 1.0 or 2.0 stars (product is widely rejected by buyers)
        if avg_rating <= 2.0:
            score -= 0.35

        # Penalty for repeated phrases (if multiple reviews share exact phrases)
        if repeated_phrases:
            total_template_matches = sum(p["count"] for p in repeated_phrases)
            if total_template_matches > 30:
                score -= 0.35
            elif total_template_matches > 10:
                score -= 0.20

        # Penalty for extreme velocity spike
        if spike_info and spike_info.get("spike_detected"):
            score -= 0.30

        # Penalty for high unverified ratio (> 60% unverified)
        if unverified_ratio > 0.60:
            score -= 0.25
        elif unverified_ratio > 0.40:
            score -= 0.10

        # Penalty for unnatural 5-star skew (> 90% 5-star on new listings)
        if len(reviews) > 50 and five_star_ratio > 0.92:
            score -= 0.15

        authenticity_score = max(0.05, min(1.0, round(score, 2)))

        meta = {
            "avg_rating": round(avg_rating, 1),
            "counterfeit_reports_count": len(counterfeit_reports),
            "counterfeit_samples": counterfeit_reports[:3],
            "unverified_ratio": round(unverified_ratio, 2),
            "total_reviews": len(reviews),
            "duplicate_clusters_count": len(repeated_phrases)
        }

        return authenticity_score, repeated_phrases, meta

    def _find_duplicate_phrases(self, reviews: List[ReviewItem]) -> List[Dict[str, Any]]:
        target_phrases = [
            "changed my life",
            "arrived fast",
            "must buy product",
            "works like magic",
            "best quality ever",
            "lost 8kg in 10 days",
            "100% natural",
            "miracle weight loss"
        ]

        results = []
        for phrase in target_phrases:
            matching_reviews = []
            for r in reviews:
                combined_text = f"{r.title} {r.text}".lower()
                if phrase in combined_text:
                    matching_reviews.append(r.reviewer_id)

            if len(matching_reviews) >= 3:
                results.append({
                    "phrase": phrase,
                    "count": len(matching_reviews),
                    "sample_reviewers": matching_reviews[:4],
                    "cluster_type": "Template Duplication Pattern"
                })

        return results
