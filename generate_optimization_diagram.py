"""
Generates a formal, high-resolution 300 DPI academic architectural diagram
for the 7 LLM Optimization Techniques and 'Which One When?' Decision Framework (Figure 5.8).
Strictly formal academic monochrome/charcoal, 100% Times New Roman, large readable typography.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches

def generate_llm_optimization_diagram(output_path="llm_optimization_diagram.png"):
    fig, ax = plt.subplots(figsize=(9.2, 11.8), dpi=300)
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#FFFFFF')
    ax.axis('off')
    ax.set_xlim(0, 9.2)
    ax.set_ylim(0, 11.8)

    # 1. Header
    ax.text(
        4.6, 11.45,
        "SEVEN ARCHITECTURAL TECHNIQUES FOR LLM INFERENCE OPTIMIZATION",
        ha='center', va='center',
        fontsize=12.5, fontweight='bold',
        fontfamily='Times New Roman',
        color='#000000'
    )
    ax.text(
        4.6, 11.18,
        "Systematic Latency Reduction, Memory Compression, and Multi-Agent Throughput Acceleration",
        ha='center', va='center',
        fontsize=9.5, fontstyle='italic',
        fontfamily='Times New Roman',
        color='#333333'
    )
    ax.plot([0.5, 8.7], [11.02, 11.02], color='#000000', lw=1.2)

    def draw_technique_card(x, y, w, h, num, title, objective, mechanism, math_spec):
        # Outer Card Border
        card = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.02,rounding_size=0.05",
            facecolor='#FCFCFC',
            edgecolor='#262626',
            linewidth=1.1,
            zorder=2
        )
        ax.add_patch(card)

        # Badge banner
        badge = patches.FancyBboxPatch(
            (x + 0.08, y + h - 0.32), 0.38, 0.24,
            boxstyle="round,pad=0.01,rounding_size=0.04",
            facecolor='#262626',
            edgecolor='#000000',
            linewidth=0.8,
            zorder=3
        )
        ax.add_patch(badge)
        ax.text(
            x + 0.27, y + h - 0.20,
            str(num),
            ha='center', va='center',
            fontsize=9.5, fontweight='bold',
            fontfamily='Times New Roman',
            color='#FFFFFF', zorder=4
        )

        # Title
        ax.text(
            x + 0.54, y + h - 0.20,
            title,
            ha='left', va='center',
            fontsize=10.0, fontweight='bold',
            fontfamily='Times New Roman',
            color='#000000', zorder=4
        )

        # Objective Pill (Right Aligned)
        obj_pill = patches.FancyBboxPatch(
            (x + w - 1.25, y + h - 0.32), 1.15, 0.24,
            boxstyle="round,pad=0.01,rounding_size=0.04",
            facecolor='#EEEEEE',
            edgecolor='#555555',
            linewidth=0.6,
            zorder=3
        )
        ax.add_patch(obj_pill)
        ax.text(
            x + w - 0.675, y + h - 0.20,
            objective,
            ha='center', va='center',
            fontsize=7.8, fontweight='bold',
            fontfamily='Times New Roman',
            color='#222222', zorder=4
        )

        # Divider line
        ax.plot([x + 0.1, x + w - 0.1], [y + h - 0.40, y + h - 0.40], color='#DDDDDD', lw=0.7, zorder=3)

        # Mechanism prose
        ax.text(
            x + 0.15, y + h - 0.62,
            f"Operation: {mechanism}",
            ha='left', va='top',
            fontsize=8.2, fontfamily='Times New Roman',
            color='#1A1A1A', zorder=4,
            wrap=True
        )

        # Formula / Metric Spec
        ax.text(
            x + 0.15, y + 0.14,
            f"Specification: {math_spec}",
            ha='left', va='bottom',
            fontsize=7.8, fontfamily='Times New Roman',
            fontstyle='italic', color='#444444', zorder=4
        )

    # 7 Technique Cards (2 columns, 3 rows + 1 wide card)
    # Column 1: x = 0.5, w = 3.95
    # Column 2: x = 4.75, w = 3.95
    card_h = 1.30

    # Row 1 (y = 9.45)
    draw_technique_card(
        0.5, 9.45, 3.95, card_h,
        1, "Quantization", "Less Memory",
        "Compress 16-bit floating weights (FP16) into 8-bit or 4-bit integers (INT8/INT4).",
        "7B Model: 14.0 GB (FP16) -> 3.5 GB (INT4) [75% VRAM Reduction]"
    )
    draw_technique_card(
        4.75, 9.45, 3.95, card_h,
        2, "Knowledge Distillation", "Smaller Model",
        "Compact student model learns to mimic probability distributions of larger teacher.",
        "Loss: L = α·CE(y, σ(z_s)) + (1-α)·T²·KL(σ(z_s/T), σ(z_t/T))"
    )

    # Row 2 (y = 7.95)
    draw_technique_card(
        0.5, 7.95, 3.95, card_h,
        3, "KV Caching", "Faster Tokens",
        "Retain past Key & Value attention tensors in GPU VRAM to eliminate recomputation.",
        "Complexity per token: Reduced from O(N^2) to O(1) attention compute"
    )
    draw_technique_card(
        4.75, 7.95, 3.95, card_h,
        4, "Continuous Batching", "More Users",
        "Dynamically inject new requests into active GPU iteration slots as sequences finish.",
        "GPU Utilization: 88-95% vs 42% in static sequential batching"
    )

    # Row 3 (y = 6.45)
    draw_technique_card(
        0.5, 6.45, 3.95, card_h,
        5, "Speculative Decoding", "Lower Latency",
        "Draft model proposes K tokens rapidly; target model verifies all in one forward pass.",
        "Speedup: 2.1x-2.8x wall-clock acceleration with mathematical exactness"
    )
    draw_technique_card(
        4.75, 6.45, 3.95, card_h,
        6, "Tensor Parallelism", "Multi-GPU",
        "Partition linear weight matrices (Q, K, V, MLP) horizontally/vertically across GPUs.",
        "Communication: All-Reduce collective per transformer layer across NVLink"
    )

    # Row 4 (y = 4.95) - Technique 7
    draw_technique_card(
        0.5, 4.95, 8.2, 1.25,
        7, "Pipeline Parallelism (Inter-Layer Model Partitioning)", "Multi-GPU Distribution",
        "Distribute sequential layers across multiple GPUs; micro-batches flow through stages concurrently (1F1B schedule).",
        "Pipeline Bubble: F_bubble = (p - 1) / (m + p - 1), where p = pipeline depth, m = micro-batch count"
    )

    # Bottom Decision Framework Box: "Which One When?"
    dec_box = patches.FancyBboxPatch(
        (0.5, 0.45), 8.2, 4.25,
        boxstyle="round,pad=0.03,rounding_size=0.06",
        facecolor='#F6F6F6',
        edgecolor='#000000',
        linewidth=1.3,
        zorder=2
    )
    ax.add_patch(dec_box)

    # Decision Header
    dec_hdr = patches.FancyBboxPatch(
        (0.7, 4.20), 7.8, 0.40,
        boxstyle="round,pad=0.01,rounding_size=0.04",
        facecolor='#262626',
        edgecolor='#000000',
        linewidth=0.8,
        zorder=3
    )
    ax.add_patch(dec_hdr)
    ax.text(
        4.6, 4.40,
        "DECISION FRAMEWORK: WHICH OPTIMIZATION TECHNIQUE WHEN?",
        ha='center', va='center',
        fontsize=10.5, fontweight='bold',
        fontfamily='Times New Roman',
        color='#FFFFFF', zorder=4
    )

    def draw_decision_row(y_pos, condition, techniques, detail):
        # Condition pill
        c_box = patches.FancyBboxPatch(
            (0.75, y_pos), 3.4, 0.90,
            boxstyle="round,pad=0.01,rounding_size=0.04",
            facecolor='#FFFFFF',
            edgecolor='#444444',
            linewidth=0.9,
            zorder=3
        )
        ax.add_patch(c_box)
        ax.text(
            0.90, y_pos + 0.65,
            condition,
            ha='left', va='center',
            fontsize=9.2, fontweight='bold',
            fontfamily='Times New Roman',
            color='#000000', zorder=4
        )
        ax.text(
            0.90, y_pos + 0.25,
            detail,
            ha='left', va='center',
            fontsize=7.8, fontfamily='Times New Roman',
            color='#555555', zorder=4
        )

        # Arrow
        ax.annotate(
            "", xy=(4.65, y_pos + 0.45), xytext=(4.25, y_pos + 0.45),
            arrowprops=dict(arrowstyle="->", color="#000000", lw=1.5),
            zorder=4
        )

        # Technique Badges Box
        t_box = patches.FancyBboxPatch(
            (4.75, y_pos), 3.75, 0.90,
            boxstyle="round,pad=0.01,rounding_size=0.04",
            facecolor='#FFFFFF',
            edgecolor='#262626',
            linewidth=0.9,
            zorder=3
        )
        ax.add_patch(t_box)

        # Draw number pills inside
        for idx, (t_num, t_name) in enumerate(techniques):
            pill_x = 4.90 + (idx * 0.88)
            num_circle = patches.Circle((pill_x + 0.12, y_pos + 0.55), 0.14, facecolor='#262626', edgecolor='#000000', lw=0.6, zorder=4)
            ax.add_patch(num_circle)
            ax.text(pill_x + 0.12, y_pos + 0.55, str(t_num), ha='center', va='center', fontsize=7.8, fontweight='bold', fontfamily='Times New Roman', color='#FFFFFF', zorder=5)
            ax.text(pill_x + 0.12, y_pos + 0.22, t_name, ha='center', va='center', fontsize=7.0, fontfamily='Times New Roman', color='#111111', zorder=5)

    # 3 Decision Conditions
    draw_decision_row(
        3.10,
        "Model Too Big for Available GPU VRAM?",
        [(1, "Quant."), (2, "Distill."), (6, "Tensor P."), (7, "Pipe P.")],
        "VRAM constraint prevents model weights loading."
    )
    draw_decision_row(
        1.85,
        "Each Output Token Generation Too Slow?",
        [(3, "KV Cache"), (5, "Spec. Dec.")],
        "High Time-Per-Output-Token (TPOT) latency."
    )
    draw_decision_row(
        0.60,
        "Too Many Concurrent Users Waiting in Queue?",
        [(4, "Cont. Batch")],
        "High queue wait times and low multi-tenant throughput."
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, facecolor='#FFFFFF')
    plt.close()
    print(f"SUCCESS: LLM optimization diagram generated at {output_path}")

if __name__ == "__main__":
    generate_llm_optimization_diagram()
