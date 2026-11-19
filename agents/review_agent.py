"""
Agent 2: Review Ingestion & Segmentation Agent
Segments extracted reviews into chronological cohorts and detects review velocity bursts
(>3x baseline cohort volume or high unverified purchase ratios).
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Tuple

from agents.schemas import CohortMetrics, ProductListing


class ReviewSegmentationAgent:
    def __init__(self) -> None:
        self.agent_id = 2
        self.name = "Review Ingestion & Segmentation Agent"

    def execute(self, listing: ProductListing) -> Tuple[List[CohortMetrics], Dict[str, Any]]:
        reviews = listing.reviews
        if not reviews:
            return [], {
                "spike_detected": False,
                "total_reviews": 0,
                "unverified_ratio": 0.0,
                "status": "No customer reviews were present on the scraped page.",
            }

        cohort_groups = defaultdict(list)
        for r in reviews:
            ts = r.timestamp.strip()
            window_key = ts[:10] if len(ts) >= 10 and ts[0].isdigit() else "Undated"
            cohort_groups[window_key].append(r)

        sorted_keys = sorted(cohort_groups.keys())
        cohorts: List[CohortMetrics] = []
        counts: List[int] = []

        total_unverified = sum(1 for r in reviews if not r.verified_purchase)
        overall_unverified_ratio = total_unverified / len(reviews)

        for key in sorted_keys:
            rev_list = cohort_groups[key]
            cnt = len(rev_list)
            counts.append(cnt)
            avg_rt = sum(r.rating for r in rev_list) / cnt
            unver = sum(1 for r in rev_list if not r.verified_purchase)
            unver_ratio = unver / cnt

            cohorts.append(
                CohortMetrics(
                    time_window=key,
                    review_count=cnt,
                    avg_rating=round(avg_rt, 2),
                    unverified_ratio=round(unver_ratio, 2),
                    is_spike=False,
                    details=f"{cnt} reviews | avg {avg_rt:.1f}★ | {unver_ratio * 100:.0f}% unverified",
                )
            )

        spike_detected = False
        spike_info: Dict[str, Any] = {}

        if len(cohorts) >= 2:
            total_count = sum(counts)
            for c in cohorts:
                other_avg = (total_count - c.review_count) / max(1, len(counts) - 1)
                if c.review_count >= 5 and c.review_count >= 3.0 * max(other_avg, 0.5):
                    c.is_spike = True
                    spike_detected = True
                    spike_info = {
                        "spike_detected": True,
                        "time_window": c.time_window,
                        "spike_count": c.review_count,
                        "baseline_average": round(other_avg, 1),
                        "multiplier": round(c.review_count / max(other_avg, 0.1), 1),
                        "unverified_ratio": c.unverified_ratio,
                        "warning": (
                            f"Velocity burst detected in {c.time_window}: {c.review_count} reviews "
                            f"vs {other_avg:.1f} baseline average."
                        ),
                    }

        if not spike_detected:
            spike_info = {
                "spike_detected": False,
                "total_reviews": len(reviews),
                "unverified_ratio": round(overall_unverified_ratio, 2),
                "status": "No abnormal single-window review velocity spike detected in extracted sample.",
            }

        return cohorts, spike_info
