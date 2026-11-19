"""
Command-Line Interface for Autonomous E-commerce Product Listing & Review Trust Agent (PS-11).
Usage:
    python cli.py --url "https://www.amazon.in/dp/..." --provider gemini
"""

from __future__ import annotations

import argparse
import json
import sys

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agents.llm_client import TrustAgentLLMClient
from agents.orchestrator import MultiAgentTrustOrchestrator


def main() -> None:
    parser = argparse.ArgumentParser(description="Autonomous E-Commerce Trust Intelligence CLI (PS-11)")
    parser.add_argument("--url", type=str, required=True, help="Live marketplace product URL to audit")
    parser.add_argument("--provider", type=str, default="gemini", choices=["gemini", "groq"], help="Live LLM provider")
    parser.add_argument("--model", type=str, default=None, help="Optional model override")
    parser.add_argument("--json", action="store_true", help="Output raw JSON report")
    args = parser.parse_args()

    console = Console(legacy_windows=False)
    llm_client = TrustAgentLLMClient(provider=args.provider, model=args.model)
    orchestrator = MultiAgentTrustOrchestrator()

    console.print(f"\n[bold cyan]Running 10-Agent Trust Audit[/bold cyan] ({args.provider}: {llm_client.model})")
    report = orchestrator.run_pipeline(target=args.url, llm_client=llm_client, input_mode="live_url")

    if args.json:
        print(json.dumps(report.model_dump(), indent=2))
        return

    tier_color = "red" if report.risk_tier == "HIGH RISK" else ("yellow" if report.risk_tier == "MEDIUM RISK" else "green")
    console.print(
        Panel(
            f"[bold {tier_color}]TRUST SCORE: {report.overall_trust_score}/100 — {report.risk_tier}[/bold {tier_color}]\n"
            f"[bold]{report.product_name}[/bold]\n"
            f"Seller: {report.seller_name} ({report.seller_id}) | Engine: {report.engine_mode}",
            title="E-Commerce Product Trust Audit",
            border_style=tier_color,
            box=box.ROUNDED,
        )
    )

    t_tbl = Table(title="10-Agent Execution Timeline", box=box.SIMPLE_HEAVY)
    t_tbl.add_column("Agent", style="cyan")
    t_tbl.add_column("Module", style="bold")
    t_tbl.add_column("Latency", justify="right", style="green")
    t_tbl.add_column("Finding")
    for a in report.agent_timeline:
        t_tbl.add_row(f"Agent {a.agent_id}", a.name, f"{a.execution_time_ms:.1f} ms", a.summary)
    console.print(t_tbl)

    console.print(Panel(report.executive_summary, title="Executive Summary", border_style=tier_color))


if __name__ == "__main__":
    main()
