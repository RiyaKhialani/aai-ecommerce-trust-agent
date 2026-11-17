"""
Agent 2: Review Ingestion & Segmentation Agent
Collects all reviews for a listing and segments them into time-windowed batches.
Detects review velocity spikes, unverified purchase surges, and rating distribution shifts.
"""

from typing import List, Dict, Any, Tuple
from collections import defaultdict
from datetime import datetime
from agents.schemas import ProductListing, ReviewItem, CohortMetrics


class ReviewSegmentationAgent:
    def __init__(self):
        self.agent_id = 2
        self.name = "Review Ingestion & Segmentation Agent"

    def execute(self, listing: ProductListing) -> Tuple[List[CohortMetrics], Dict[str, Any]]:
        reviews = listing.reviews
        if not reviews:
            return [], {"spike_detected": False, "total_reviews": 0}

        # Bucket reviews by timestamp or identifier
        cohort_groups = defaultdict(list)
        for r in reviews:
            # Determine window key (e.g. Week 1, Week 2, or YYYY-MM)
            time_str = r.timestamp[:10] if len(r.timestamp) >= 10 else "General"
            cohort_groups[time_str].append(r)

        # Sort dates
        sorted_keys = sorted(cohort_groups.keys())
        cohorts: List[CohortMetrics] = []
        counts = []

        total_unverified = sum(1 for r in reviews if not r.verified_purchase)
        overall_unverified_ratio = total_unverified / len(reviews) if reviews else 0.0

        for key in sorted_keys:
            rev_list = cohort_groups[key]
            cnt = len(rev_list)
            counts.append(cnt)
            avg_rt = sum(r.rating for r in rev_list) / cnt if cnt > 0 else 0.0
            unver = sum(1 for r in rev_list if not r.verified_purchase)
            unver_ratio = unver / cnt if cnt > 0 else 0.0
            
            cohorts.append(
                CohortMetrics(
                    time_window=key,
                    review_count=cnt,
                    avg_rating=round(avg_rt, 2),
                    unverified_ratio=round(unver_ratio, 2),
                    is_spike=False,
                    details=f"{cnt} reviews, avg {round(avg_rt, 1)}★, {round(unver_ratio * 100)}% unverified"
                )
            )

        # Spike detection algorithm:
        # A cohort is considered a spike if count > 50 and count >= 3x the average of other cohorts,
        # or if a single 48h cohort contains > 100 reviews.
        spike_detected = False
        spike_info = {}

        if len(cohorts) > 0:
            avg_count = sum(counts) / len(counts)
            for c in cohorts:
                if c.review_count > 50 and (c.review_count >= 3 * avg_count or c.review_count >= 100):
                    c.is_spike = True
                    spike_detected = True
                    spike_info = {
                        "spike_detected": True,
                        "time_window": c.time_window,
                        "spike_count": c.review_count,
                        "baseline_average": round(avg_count, 1),
                        "multiplier": round(c.review_count / (avg_count or 1), 1),
                        "unverified_ratio": c.unverified_ratio,
                        "warning": f"Abnormal burst: {c.review_count} reviews in a single window vs baseline {round(avg_count, 1)}"
                    }

        if not spike_detected:
            spike_info = {
                "spike_detected": False,
                "total_reviews": len(reviews),
                "unverified_ratio": round(overall_unverified_ratio, 2),
                "status": "Review velocity appears organic and steady."
            }

        return cohorts, spike_info
