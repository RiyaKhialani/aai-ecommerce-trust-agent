"""
Command-Line Interface for Autonomous E-commerce Trust Intelligence System.
Usage:
    python cli.py --target ultracharge_fraud
    python cli.py --target miracle_supplement
    python cli.py --target genuine_audio
    python cli.py --url https://www.amazon.in/...
"""

import argparse
import json
import sys
import io

# Ensure UTF-8 output on Windows terminal
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from agents.orchestrator import MultiAgentTrustOrchestrator
from agents.schemas import TrustReport


def main():
    parser = argparse.ArgumentParser(description="Autonomous E-commerce Product Trust Intelligence System (PS-11)")
    parser.add_argument("--target", type=str, default="ultracharge_fraud", help="Benchmark ID (ultracharge_fraud, miracle_supplement, genuine_audio)")
    parser.add_argument("--url", type=str, default=None, help="Live marketplace URL to inspect")
    parser.add_argument("--engine", type=str, default="demo", choices=["demo", "llm", "auto"], help="Execution engine mode")
    parser.add_argument("--json", action="store_true", help="Output raw JSON report")

    args = parser.parse_args()
    console = Console(legacy_windows=False)

    orchestrator = MultiAgentTrustOrchestrator()
    target_input = args.url if args.url else args.target
    input_mode = "live_url" if args.url else "benchmark"

    console.print(f"\n[bold cyan]⚡ Initializing Autonomous E-commerce Trust Intelligence System[/bold cyan]")
    console.print(f"[dim]Target: {target_input} | Mode: {input_mode} | Engine: {args.engine}[/dim]\n")

    report: TrustReport = orchestrator.run_pipeline(
        target=target_input,
        input_mode=input_mode,
        force_engine=args.engine
    )

    if args.json:
        print(json.dumps(report.model_dump(), indent=2))
        return

    # Visual Rich Output
    # 1. Header Banner
    tier_color = "red" if report.risk_tier == "HIGH RISK" else ("yellow" if report.risk_tier == "MEDIUM RISK" else "green")
    console.print(
        Panel(
            f"[bold {tier_color}]TRUST SCORE: {report.overall_trust_score}/100 — {report.risk_tier}[/bold {tier_color}]\n"
            f"[bold white]{report.product_name}[/bold white]\n"
            f"Seller: [cyan]{report.seller_name}[/cyan] ({report.seller_id}) | Category: [magenta]{report.category}[/magenta]\n"
            f"Engine: [yellow]{report.engine_mode}[/yellow] (Demo Mode: {report.is_demo_mode})",
            title="🛡️ E-COMMERCE PRODUCT TRUST INTELLIGENCE AUDIT",
            border_style=tier_color,
            box=box.ROUNDED
        )
    )

    # 2. Agent Execution Timeline Table
    timeline_table = Table(title="🤖 10-Agent Autonomous Execution Timeline", box=box.SIMPLE_HEAVY)
    timeline_table.add_column("Agent ID", style="cyan", justify="center")
    timeline_table.add_column("Agent Name", style="bold white")
    timeline_table.add_column("Time (ms)", style="green", justify="right")
    timeline_table.add_column("Summary Finding", style="dim white")

    for status in report.agent_timeline:
        timeline_table.add_row(
            str(status.agent_id),
            status.name,
            f"{status.execution_time_ms:.1f} ms",
            status.summary
        )
    console.print(timeline_table)

    # 3. Component Scores Breakdown
    scores_table = Table(title="📊 Modular Trust Component Metrics", box=box.SIMPLE)
    scores_table.add_column("Module", style="cyan")
    scores_table.add_column("Score", style="bold white", justify="center")
    scores_table.add_column("Status", justify="left")

    def format_score(val):
        color = "green" if val >= 0.75 else ("yellow" if val >= 0.50 else "red")
        return f"[{color}]{int(val * 100)}%[/{color}]"

    scores_table.add_row("Listing Policy Compliance", format_score(report.compliance_score), "Keyword & regulatory verification")
    scores_table.add_row("Review Authenticity", format_score(report.authenticity_score), "Duplication, sentiment & timing bursts")
    scores_table.add_row("Seller Reliability", format_score(report.seller_score), "Account age vs sales velocity ratio")
    scores_table.add_row("Image & Brand Integrity", format_score(report.image_integrity_score), "Stock photo reuse & badge markings")
    console.print(scores_table)

    # 4. Itemized Evidence Table
    evidence_table = Table(title="🔍 Itemized Evidence & Risk Flags", box=box.DOUBLE_EDGE)
    evidence_table.add_column("Risk", justify="center")
    evidence_table.add_column("Module", style="cyan")
    evidence_table.add_column("Item Detected", style="bold white")
    evidence_table.add_column("Explanation & Recommendation", style="dim white")

    for ev in report.itemized_evidence:
        ev_color = "red" if ev.risk_level in ["High", "Critical"] else ("yellow" if ev.risk_level == "Medium" else "green")
        evidence_table.add_row(
            f"[{ev_color}]{ev.risk_level.upper()}[/{ev_color}]",
            ev.module,
            ev.item_detected,
            f"{ev.explanation}\n[bold {ev_color}]Action:[/] {ev.recommendation}"
        )
    console.print(evidence_table)

    # 5. Redline View
    if report.redline_suggestions:
        redline_table = Table(title="📝 Claim Redline & Remediation Suggestions", box=box.ROUNDED)
        redline_table.add_column("Original Prohibited/Unverified Claim", style="red")
        redline_table.add_column("Compliant Redline Replacement", style="green")
        redline_table.add_column("Policy Rationale", style="dim white")
        for r in report.redline_suggestions:
            redline_table.add_row(r["original"], r["replacement"], r["reason"])
        console.print(redline_table)

    # 6. Auto-Suggested Reviewer Prompt
    if report.auto_suggested_reviewer_prompt:
        console.print(
            Panel(
                f"[italic white]{report.auto_suggested_reviewer_prompt}[/italic white]",
                title="✉️ Auto-Suggested Reviewer Action Notice",
                border_style="yellow",
                box=box.ROUNDED
            )
        )

    # 7. Final Verdict
    console.print(
        Panel(
            f"[bold {tier_color}]{report.recommended_verdict}[/bold {tier_color}]\n\n{report.executive_summary}",
            title="📋 EXECUTIVE ACTION VERDICT",
            border_style=tier_color,
            box=box.HEAVY
        )
    )


if __name__ == "__main__":
    main()
