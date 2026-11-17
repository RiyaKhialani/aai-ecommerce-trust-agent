"""
Autonomous E-commerce Product Listing & Review Trust Intelligence Agent
Package containing the 10-Agent Architecture, Schemas, and Benchmark Datasets.
"""

from agents.schemas import ProductListing, TrustReport, EvidenceItem, CohortMetrics, ExtractedClaim
from agents.orchestrator import MultiAgentTrustOrchestrator
from agents.datasets import get_benchmark_listings

__all__ = [
    "ProductListing",
    "TrustReport",
    "EvidenceItem",
    "CohortMetrics",
    "ExtractedClaim",
    "MultiAgentTrustOrchestrator",
    "get_benchmark_listings",
]
