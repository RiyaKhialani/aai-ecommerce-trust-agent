"""
Generates a formal, high-resolution academic Conceptual System Design (CSD) diagram (Figure 3.1)
strictly adhering to formal academic publishing standards:
- Grayscale / Monochrome palette (NO BLUE, no rainbow pastel AI colors).
- Large, crisp, bold Times New Roman typography readable at 100% scale in Word.
- Hierarchical 10-agent multi-agent architecture.
- Zero overlapping, perfect padding, beautiful framing.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import textwrap

def create_formal_csd_diagram(output_path="csd_architecture_diagram.png"):
    # 9.2 x 11.2 inches at 300 DPI
    fig, ax = plt.subplots(figsize=(9.2, 11.4), dpi=300)
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#FFFFFF')
    ax.axis('off')
    ax.set_xlim(0, 9.2)
    ax.set_ylim(0, 11.4)

    # 1. Title Banner
    ax.text(
        4.6, 11.08,
        "CONCEPTUAL SYSTEM DESIGN (CSD) ARCHITECTURE",
        ha='center', va='center',
        fontsize=13.5, fontweight='bold',
        fontfamily='Times New Roman',
        color='#000000'
    )
    ax.text(
        4.6, 10.82,
        "Autonomous 10-Agent E-commerce Trust Intelligence System (Problem Statement PS-11)",
        ha='center', va='center',
        fontsize=9.8, fontstyle='italic',
        fontfamily='Times New Roman',
        color='#333333'
    )
    ax.plot([0.5, 8.7], [10.66, 10.66], color='#000000', lw=1.2)

    def draw_box(x, y, w, h, title, subtitle="", bg_color="#FFFFFF", border_color="#222222", text_color="#000000", is_header=False):
        box = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.02,rounding_size=0.06",
            facecolor=bg_color,
            edgecolor=border_color,
            linewidth=1.2,
            zorder=2
        )
        ax.add_patch(box)

        if is_header:
            ax.text(
                x + w / 2, y + h / 2 + (0.08 if subtitle else 0),
                title,
                ha='center', va='center',
                fontsize=10.5, fontweight='bold',
                fontfamily='Times New Roman',
                color=text_color,
                zorder=4
            )
            if subtitle:
                ax.text(
                    x + w / 2, y + h / 2 - 0.12,
                    subtitle,
                    ha='center', va='center',
                    fontsize=8.5, fontstyle='italic',
                    fontfamily='Times New Roman',
                    color='#DDDDDD' if text_color == '#FFFFFF' else '#555555',
                    zorder=4
                )
        else:
            ax.text(
                x + w / 2, y + h / 2 + 0.12,
                title,
                ha='center', va='center',
                fontsize=9.2, fontweight='bold',
                fontfamily='Times New Roman',
                color=text_color,
                zorder=4
            )
            if subtitle:
                wrapped = textwrap.fill(subtitle, width=40)
                ax.text(
                    x + w / 2, y + h / 2 - 0.12,
                    wrapped,
                    ha='center', va='center',
                    fontsize=7.8,
                    fontfamily='Times New Roman',
                    color='#333333' if text_color == '#000000' else '#CCCCCC',
                    linespacing=1.15,
                    zorder=4
                )

    # 1. Target Listing Input (Top Box)
    draw_box(1.6, 9.85, 6.0, 0.68, "Target Listing Input: Live URL / Benchmark Corpus", "Amazon, Flipkart, Reliance Digital | Curated Benchmark Cases", bg_color="#1A1A1A", border_color="#1A1A1A", text_color="#FFFFFF", is_header=True)

    # Arrow Down
    ax.annotate('', xy=(4.6, 9.42), xytext=(4.6, 9.85), arrowprops=dict(facecolor='#000000', edgecolor='#000000', width=1.5, headwidth=6, headlength=6), zorder=5)

    # 2. Ingestion Layer (Agent 1 & Agent 2)
    draw_box(0.6, 8.65, 3.8, 0.75, "Agent 1: Listing Ingestion Agent", "Normalizes Title, Pricing History, Merchant Age, Specs & Images", bg_color="#F6F6F8", border_color="#222222")
    draw_box(4.8, 8.65, 3.8, 0.75, "Agent 2: Review Ingestion & Segmentation", "Segments 1,780 Reviews into Cohorts; Detects Velocity Bursts", bg_color="#F6F6F8", border_color="#222222")

    # Connecting horizontal line & down arrows
    ax.plot([2.5, 6.7], [8.40, 8.40], color='#000000', lw=1.2, zorder=5)
    ax.plot([4.6, 4.6], [8.65, 8.40], color='#000000', lw=1.2, zorder=5)
    ax.annotate('', xy=(2.5, 7.95), xytext=(2.5, 8.40), arrowprops=dict(facecolor='#000000', edgecolor='#000000', width=1.5, headwidth=6, headlength=6), zorder=5)
    ax.annotate('', xy=(6.7, 7.95), xytext=(6.7, 8.40), arrowprops=dict(facecolor='#000000', edgecolor='#000000', width=1.5, headwidth=6, headlength=6), zorder=5)

    # 3. Parallel Detection Engines Container
    tier_bg = patches.FancyBboxPatch(
        (0.5, 4.95), 8.2, 2.95,
        boxstyle="round,pad=0.02,rounding_size=0.06",
        facecolor='#F5F5F7',
        edgecolor='#333333',
        linewidth=1.2,
        linestyle='--',
        zorder=1
    )
    ax.add_patch(tier_bg)

    ax.text(
        4.6, 7.72,
        "PARALLEL DETECTION ENGINES (COGNITIVE REASONING & ANOMALY AUDIT)",
        ha='center', va='center',
        fontsize=9.2, fontweight='bold',
        fontfamily='Times New Roman',
        color='#000000',
        zorder=3
    )
    ax.plot([0.8, 8.4], [7.56, 7.56], color='#888888', lw=0.8, zorder=3)

    # Left Column Engines
    draw_box(0.7, 6.75, 3.7, 0.70, "Agent 3: Compliance Classifier", "Banned medical claims, unapproved FDA/UL marks & jargon", bg_color="#FFFFFF", border_color="#222222")
    draw_box(0.7, 5.90, 3.7, 0.70, "Agent 5: Authenticity Detector", "N-gram bot templates ('changed my life') & fake buyer reports", bg_color="#FFFFFF", border_color="#222222")
    draw_box(0.7, 5.05, 3.7, 0.70, "Agent 7: Image & Counterfeit Signal", "Recycled stock photo fingerprinting & missing casing marks", bg_color="#FFFFFF", border_color="#222222")

    # Right Column Engines
    draw_box(4.8, 6.75, 3.7, 0.70, "Agent 4: Claim Extraction Agent", "Isolates battery wattage, capacity; verifies certification tags", bg_color="#FFFFFF", border_color="#222222")
    draw_box(4.8, 5.90, 3.7, 0.70, "Agent 6: Seller Behavior Agent", "Account age vs sales velocity ratio & 77% price dumping", bg_color="#FFFFFF", border_color="#222222")
    draw_box(4.8, 5.05, 3.7, 0.70, "Listing Drift & Snapshot Detector", "30-day temporal snapshot diffs (seller, price, bullet edits)", bg_color="#FFFFFF", border_color="#222222")

    # Down Arrow from Parallel Engines to Scoring
    ax.annotate('', xy=(4.6, 4.45), xytext=(4.6, 4.95), arrowprops=dict(facecolor='#000000', edgecolor='#000000', width=1.5, headwidth=6, headlength=6), zorder=5)

    # 4. Agent 8: Risk Scoring & Aggregation
    draw_box(1.2, 3.75, 6.8, 0.70, "Agent 8: Risk Scoring & Aggregation Agent", "Weighted Multi-Factor Synthesis: 35% Authenticity + 25% Compliance + 25% Seller + 15% Images", bg_color="#222222", border_color="#222222", text_color="#FFFFFF", is_header=True)

    # Down Arrow
    ax.annotate('', xy=(4.6, 3.30), xytext=(4.6, 3.75), arrowprops=dict(facecolor='#000000', edgecolor='#000000', width=1.5, headwidth=6, headlength=6), zorder=5)

    # 5. Agent 9: Plain-Language Report Agent
    draw_box(1.2, 2.58, 6.8, 0.70, "Agent 9: Plain-Language Report Agent", "Executive Summaries, Triage Recommendations, Claim Redlines, Auto Seller Audit Notices", bg_color="#F6F6F8", border_color="#222222")

    # Down Arrow
    ax.annotate('', xy=(4.6, 2.15), xytext=(4.6, 2.58), arrowprops=dict(facecolor='#000000', edgecolor='#000000', width=1.5, headwidth=6, headlength=6), zorder=5)

    # 6. Agent 10: Multi-Agent Orchestrator
    draw_box(1.2, 1.45, 6.8, 0.70, "Agent 10: Multi-Agent Orchestrator", "End-to-End Telemetry Pipeline, Latency Monitoring, Fallback & Dual-Engine Controller", bg_color="#333333", border_color="#333333", text_color="#FFFFFF", is_header=True)

    # Down Arrow
    ax.annotate('', xy=(4.6, 1.05), xytext=(4.6, 1.45), arrowprops=dict(facecolor='#000000', edgecolor='#000000', width=1.5, headwidth=6, headlength=6), zorder=5)

    # 7. Final Deliverable Output Box
    draw_box(0.8, 0.35, 7.6, 0.68, "Output: Enterprise Trust Dashboard & Evidentiary Dossier", "Calibrated Trust Score (0-100), Triage Verdict, Interactive Streamlit UI & Edge Telemetry", bg_color="#000000", border_color="#000000", text_color="#FFFFFF", is_header=True)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, facecolor='#FFFFFF', edgecolor='none', bbox_inches='tight')
    plt.close()
    print(f"SUCCESS: Formal CSD architecture diagram generated at {output_path}")

if __name__ == "__main__":
    create_formal_csd_diagram()
