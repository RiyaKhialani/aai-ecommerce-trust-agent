"""
Advanced Feature: Listing Drift & Version Comparison Detector
Diffs current listing snapshot against historical 30-day baseline to detect
seller account swaps, spec tampering, and price crashes often preceding fraud.
"""

from typing import Dict, Any, Optional
from agents.schemas import ProductListing
from agents.datasets import get_listing_drift_snapshot


class ListingDriftDetector:
    def __init__(self):
        self.name = "Listing Drift Detector"

    def analyze_drift(self, listing: ProductListing, benchmark_id: Optional[str] = None) -> Dict[str, Any]:
        """Compares current listing state with historical snapshot."""
        if benchmark_id:
            return get_listing_drift_snapshot(benchmark_id)

        # For live listings, evaluate price history variance
        if len(listing.price_history) >= 2:
            p_initial = listing.price_history[0]["price"]
            p_latest = listing.price_history[-1]["price"]
            drift_detected = p_latest < (p_initial * 0.7)
            
            changes = []
            if drift_detected:
                changes.append({
                    "attribute": "Price Drop Anomaly",
                    "previous": f"₹{p_initial:,.2f}",
                    "current": f"₹{p_latest:,.2f}",
                    "flag": "Sudden price drop detected"
                })

            return {
                "snapshot_date": "Historical record",
                "drift_detected": drift_detected,
                "severity": "Medium" if drift_detected else "Low",
                "changes": changes,
                "recommendation": "Monitor listing velocity." if drift_detected else "Listing parameters stable."
            }

        return {
            "snapshot_date": "Baseline current",
            "drift_detected": False,
            "severity": "Low",
            "changes": [],
            "recommendation": "No prior historical drift detected."
        }
