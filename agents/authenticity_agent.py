"""
Agent 5: Review Authenticity Detection Agent
Analyzes customer reviews for opinion spam, repeated n-gram phrasing, unverified purchase
ratios, direct counterfeit complaints, and generates forensic per-review ranking of the
Top 5 Most Fake/Suspicious reviews and Top Authentic reviews with detailed AI reasoning.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from agents.llm_client import LLMError, TrustAgentLLMClient
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

    def _rank_reviews_forensically(
        self,
        reviews: List[ReviewItem],
        repeated_phrases: List[Dict[str, Any]],
        spike_info: Optional[Dict[str, Any]] = None,
        llm_client: Optional[TrustAgentLLMClient] = None,
        product_title: str = "",
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Ranks reviews from most fake to most authentic with itemized forensic reasoning."""
        if not reviews:
            return [], []

        # 1. Deterministic heuristic baseline scoring per review
        review_analyses: List[Dict[str, Any]] = []
        dup_set = {dp["phrase"] for dp in repeated_phrases}
        generic_buzzwords = [
            "best ever", "miracle", "must buy", "life changing", "value of money",
            "awesome product", "good product", "nice product", "superb product",
            "very very worst", "waste of money", "100% recommend"
        ]

        for r in reviews:
            h_score = 0.10
            h_reasons = []
            lower_text = f"{r.title} {r.text}".lower()

            if not r.verified_purchase:
                h_score += 0.30
                h_reasons.append("Unverified buyer account (no confirmed platform order)")

            matched_dups = [p for p in dup_set if p in lower_text]
            if matched_dups:
                h_score += 0.35
                h_reasons.append(f"Contains syndicated review-farm phrasing: '{matched_dups[0]}'")

            words = re.findall(r"\w+", r.text)
            matched_buzz = [b for b in generic_buzzwords if b in lower_text]
            if matched_buzz and len(words) < 22:
                h_score += 0.20
                h_reasons.append(f"Generic hyperbolic phrasing ('{matched_buzz[0]}') with minimal functional detail ({len(words)} words)")

            if any(term in lower_text for term in ["fake", "scam", "counterfeit", "duplicate", "cheap copy", "not original", "blast", "explosive"]):
                h_score += 0.25
                h_reasons.append("Contains explicit buyer fraud/defect warnings or extreme alarmist vocabulary")

            if r.rating == 5.0 and not r.verified_purchase:
                h_score += 0.15
                h_reasons.append("Unverified 5-star rating typical of promotional review seeding")

            if spike_info and spike_info.get("spike_detected"):
                sw = str(spike_info.get("time_window") or "")
                if sw and sw in r.timestamp:
                    h_score += 0.15
                    h_reasons.append(f"Posted during identified velocity burst window ({sw})")

            h_score = min(0.95, max(0.05, round(h_score, 2)))
            review_analyses.append(
                {
                    "review_id": r.review_id,
                    "reviewer_id": r.reviewer_id,
                    "rating": r.rating,
                    "title": r.title,
                    "text": r.text,
                    "timestamp": r.timestamp,
                    "verified_purchase": r.verified_purchase,
                    "helpful_votes": r.helpful_votes,
                    "heuristic_score": h_score,
                    "heuristic_reasons": h_reasons,
                    "fake_score": h_score,
                    "reasoning": "; ".join(h_reasons) or "Authentic verified purchase with specific usage feedback.",
                    "verdict": "Likely Authentic",
                }
            )

        # 2. Live LLM per-review forensic reasoning
        if llm_client is not None:
            sample_for_llm = "\n".join(
                f"Review #{idx} [ID: {ra['review_id']}]:\n"
                f"Reviewer: {ra['reviewer_id']} | Rating: {ra['rating']}★ | Date: {ra['timestamp']} | Verified: {ra['verified_purchase']}\n"
                f"Title: {ra['title']}\n"
                f"Body: {ra['text'][:280]}\n"
                for idx, ra in enumerate(review_analyses[:15], 1)
            )

            prompt = f"""
You are Agent 5 (Review Authenticity & Forensic Analysis Agent) in an E-Commerce Trust & Safety pipeline.
Analyze each customer review below and evaluate its authenticity vs opinion-spam/incentivized manipulation.
For EVERY review (by review_id), provide:
1. "fake_score": float from 0.0 (100% authentic genuine buyer) to 1.0 (100% fake, bot, templated, or manipulated).
2. "verdict": "High Suspicion (Likely Fake)", "Moderate Suspicion", or "Likely Authentic".
3. "reasoning": 1-2 sentence detailed forensic rationale explaining why this review seems fake or authentic (mention specific signals: generic superlatives, lack of detail, verified purchase badge, extreme emotional tone, specific technical usage).

Product: {product_title}

Reviews to evaluate:
{sample_for_llm}

Return strict JSON:
{{
  "ranked_reviews": [
    {{
      "review_id": "rev-1",
      "fake_score": 0.85,
      "verdict": "High Suspicion (Likely Fake)",
      "reasoning": "Unverified buyer with generic hyperbolic praise and no mention of specific features."
    }}
  ]
}}
"""
            try:
                parsed, _, _ = llm_client.generate_json(prompt)
                raw_ranked = parsed if isinstance(parsed, list) else (parsed.get("ranked_reviews") if isinstance(parsed, dict) else [])
                llm_reviews_map = {
                    str(item.get("review_id")): item
                    for item in (raw_ranked or [])
                    if isinstance(item, dict) and item.get("review_id")
                }

                for ra in review_analyses:
                    rid = str(ra["review_id"])
                    if rid in llm_reviews_map:
                        llm_item = llm_reviews_map[rid]
                        try:
                            l_score = float(llm_item.get("fake_score", ra["heuristic_score"]))
                            l_score = min(0.98, max(0.02, l_score))
                        except (ValueError, TypeError):
                            l_score = ra["heuristic_score"]

                        # Blend 35% heuristic + 65% LLM forensic evaluation
                        ra["fake_score"] = round(0.35 * ra["heuristic_score"] + 0.65 * l_score, 2)
                        ra["reasoning"] = str(llm_item.get("reasoning") or ra["reasoning"]).strip()
                        ra["verdict"] = str(llm_item.get("verdict") or "Evaluated").strip()
            except Exception:
                pass

        # 3. Final verdict assignment and ranking
        for ra in review_analyses:
            fs = ra["fake_score"]
            if fs >= 0.60:
                ra["verdict"] = "High Suspicion (Likely Fake)"
                ra["risk_badge"] = "HIGH SUSPICION"
            elif fs >= 0.38:
                ra["verdict"] = "Moderate Suspicion"
                ra["risk_badge"] = "MODERATE SUSPICION"
            else:
                ra["verdict"] = "Likely Authentic"
                ra["risk_badge"] = "AUTHENTIC"
            ra["fake_probability_pct"] = int(fs * 100)

        # Sort descending by fake_score for top fake
        ranked_fake = sorted(review_analyses, key=lambda x: x["fake_score"], reverse=True)
        for idx, item in enumerate(ranked_fake, start=1):
            item["rank"] = idx

        top_5_fake = ranked_fake[:5]

        # Sort ascending for most authentic
        ranked_authentic = sorted(review_analyses, key=lambda x: x["fake_score"])
        top_authentic = [r for r in ranked_authentic if r["fake_score"] < 0.50][:5]

        return top_5_fake, top_authentic

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
                "top_fake_reviews": [],
                "top_authentic_reviews": [],
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

        # Perform forensic per-review ranking and explanation
        top_fake_reviews, top_authentic_reviews = self._rank_reviews_forensically(
            reviews=reviews,
            repeated_phrases=repeated_phrases,
            spike_info=spike_info,
            llm_client=llm_client,
            product_title=listing.title,
        )

        meta: Dict[str, Any] = {
            "review_count": len(reviews),
            "avg_rating": round(avg_rating, 2),
            "unverified_ratio": round(unverified_ratio, 2),
            "counterfeit_mentions": len(counterfeit_reports),
            "rationale": "",
            "top_fake_reviews": top_fake_reviews,
            "top_authentic_reviews": top_authentic_reviews,
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
                if not isinstance(parsed, dict):
                    parsed = {}
                if "authenticity_score" in parsed:
                    llm_score = max(0.05, min(1.0, float(parsed["authenticity_score"])))
                    score = round(min(score, llm_score), 2)
                if parsed.get("counterfeit_alert_detected"):
                    score = min(score, 0.25)
                meta["llm_model"] = model_used
                meta["llm_latency_ms"] = lat_ms
                meta["rationale"] = str(parsed.get("rationale") or "")
            except Exception as exc:
                meta["llm_error"] = str(exc)
                meta["rationale"] = "Assessed via deterministic n-gram analysis, verified purchase ratios, and buyer counterfeit keyword scans."

        return score, repeated_phrases, meta
