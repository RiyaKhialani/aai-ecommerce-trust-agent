from __future__ import annotations
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class ReviewItem(BaseModel):
    review_id: str
    reviewer_id: str
    rating: float
    title: str
    text: str
    timestamp: str
    verified_purchase: bool = True
    helpful_votes: int = 0


class ProductListing(BaseModel):
    listing_id: str
    title: str
    description: str
    brand: str
    category: str
    price: float
    original_mrp: Optional[float] = None
    currency: str = "INR"
    seller_id: str
    seller_name: str
    seller_country: Optional[str] = None
    origin_country: Optional[str] = None
    seller_account_age_days: int
    seller_rating: float = 4.5
    price_history: List[Dict[str, Any]] = Field(default_factory=list)
    image_urls: List[str] = Field(default_factory=list)
    listing_date: str = ""
    stock_status: str = "In Stock"
    specs: Dict[str, str] = Field(default_factory=dict)
    url: Optional[str] = None
    reviews: List[ReviewItem] = Field(default_factory=list)


class CohortMetrics(BaseModel):
    time_window: str
    review_count: int
    avg_rating: float
    unverified_ratio: float
    is_spike: bool = False
    details: str = ""


class ExtractedClaim(BaseModel):
    claim_text: str
    claim_category: str  # e.g., "Certification", "Technical Spec", "Medical/Health", "Warranty"
    is_verified: bool = False
    verification_source: str = "Seller-stated"
    risk_level: str = "Low"  # "Low", "Medium", "High"
    policy_issue: Optional[str] = None
    suggested_redline: Optional[str] = None


class EvidenceItem(BaseModel):
    module: str
    item_detected: str
    issue: str
    risk_level: str  # "Low", "Medium", "High", "Critical"
    explanation: str
    recommendation: str


class AgentExecutionStatus(BaseModel):
    agent_id: int
    name: str
    status: str = "success"  # "success", "fallback", "error"
    execution_time_ms: float = 0.0
    summary: str = ""
    details: Dict[str, Any] = Field(default_factory=dict)


class TrustReport(BaseModel):
    product_name: str
    category: str
    seller_name: str
    seller_id: str
    overall_trust_score: float  # 0 to 100
    risk_tier: str  # "LOW RISK", "MEDIUM RISK", "HIGH RISK"
    compliance_score: float  # 0.0 to 1.0
    authenticity_score: float  # 0.0 to 1.0
    seller_score: float  # 0.0 to 1.0
    image_integrity_score: float  # 0.0 to 1.0
    engine_mode: str  # "Live AI LLM" or "Deterministic Heuristic Demo"
    is_demo_mode: bool = False
    input_source: str = "Benchmark Dataset"  # "Live URL" or "Benchmark Dataset"
    executive_summary: str
    recommended_verdict: str
    itemized_evidence: List[EvidenceItem] = Field(default_factory=list)
    velocity_spike_detected: bool = False
    velocity_spike_details: Optional[Dict[str, Any]] = None
    cohort_analysis: List[CohortMetrics] = Field(default_factory=list)
    duplicate_phrases_found: List[Dict[str, Any]] = Field(default_factory=list)
    extracted_claims: List[ExtractedClaim] = Field(default_factory=list)
    redline_suggestions: List[Dict[str, str]] = Field(default_factory=list)
    seller_flags: List[str] = Field(default_factory=list)
    image_flags: List[str] = Field(default_factory=list)
    auto_suggested_reviewer_prompt: str = ""
    agent_timeline: List[AgentExecutionStatus] = Field(default_factory=list)
    drift_analysis: Optional[Dict[str, Any]] = None
    verbose_audit_logs: List[Dict[str, Any]] = Field(default_factory=list)
    guardrail_status: Optional[Dict[str, Any]] = None
