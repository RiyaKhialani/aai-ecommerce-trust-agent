"""
Agent 5: Review Authenticity Detection Agent
Analyzes extracted customer reviews for opinion spam, repeated n-gram phrasing,
unverified purchase ratios, direct counterfeit complaints, and live LLM authenticity reasoning.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from agents.llm_client import TrustAgentLLMClient
from agents.schemas import ProductListing, ReviewItem


class ReviewAuthenticityAgent:
    def __init__(self) -> None:
        self.agent_id = 5
        self.name = "Review Authenticity Detection Agent"

    @staticmethod
    def _find_duplicate_phrases(reviews: List[ReviewItem], min_count: int = 2) -> List[Dict[str, Any]]:
        ngram_counts: Counter = Counter()
        for r in reviews:
            tokens = re.findall(r"[a-z]{3,}", f"{r.title} {r.text}".lower())
            seen_in_review = set()
            for i in range(len(tokens) - 3):
                phrase = " ".join(tokens[i : i + 4])
                if phrase not in seen_in_review:
                    seen_in_review.add(phrase)
                    ngram_counts[phrase] += 1

        return [
            {"phrase": phrase, "count": count}
            for phrase, count in ngram_counts.most_common(8)
            if count >= min_count
        ]

    def execute(
        self,
        listing: ProductListing,
        spike_info: Optional[Dict[str, Any]] = None,
        llm_client: Optional[TrustAgentLLMClient] = None,
    ) -> Tuple[float, List[Dict[str, Any]], Dict[str, Any]]:
        reviews = listing.reviews
        if not reviews:
            return 0.65, [], {
                "summary": "No customer reviews extracted from listing; assigned neutral baseline (0.65).",
                "counterfeit_mentions": 0,
            }

        counterfeit_reports = []
        for r in reviews:
            full_rev = f"{r.title} {r.text}".lower()
            if any(
                term in full_rev
                for term in ["fake product", "scam", "counterfeit", "duplicate", "cheap copy", "not original"]
            ):
                counterfeit_reports.append(
                    {
                        "reviewer_id": r.reviewer_id,
                        "rating": r.rating,
                        "title": r.title,
                        "text": r.text,
                    }
                )

        repeated_phrases = self._find_duplicate_phrases(reviews)
        avg_rating = sum(r.rating for r in reviews) / len(reviews)
        unverified_ratio = sum(1 for r in reviews if not r.verified_purchase) / len(reviews)

        score = 1.0
        if counterfeit_reports:
            score -= 0.65
        if avg_rating <= 2.2:
            score -= 0.25
        if repeated_phrases:
            score -= min(0.30, 0.08 * len(repeated_phrases))
        if unverified_ratio > 0.5:
            score -= 0.20
        if spike_info and spike_info.get("spike_detected"):
            score -= 0.25
        score = max(0.05, min(1.0, round(score, 2)))

        meta: Dict[str, Any] = {
            "review_count": len(reviews),
            "avg_rating": round(avg_rating, 2),
            "unverified_ratio": round(unverified_ratio, 2),
            "counterfeit_mentions": len(counterfeit_reports),
            "rationale": "",
        }

        if llm_client is not None:
            sample_text = "\n".join(
                f"- [{r.rating}★ | {'Verified' if r.verified_purchase else 'Unverified'}] {r.title}: {r.text[:240]}"
                for r in reviews[:12]
            )
            prompt = f"""
You are Agent 5 (Review Authenticity Detection Agent) in an E-Commerce Trust & Safety system.
Analyze these customer reviews for bot/templated phrasing, incentivized manipulation, or direct buyer counterfeit warnings.

Product: {listing.title}
Reviews:
{sample_text}

Return strict JSON:
{{
  "authenticity_score": 0.0,
  "counterfeit_alert_detected": false,
  "rationale": "Concise 2-sentence explanation of review authenticity"
}}
"""
            try:
                parsed, model_used, lat_ms = llm_client.generate_json(prompt)
                if "authenticity_score" in parsed:
                    llm_score = max(0.05, min(1.0, float(parsed["authenticity_score"])))
                    score = round(min(score, llm_score), 2)
                if parsed.get("counterfeit_alert_detected"):
                    score = min(score, 0.25)
                meta["llm_model"] = model_used
                meta["llm_latency_ms"] = lat_ms
                meta["rationale"] = str(parsed.get("rationale") or "")
            except LLMError as exc:
                meta["llm_error"] = str(exc)
                meta["rationale"] = "Assessed via deterministic n-gram analysis, verified purchase ratios, and buyer counterfeit keyword scans."

        return score, repeated_phrases, meta
