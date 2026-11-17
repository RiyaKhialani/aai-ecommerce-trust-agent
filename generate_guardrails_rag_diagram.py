"""
Generates a formal, high-resolution 300 DPI academic architectural diagram
for Enterprise Safety Guardrails, Model Context Protocol (MCP), and RAG Knowledge Architecture (Figure 3.3).
Strictly formal academic monochrome/charcoal, 100% Times New Roman, large readable typography.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches

def generate_guardrails_rag_diagram(output_path="guardrails_rag_mcp_diagram.png"):
    fig, ax = plt.subplots(figsize=(9.2, 10.5), dpi=300)
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#FFFFFF')
    ax.axis('off')
    ax.set_xlim(0, 9.2)
    ax.set_ylim(0, 10.5)

    # 1. Header
    ax.text(
        4.6, 10.15,
        "ENTERPRISE SAFETY GUARDRAILS, MCP PROTOCOL & RAG STORAGE",
        ha='center', va='center',
        fontsize=12.5, fontweight='bold',
        fontfamily='Times New Roman',
        color='#000000'
    )
    ax.text(
        4.6, 9.88,
        "Two-Tiered Safety Defenses, Standardized Tool Context, and Statutory Knowledge Persistence",
        ha='center', va='center',
        fontsize=9.5, fontstyle='italic',
        fontfamily='Times New Roman',
        color='#333333'
    )
    ax.plot([0.5, 8.7], [9.72, 9.72], color='#000000', lw=1.2)

    def draw_component(x, y, w, h, title, subtitle, bullets, fill_color="#FCFCFC", border_color="#262626"):
        box = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.02,rounding_size=0.05",
            facecolor=fill_color,
            edgecolor=border_color,
            linewidth=1.1,
            zorder=2
        )
        ax.add_patch(box)

        # Header pill
        hpill = patches.FancyBboxPatch(
            (x + 0.08, y + h - 0.38), w - 0.16, 0.30,
            boxstyle="round,pad=0.01,rounding_size=0.04",
            facecolor='#262626',
            edgecolor='#000000',
            linewidth=0.7,
            zorder=3
        )
        ax.add_patch(hpill)
        ax.text(
            x + w/2, y + h - 0.23,
            title,
            ha='center', va='center',
            fontsize=9.2, fontweight='bold',
            fontfamily='Times New Roman',
            color='#FFFFFF', zorder=4
        )

        if subtitle:
            ax.text(
                x + w/2, y + h - 0.52,
                subtitle,
                ha='center', va='center',
                fontsize=8.0, fontstyle='italic',
                fontfamily='Times New Roman',
                color='#444444', zorder=4
            )

        # Bullets
        b_y = y + h - 0.72
        for b in bullets:
            ax.text(
                x + 0.15, b_y,
                f"• {b}",
                ha='left', va='top',
                fontsize=7.8, fontfamily='Times New Roman',
                color='#111111', zorder=4
            )
            b_y -= 0.28

    # Tier 1: Input Guardrails (Top Left)
    draw_component(
        0.5, 6.70, 3.95, 2.75,
        "INPUT SAFETY GUARDRAILS",
        "Deterministic Pre-LLM Boundary Protection",
        [
            "Prompt Injection & Jailbreak Defense (DAN patterns)",
            "System Prompt Override & Role Leakage Detection",
            "PII Masking (Credit Cards, Phone Numbers, Aadhaar)",
            "Malicious Script & SQL Injection Blocker",
            "Domain Scope Alignment (E-commerce Triage Only)"
        ]
    )

    # Tier 2: Output Guardrails (Top Right)
    draw_component(
        4.75, 6.70, 3.95, 2.75,
        "OUTPUT SAFETY GUARDRAILS",
        "Mathematical Post-LLM Invariant Enforcement",
        [
            "Trust Score Bounded Invariant: Score in [0.0, 100.0]",
            "Risk Tier Threshold Consistency Validation",
            "Anti-Hallucination Counterfeit Override Check",
            "Mandatory Statutory Disclaimers Injected",
            "JSON-Schema Telemetry Guarantee Check"
        ]
    )

    # Connectors between Input and Output Guardrails
    ax.annotate(
        "Safe Ingestion", xy=(4.65, 8.2), xytext=(4.05, 8.2),
        arrowprops=dict(arrowstyle="->", color="#000000", lw=1.2),
        fontsize=7.5, fontfamily='Times New Roman', ha='center', va='bottom'
    )

    # Tier 3: Model Context Protocol (MCP) Server (Middle Row)
    draw_component(
        0.5, 3.65, 8.2, 2.75,
        "MODEL CONTEXT PROTOCOL (MCP) INTERFACE ARCHITECTURE",
        "Standardized JSON-RPC 2.0 Stdio Integration for AI Agents & IDE Extensions",
        [
            "Exposed Tools: audit_listing (automated audit), query_compliance_rag (statutory retrieval), validate_guardrails, get_audit_history, evaluate_llm_optimization",
            "Exposed Context Resources: trust://policies (regulatory clauses), trust://benchmarks (catalog datasets), trust://latest_audit (live telemetry)",
            "Bidirectional Interoperability: Seamless integration into Antigravity, Claude Code, Cursor, and enterprise IDE copilots without API lock-in",
            "Deterministic FastMCP Stdio Loop: Zero external network dependencies; operates seamlessly offline in isolated enterprise test environments"
        ]
    )

    # Tier 4: Storage & RAG Engine (Bottom Left & Right)
    draw_component(
        0.5, 0.50, 3.95, 2.85,
        "PERSISTENT DATA STORAGE (SQLite WAL)",
        "ACID-Compliant Relational Data Foundation",
        [
            "audit_records: Audit IDs, timestamps, verdicts, redlines",
            "chat_history: Session IDs, user queries, LLM citations",
            "guardrail_events: Injection attempts, sanitized PII, scores",
            "rag_knowledge: Ingested regulatory clauses and statutes",
            "Write-Ahead Logging (WAL): High concurrent throughput"
        ]
    )

    draw_component(
        4.75, 0.50, 3.95, 2.85,
        "RETRIEVAL-AUGMENTED GENERATION (RAG)",
        "BM25 / TF-IDF Grounded Compliance Engine",
        [
            "FDA 21 CFR § 101.93 & DSHEA Disease Cure Prohibitions",
            "Bureau of Indian Standards (BIS) IS 13252 / IS 16046 (CRS)",
            "Underwriters Laboratories (UL 2056) Battery Safety Mandates",
            "FTC 16 CFR Part 255 Synthesized Endorsement Regulations",
            "CDSCO Drugs & Cosmetics Act IS 4707 Counterfeit Standards"
        ]
    )

    # Connecting Arrows
    ax.annotate(
        "Persist Records", xy=(2.475, 3.35), xytext=(2.475, 3.65),
        arrowprops=dict(arrowstyle="->", color="#000000", lw=1.2)
    )
    ax.annotate(
        "Ground Reasoning", xy=(6.725, 3.65), xytext=(6.725, 3.35),
        arrowprops=dict(arrowstyle="->", color="#000000", lw=1.2)
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, facecolor='#FFFFFF')
    plt.close()
    print(f"SUCCESS: Guardrails/RAG/MCP diagram generated at {output_path}")

if __name__ == "__main__":
    generate_guardrails_rag_diagram()
