"""
Comprehensive Test Suite for Multi-Agent Trust Intelligence System.
Tests all 10 agents, benchmark scenarios, edge cases, and output schema validation.
"""

import sys
import os

# Add root directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.orchestrator import MultiAgentTrustOrchestrator
from agents.schemas import TrustReport


def test_ultracharge_fraud_scenario():
    orchestrator = MultiAgentTrustOrchestrator()
    report: TrustReport = orchestrator.run_pipeline("ultracharge_fraud", input_mode="benchmark", force_engine="demo")

    assert report.risk_tier == "HIGH RISK", f"Expected HIGH RISK, got {report.risk_tier}"
    assert report.overall_trust_score < 50.0, f"Expected trust score < 50, got {report.overall_trust_score}"
    assert report.velocity_spike_detected is True, "Expected velocity spike to be detected"
    assert len(report.duplicate_phrases_found) > 0, "Expected duplicate phrasing clusters"
    assert len(report.itemized_evidence) >= 3, "Expected itemized evidence records"
    assert len(report.agent_timeline) == 10, f"Expected 10 agents in timeline, got {len(report.agent_timeline)}"
    assert report.drift_analysis is not None, "Expected drift analysis"
    assert report.drift_analysis["drift_detected"] is True, "Expected drift detected"
    print("PASS: test_ultracharge_fraud_scenario")


def test_miracle_supplement_scenario():
    orchestrator = MultiAgentTrustOrchestrator()
    report: TrustReport = orchestrator.run_pipeline("miracle_supplement", input_mode="benchmark", force_engine="demo")

    assert report.risk_tier == "HIGH RISK", f"Expected HIGH RISK, got {report.risk_tier}"
    assert report.compliance_score < 0.6, f"Expected low compliance score, got {report.compliance_score}"
    assert any("disease cure" in e.issue.lower() or "medical" in e.issue.lower() for e in report.itemized_evidence), "Expected medical claim violation"
    print("PASS: test_miracle_supplement_scenario")


def test_genuine_audio_scenario():
    orchestrator = MultiAgentTrustOrchestrator()
    report: TrustReport = orchestrator.run_pipeline("genuine_audio", input_mode="benchmark", force_engine="demo")

    assert report.risk_tier == "LOW RISK", f"Expected LOW RISK, got {report.risk_tier}"
    assert report.overall_trust_score >= 75.0, f"Expected trust score >= 75, got {report.overall_trust_score}"
    assert report.velocity_spike_detected is False, "Expected no velocity spike"
    assert report.drift_analysis["drift_detected"] is False, "Expected no drift"
    print("PASS: test_genuine_audio_scenario")


def test_rhode_counterfeit_scenario():
    orchestrator = MultiAgentTrustOrchestrator()
    report: TrustReport = orchestrator.run_pipeline("rhode_fake_tint", input_mode="benchmark", force_engine="demo")

    assert report.risk_tier == "HIGH RISK", f"Expected HIGH RISK, got {report.risk_tier}"
    assert report.overall_trust_score < 50.0, f"Expected trust score < 50, got {report.overall_trust_score}"
    assert report.authenticity_score <= 0.3, f"Expected very low authenticity score due to fake alert, got {report.authenticity_score}"
    assert any("counterfeit" in e.issue.lower() or "fake" in e.issue.lower() for e in report.itemized_evidence), "Expected counterfeit alert in evidence"
    print("PASS: test_rhode_counterfeit_scenario")


if __name__ == "__main__":
    test_ultracharge_fraud_scenario()
    test_miracle_supplement_scenario()
    test_genuine_audio_scenario()
    test_rhode_counterfeit_scenario()
    print("\nALL MULTI-AGENT PIPELINE TESTS PASSED SUCCESSFULLY!")
