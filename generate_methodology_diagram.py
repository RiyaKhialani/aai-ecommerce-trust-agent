"""
Generates a formal, highly legible academic methodology diagram (Figure 3.2)
strictly adhering to formal academic publishing standards:
- Grayscale / Monochrome palette (NO BLUE, no rainbow pastel AI colors).
- Large, crisp, bold Times New Roman typography readable at 100% scale in Word.
- Hierarchical 3-tier pipeline layout (Ingestion -> Parallel Engines -> Action Delivery).
- Zero overlapping, perfect padding, beautiful framing.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import textwrap

def create_formal_methodology_diagram(output_path="methodology_flow_diagram.png"):
    fig, ax = plt.subplots(figsize=(9.6, 9.4), dpi=300)
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#FFFFFF')
    ax.axis('off')
    ax.set_xlim(0, 9.6)
    ax.set_ylim(0, 9.4)

    # 1. Document Title Banner (Formal Academic Monochrome)
    ax.text(
        4.8, 9.12,
        "AUTONOMOUS E-COMMERCE PRODUCT TRUST INTELLIGENCE SYSTEM",
        ha='center', va='center',
        fontsize=13.0, fontweight='bold',
        fontfamily='Times New Roman',
        color='#000000'
    )
    ax.text(
        4.8, 8.86,
        "Methodological Workflow: Multi-Source Ingestion, Parallel Anomaly Detection, & Evidentiary Action Delivery",
        ha='center', va='center',
        fontsize=9.8, fontstyle='italic',
        fontfamily='Times New Roman',
        color='#333333'
    )
    ax.plot([0.5, 9.1], [8.70, 8.70], color='#000000', lw=1.2)

    # Helper function for drawing rounded boxes with header banners
    def draw_stage_card(x, y, w, h, title_text, bullet_items):
        # Outer card background and border
        card = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.02,rounding_size=0.06",
            facecolor='#FAFAFA',
            edgecolor='#222222',
            linewidth=1.2,
            zorder=2
        )
        ax.add_patch(card)

        # Header banner
        hdr_h = 0.38
        hdr = patches.FancyBboxPatch(
            (x, y + h - hdr_h), w, hdr_h,
            boxstyle="round,pad=0.02,rounding_size=0.06",
            facecolor='#1A1A1A',
            edgecolor='#1A1A1A',
            linewidth=1.0,
            zorder=3
        )
        ax.add_patch(hdr)

        # Header text
        ax.text(
            x + w / 2, y + h - (hdr_h / 2),
            title_text,
            ha='center', va='center',
            fontsize=10.0, fontweight='bold',
            fontfamily='Times New Roman',
            color='#FFFFFF',
            zorder=4
        )

        # Card content bullets
        curr_y = y + h - hdr_h - 0.16
        for prefix, body in bullet_items:
            # Bullet prefix
            ax.text(
                x + 0.16, curr_y,
                f"• {prefix}:",
                ha='left', va='top',
                fontsize=8.8, fontweight='bold',
                fontfamily='Times New Roman',
                color='#000000',
                zorder=4
            )
            # Body text (wrapped)
            wrapped_body = textwrap.fill(body, width=42)
            ax.text(
                x + 0.26, curr_y - 0.16,
                wrapped_body,
                ha='left', va='top',
                fontsize=8.2,
                fontfamily='Times New Roman',
                color='#222222',
                linespacing=1.18,
                zorder=4
            )
            # Advance Y based on lines
            num_lines = wrapped_body.count('\n') + 1
            curr_y -= (0.22 + num_lines * 0.15)

    # --- TIER 1: Ingestion & Normalization (Top Row) ---
    p1_items = [
        ("Listing Metadata Ingestion", "Scrapes listing prose, pricing history, merchant age & specs via Jina Reader/DOM."),
        ("Multi-Cohort Review Streams", "Ingests entire 1,780-review corpus partitioned across baseline & hijack cohorts."),
        ("Asset & Spec Extraction", "Extracts statutory marks, claimed wattages, warranties, and product gallery images.")
    ]
    draw_stage_card(0.5, 6.25, 4.15, 2.25, "PHASE 1: Data Gathering & Multi-Source Ingestion", p1_items)

    p2_items = [
        ("Text Sanitization & Cleansing", "HTML entity stripping, unicode normalization, and canonical lowercasing."),
        ("Regex Currency & Specs Parsing", "Standardizes ₹ INR values to floats; parses numeric wattage and capacity tokens."),
        ("Longitudinal Cohort Partitioning", "Segments reviews into weekly/monthly windows; calculates unverified buyer ratios.")
    ]
    draw_stage_card(4.95, 6.25, 4.15, 2.25, "PHASE 2: Preprocessing & Cohort Normalization", p2_items)

    # Arrow Phase 1 -> Phase 2
    ax.annotate(
        '', xy=(4.90, 7.37), xytext=(4.68, 7.37),
        arrowprops=dict(facecolor='#000000', edgecolor='#000000', width=1.5, headwidth=6, headlength=6),
        zorder=5
    )

    # Arrow Phase 2 down to Phase 3
    ax.annotate(
        '', xy=(4.80, 5.92), xytext=(4.80, 6.20),
        arrowprops=dict(facecolor='#000000', edgecolor='#000000', width=1.5, headwidth=6, headlength=6),
        zorder=5
    )

    # --- TIER 2: Parallel Anomaly Detection Engines (Middle Row) ---
    tier2_bg = patches.FancyBboxPatch(
        (0.5, 3.40), 8.60, 2.40,
        boxstyle="round,pad=0.02,rounding_size=0.06",
        facecolor='#F5F5F7',
        edgecolor='#333333',
        linewidth=1.2,
        linestyle='--',
        zorder=1
    )
    ax.add_patch(tier2_bg)

    ax.text(
        4.8, 5.58,
        "PHASE 3: PARALLEL ANOMALY DETECTION ENGINES (COGNITIVE MULTI-AGENT PIPELINE)",
        ha='center', va='center',
        fontsize=9.2, fontweight='bold',
        fontfamily='Times New Roman',
        color='#000000',
        zorder=3
    )
    ax.plot([0.8, 8.8], [5.42, 5.42], color='#888888', lw=0.8, zorder=3)

    # 5 Detection Engine Blocks arranged in a neat 3 + 2 grid
    def draw_engine_box(bx, by, bw, bh, eng_num, eng_title, eng_desc):
        eb = patches.FancyBboxPatch(
            (bx, by), bw, bh,
            boxstyle="round,pad=0.02,rounding_size=0.05",
            facecolor='#FFFFFF',
            edgecolor='#222222',
            linewidth=1.0,
            zorder=3
        )
        ax.add_patch(eb)
        # Title
        ax.text(
            bx + 0.10, by + bh - 0.14,
            f"Agent {eng_num}: {eng_title}",
            ha='left', va='top',
            fontsize=8.3, fontweight='bold',
            fontfamily='Times New Roman',
            color='#000000',
            zorder=4
        )
        # Desc
        wrapped = textwrap.fill(eng_desc, width=32)
        ax.text(
            bx + 0.10, by + bh - 0.32,
            wrapped,
            ha='left', va='top',
            fontsize=7.5,
            fontfamily='Times New Roman',
            color='#222222',
            linespacing=1.16,
            zorder=4
        )

    # Row 1 of engines: 3 engines
    draw_engine_box(0.65, 4.40, 2.60, 0.86, "3", "Compliance Classifier", "Flags illegal medical claims, unapproved FDA/UL marks, & deceptive marketing buzzwords.")
    draw_engine_box(3.50, 4.40, 2.60, 0.86, "4", "Claim Extraction Agent", "Isolates battery capacity, wattage & certifications; tags confidence source & builds redlines.")
    draw_engine_box(6.35, 4.40, 2.60, 0.86, "2", "Review Velocity Engine", "Detects velocity bursts (>3x baseline or >50 reviews in 48h) and rating distribution anomalies.")

    # Row 2 of engines: 2 wider engines
    draw_engine_box(1.05, 3.52, 3.50, 0.74, "5", "Review Authenticity Detector", "Discovers N-gram bot phrase clusters ('changed my life'), unverified skew & buyer counterfeit alerts.")
    draw_engine_box(5.05, 3.52, 3.50, 0.74, "6&7", "Seller & Image Signals Agent", "Profiles merchant tenure vs volume (18-day shell accounts), price dumping (77% off) & stock photo clones.")

    # Arrow Phase 3 down to Tier 3
    ax.annotate(
        '', xy=(4.80, 3.02), xytext=(4.80, 3.35),
        arrowprops=dict(facecolor='#000000', edgecolor='#000000', width=1.5, headwidth=6, headlength=6),
        zorder=5
    )

    # --- TIER 3: Scoring & Action Delivery (Bottom Row) ---
    p4_items = [
        ("Multi-Factor Risk Scoring", "Computes calibrated Trust Score (0–100) across Authenticity (35%), Compliance (25%), Seller (25%), and Images (15%)."),
        ("Calibrated Triage Tiers", "Categorizes listing into LOW RISK (≥75), MEDIUM RISK (50–74), or HIGH RISK (<50)."),
        ("Itemized Evidentiary Dossier", "Compiles transparent empirical citations, policy violations, and confidence scores for human T&S reviewers.")
    ]
    draw_stage_card(0.5, 0.45, 4.15, 2.45, "PHASE 4: Risk Scoring & Evidence Aggregation", p4_items)

    p5_items = [
        ("Plain-Language Action Report", "Synthesizes plain-language executive triage summaries with priority risk recommendations."),
        ("Contract Claim Redline Diff", "Generates before/after specification diffs striking out unverified assertions in favor of compliant text."),
        ("Streamlit Enterprise Dashboard", "Delivers reactive UI with real-time multi-agent execution stepper, Plotly burst charts & audit drawer.")
    ]
    draw_stage_card(4.95, 0.45, 4.15, 2.45, "PHASE 5: Evidentiary Triage & Action Delivery", p5_items)

    # Arrow Phase 4 -> Phase 5
    ax.annotate(
        '', xy=(4.90, 1.67), xytext=(4.68, 1.67),
        arrowprops=dict(facecolor='#000000', edgecolor='#000000', width=1.5, headwidth=6, headlength=6),
        zorder=5
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, facecolor='#FFFFFF', edgecolor='none', bbox_inches='tight')
    plt.close()
    print(f"SUCCESS: Formal academic methodology diagram generated at {output_path}")

if __name__ == "__main__":
    create_formal_methodology_diagram()
