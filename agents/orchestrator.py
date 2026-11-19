"""
Agent 10: Multi-Agent Orchestrator
Coordinates all 10 agents end-to-end with real per-agent timing, Two-Tier Safety Guardrails,
live LLM reasoning (Google Gemini or Groq), and persistent SQLite audit storage.
Zero fake latency floors, zero hardcoded datasets, and zero offline mock fallbacks.
"""

from __future__ import annotations

import time
from typing import Optional

from agents.authenticity_agent import ReviewAuthenticityAgent
from agents.claim_agent import ClaimExtractionAgent
from agents.compliance_agent import ListingComplianceClassifier
from agents.guardrails import TrustGuardrailsEngine
from agents.image_agent import CounterfeitImageSignalAgent
from agents.listing_agent import ListingIngestionAgent
from agents.llm_client import TrustAgentLLMClient, audit_logger
from agents.report_agent import PlainLanguageReportAgent
from agents.review_agent import ReviewSegmentationAgent
from agents.risk_agent import RiskScoringAggregationAgent
from agents.schemas import AgentExecutionStatus, ProductListing, TrustReport
from agents.seller_agent import SellerBehaviorAgent
from agents.storage import TrustStorage


class MultiAgentTrustOrchestrator:
    def __init__(self, storage: Optional[TrustStorage] = None) -> None:
        self.agent_id = 10
        self.name = "Multi-Agent Orchestrator"

        self.guardrails = TrustGuardrailsEngine()
        self.storage = storage or TrustStorage()
        self.listing_agent = ListingIngestionAgent()
        self.review_agent = ReviewSegmentationAgent()
        self.compliance_agent = ListingComplianceClassifier()
        self.claim_agent = ClaimExtractionAgent()
        self.authenticity_agent = ReviewAuthenticityAgent()
        self.seller_agent = SellerBehaviorAgent()
        self.image_agent = CounterfeitImageSignalAgent()
        self.risk_agent = RiskScoringAggregationAgent()
        self.report_agent = PlainLanguageReportAgent()

    def run_pipeline(
        self,
        target: str,
        llm_client: TrustAgentLLMClient,
        input_mode: str = "live_url",  # "live_url" or "pasted_text"
    ) -> TrustReport:
        """Executes the full 10-agent Trust Triage pipeline with real LLM calls and real latencies."""
        audit_logger.clear()
        timeline: list[AgentExecutionStatus] = []
        pipeline_start = time.perf_counter()

        # Validate input via Input Safety Guardrails
        in_guard = self.guardrails.validate_input(target)
        if not in_guard.is_safe:
            self.storage.log_guardrail_event(
                event_type="INPUT_BLOCKED",
                severity="Critical",
                raw_input=target[:300],
                sanitized_output=in_guard.sanitized_text[:300],
                action_taken=in_guard.action_taken,
                details="; ".join(in_guard.violations_detected),
            )
            raise ValueError(f"Input Guardrail blocked request: {'; '.join(in_guard.violations_detected)}")

        engine_label = f"{llm_client.provider.title()} ({llm_client.model})"

        # --- AGENT 1: Listing Ingestion ---
        t0 = time.perf_counter()
        is_url = (
            str(input_mode).strip().lower() in ("live_url", "live url", "url")
            or target.strip().startswith(("http://", "https://"))
        )
        if is_url:
            listing: ProductListing = self.listing_agent.execute_from_url(target, llm_client=llm_client)
            source_label = "Live Marketplace URL"
        else:
            listing = self.listing_agent.execute_from_text(in_guard.sanitized_text, llm_client=llm_client)
            source_label = "Direct Listing Paste"
        elapsed_1 = round((time.perf_counter() - t0) * 1000, 1)

        audit_logger.log_event(
            1,
            "Listing Ingestion Agent",
            "INGESTION_COMPLETED",
            {
                "source": source_label,
                "listing_id": listing.listing_id,
                "title": listing.title,
                "category": listing.category,
                "price": listing.price,
                "seller": listing.seller_name,
                "reviews_extracted": len(listing.reviews),
                "latency_ms": elapsed_1,
            },
        )
        timeline.append(
            AgentExecutionStatus(
                agent_id=1,
                name="Listing Ingestion Agent",
                status="success",
                execution_time_ms=elapsed_1,
                summary=f"Extracted '{listing.title[:50]}' ({listing.category}) with {len(listing.reviews)} real reviews.",
            )
        )

        # --- AGENT 2: Review Ingestion & Segmentation ---
        t0 = time.perf_counter()
        cohorts, spike_info = self.review_agent.execute(listing)
        elapsed_2 = round((time.perf_counter() - t0) * 1000, 1)

        audit_logger.log_event(
            2,
            "Review Ingestion & Segmentation Agent",
            "COHORT_SEGMENTATION",
            {
                "cohort_count": len(cohorts),
                "spike_detected": spike_info.get("spike_detected", False),
                "spike_details": spike_info,
                "latency_ms": elapsed_2,
            },
        )
        timeline.append(
            AgentExecutionStatus(
                agent_id=2,
                name="Review Ingestion & Segmentation Agent",
                status="success",
                execution_time_ms=elapsed_2,
                summary=f"Segmented {len(listing.reviews)} reviews into {len(cohorts)} time cohort(s). Velocity spike: {spike_info.get('spike_detected', False)}.",
            )
        )

        # --- AGENT 3: Listing Compliance Classifier ---
        t0 = time.perf_counter()
        compliance_score, compliance_violations, comp_meta = self.compliance_agent.execute(listing, llm_client=llm_client)
        elapsed_3 = round((time.perf_counter() - t0) * 1000, 1)

        audit_logger.log_event(
            3,
            "Listing Compliance Classifier",
            "COMPLIANCE_AUDIT",
            {
                "compliance_score": compliance_score,
                "violations": compliance_violations,
                "llm_meta": comp_meta,
                "latency_ms": elapsed_3,
            },
        )
        timeline.append(
            AgentExecutionStatus(
                agent_id=3,
                name="Listing Compliance Classifier",
                status="success",
                execution_time_ms=elapsed_3,
                summary=f"Compliance Score: {compliance_score:.2f} | Flagged {len(compliance_violations)} policy violation(s).",
            )
        )

        # --- AGENT 4: Claim Extraction Agent ---
        t0 = time.perf_counter()
        extracted_claims = self.claim_agent.execute(listing, llm_client=llm_client)
        elapsed_4 = round((time.perf_counter() - t0) * 1000, 1)

        audit_logger.log_event(
            4,
            "Claim Extraction Agent",
            "CLAIMS_EXTRACTED",
            {
                "total_claims": len(extracted_claims),
                "claims": [c.model_dump() for c in extracted_claims],
                "latency_ms": elapsed_4,
            },
        )
        timeline.append(
            AgentExecutionStatus(
                agent_id=4,
                name="Claim Extraction Agent",
                status="success",
                execution_time_ms=elapsed_4,
                summary=f"Extracted {len(extracted_claims)} factual claim(s) for verification and redlining.",
            )
        )

        # --- AGENT 5: Review Authenticity Detection ---
        t0 = time.perf_counter()
        authenticity_score, duplicate_phrases, auth_meta = self.authenticity_agent.execute(
            listing, spike_info=spike_info, llm_client=llm_client
        )
        elapsed_5 = round((time.perf_counter() - t0) * 1000, 1)

        audit_logger.log_event(
            5,
            "Review Authenticity Detection Agent",
            "AUTHENTICITY_AUDIT",
            {
                "authenticity_score": authenticity_score,
                "duplicate_phrases": duplicate_phrases,
                "meta": auth_meta,
                "latency_ms": elapsed_5,
            },
        )
        timeline.append(
            AgentExecutionStatus(
                agent_id=5,
                name="Review Authenticity Detection Agent",
                status="success",
                execution_time_ms=elapsed_5,
                summary=f"Authenticity Score: {authenticity_score:.2f} | Found {len(duplicate_phrases)} repeated 4-gram cluster(s).",
            )
        )

        # --- AGENT 6: Seller Behavior Pattern Agent ---
        t0 = time.perf_counter()
        seller_score, seller_flags, seller_meta = self.seller_agent.execute(listing)
        elapsed_6 = round((time.perf_counter() - t0) * 1000, 1)

        audit_logger.log_event(
            6,
            "Seller Behavior Pattern Agent",
            "MERCHANT_PROFILING",
            {
                "seller_score": seller_score,
                "flags": seller_flags,
                "meta": seller_meta,
                "latency_ms": elapsed_6,
            },
        )
        timeline.append(
            AgentExecutionStatus(
                agent_id=6,
                name="Seller Behavior Pattern Agent",
                status="success",
                execution_time_ms=elapsed_6,
                summary=f"Seller Reliability Score: {seller_score:.2f} | Flagged {len(seller_flags)} merchant signal(s).",
            )
        )

        # --- AGENT 7: Counterfeit & Image Signal Agent ---
        t0 = time.perf_counter()
        image_score, image_flags, image_meta = self.image_agent.execute(listing, llm_client=llm_client)
        elapsed_7 = round((time.perf_counter() - t0) * 1000, 1)

        audit_logger.log_event(
            7,
            "Counterfeit & Image Signal Agent",
            "IMAGE_SIGNAL_AUDIT",
            {
                "image_score": image_score,
                "flags": image_flags,
                "meta": image_meta,
                "latency_ms": elapsed_7,
            },
        )
        timeline.append(
            AgentExecutionStatus(
                agent_id=7,
                name="Counterfeit & Image Signal Agent",
                status="success",
                execution_time_ms=elapsed_7,
                summary=f"Image & Packaging Score: {image_score:.2f} | Flagged {len(image_flags)} signal(s).",
            )
        )

        # --- AGENT 8: Risk Scoring & Aggregation ---
        t0 = time.perf_counter()
        trust_score, risk_tier, evidence = self.risk_agent.execute(
            listing=listing,
            compliance_score=compliance_score,
            compliance_violations=compliance_violations,
            authenticity_score=authenticity_score,
            duplicate_phrases=duplicate_phrases,
            spike_info=spike_info,
            seller_score=seller_score,
            seller_flags=seller_flags,
            image_score=image_score,
            image_flags=image_flags,
            extracted_claims=extracted_claims,
        )
        elapsed_8 = round((time.perf_counter() - t0) * 1000, 1)

        audit_logger.log_event(
            8,
            "Risk Scoring & Aggregation Agent",
            "WEIGHTED_AGGREGATION",
            {
                "formula": "100 * (0.25*Compliance + 0.35*Authenticity + 0.25*Seller + 0.15*Image)",
                "overall_trust_score": trust_score,
                "risk_tier": risk_tier,
                "evidence_count": len(evidence),
                "latency_ms": elapsed_8,
            },
        )
        timeline.append(
            AgentExecutionStatus(
                agent_id=8,
                name="Risk Scoring & Aggregation Agent",
                status="success",
                execution_time_ms=elapsed_8,
                summary=f"Computed Trust Score: {trust_score}/100 ({risk_tier}) with {len(evidence)} itemized finding(s).",
            )
        )

        # --- AGENT 9: Plain-Language Report Agent ---
        t0 = time.perf_counter()
        exec_summary, verdict, merchant_notice, redlines = self.report_agent.execute(
            listing=listing,
            trust_score=trust_score,
            risk_tier=risk_tier,
            evidence=evidence,
            extracted_claims=extracted_claims,
            llm_client=llm_client,
        )
        elapsed_9 = round((time.perf_counter() - t0) * 1000, 1)

        audit_logger.log_event(
            9,
            "Plain-Language Report Agent",
            "REPORT_SYNTHESIS",
            {
                "verdict": verdict,
                "redline_count": len(redlines),
                "latency_ms": elapsed_9,
            },
        )
        timeline.append(
            AgentExecutionStatus(
                agent_id=9,
                name="Plain-Language Report Agent",
                status="success",
                execution_time_ms=elapsed_9,
                summary=f"Synthesized executive triage summary, merchant notice, and {len(redlines)} claim redline(s).",
            )
        )

        # --- AGENT 10: Orchestrator Wrap-up ---
        total_elapsed = round((time.perf_counter() - pipeline_start) * 1000, 1)
        audit_logger.log_event(
            10,
            "Multi-Agent Orchestrator",
            "PIPELINE_COMPLETE",
            {
                "total_elapsed_ms": total_elapsed,
                "engine": engine_label,
                "trust_score": trust_score,
                "risk_tier": risk_tier,
            },
        )
        timeline.append(
            AgentExecutionStatus(
                agent_id=10,
                name="Multi-Agent Orchestrator",
                status="success",
                execution_time_ms=total_elapsed,
                summary=f"Completed 10-agent pipeline in {total_elapsed:.1f} ms via {engine_label}.",
            )
        )

        final_report = TrustReport(
            listing_id=listing.listing_id,
            product_name=listing.title,
            brand=listing.brand,
            category=listing.category,
            price=listing.price,
            currency=listing.currency,
            seller_name=listing.seller_name,
            seller_id=listing.seller_id,
            overall_trust_score=trust_score,
            risk_tier=risk_tier,
            compliance_score=compliance_score,
            authenticity_score=authenticity_score,
            seller_score=seller_score,
            image_integrity_score=image_score,
            engine_mode=engine_label,
            input_source=source_label,
            executive_summary=exec_summary,
            recommended_verdict=verdict,
            itemized_evidence=evidence,
            velocity_spike_detected=spike_info.get("spike_detected", False),
            velocity_spike_details=spike_info if spike_info.get("spike_detected") else None,
            cohort_analysis=cohorts,
            duplicate_phrases_found=duplicate_phrases,
            extracted_claims=extracted_claims,
            redline_suggestions=redlines,
            seller_flags=seller_flags,
            image_flags=image_flags,
            auto_suggested_reviewer_prompt=merchant_notice,
            reviews_sample=[r.model_dump() for r in listing.reviews],
            top_fake_reviews=auth_meta.get("top_fake_reviews", []),
            top_authentic_reviews=auth_meta.get("top_authentic_reviews", []),
            agent_timeline=timeline,
            verbose_audit_logs=audit_logger.get_logs(),
        )

        # Output Guardrails validation
        guard_out = self.guardrails.validate_output(final_report.model_dump())
        final_report.guardrail_status = guard_out.model_dump()

        # Persist to SQLite
        save_payload = final_report.model_dump()
        save_payload["reviews_count"] = len(listing.reviews)
        save_payload["cohorts_count"] = len(cohorts)
        self.storage.save_audit_report(save_payload)

        return final_report
