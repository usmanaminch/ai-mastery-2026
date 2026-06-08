"""
plot_attention.py — Visual attention heatmaps for UrduGPT
=========================================================
Reads attention_maps/attention_analysis.json and generates
heatmap images for the usmanc.com analysis post.

Run: python3 plot_attention.py
Output: attention_maps/*.png
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
import os
import os
import arabic_reshaper
from bidi.algorithm import get_display
from matplotlib import font_manager

# Use Geeza Pro — macOS built-in Arabic/Urdu font
_ARABIC_FONTS = [
    '/System/Library/Fonts/GeezaPro.ttc',
    '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
    '/Library/Fonts/Arial Unicode.ttf',
]
_urdu_font = None
for _fp in _ARABIC_FONTS:
    if os.path.exists(_fp):
        _urdu_font = font_manager.FontProperties(fname=_fp)
        plt.rcParams['font.family'] = 'sans-serif'
        break

def u(text: str) -> str:
    """Reshape Urdu text for correct matplotlib rendering."""
    try:
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)
    except Exception:
        return str(text)

INPUT  = Path("attention_maps/attention_analysis.json")
OUTPUT = Path("attention_maps")

# Color scheme matching usmanc.com dark theme
COLORS = {
    "PREV":    "#7F77DD",  # purple
    "LOCAL":   "#1D9E75",  # teal
    "SELF":    "#D85A30",  # coral
    "UNIFORM": "#666666",  # gray
    "MIXED":   "#BA7517",  # amber
}


def plot_head_behavior_summary(all_results: dict):
    """
    Bar chart: how many heads of each type per layer.
    Shows the hierarchical shift from PREV → LOCAL across layers.
    """
    # Aggregate across all phrases
    layer_counts = {}
    for phrase_data in all_results.values():
        for key, data in phrase_data["behaviors"].items():
            layer = int(key[1])
            behavior = data["behavior"]
            if layer not in layer_counts:
                layer_counts[layer] = {}
            layer_counts[layer][behavior] = layer_counts[layer].get(behavior, 0) + 1

    layers = sorted(layer_counts.keys())
    behavior_types = ["PREV", "LOCAL", "SELF", "MIXED", "UNIFORM"]

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#0a0a0a")
    ax.set_facecolor("#111111")

    x = np.arange(len(layers))
    width = 0.15
    for i, btype in enumerate(behavior_types):
        counts = [layer_counts[l].get(btype, 0) for l in layers]
        if sum(counts) == 0:
            continue
        bars = ax.bar(x + i * width, counts, width,
                      label=btype, color=COLORS.get(btype, "#888"),
                      alpha=0.85, edgecolor="#0a0a0a")

    ax.set_xlabel("Layer", color="#e5e5e5", fontsize=11)
    ax.set_ylabel("Head count (across all phrases)", color="#e5e5e5", fontsize=11)
    ax.set_title("Attention Head Specialization by Layer\nUrduGPT — 11M params, 290M char corpus",
                 color="#e5e5e5", fontsize=13, pad=15)
    ax.set_xticks(x + width * 2)
    ax.set_xticklabels([f"L{l}" for l in layers], color="#999")
    ax.tick_params(colors="#999")
    ax.spines[['bottom','left']].set_color("#333")
    ax.spines[['top','right']].set_visible(False)

    legend = ax.legend(facecolor="#1a1a1a", edgecolor="#333", labelcolor="#ccc",
                       title="Behavior", title_fontsize=9)
    legend.get_title().set_color("#999")

    plt.tight_layout()
    out = OUTPUT / "head_behavior_by_layer.png"
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor="#0a0a0a")
    plt.close()
    print(f"✅ Saved: {out}")


def plot_attention_heatmap(matrix: np.ndarray, chars: list,
                            title: str, filename: str):
    """Single attention head heatmap."""
    fig, ax = plt.subplots(figsize=(max(5, len(chars)*0.6), max(4, len(chars)*0.5)))
    fig.patch.set_facecolor("#0a0a0a")
    ax.set_facecolor("#0a0a0a")

    im = ax.imshow(matrix, cmap="Purples", aspect="auto", vmin=0, vmax=1)
    plt.colorbar(im, ax=ax, fraction=0.04).ax.yaxis.set_tick_params(color="#999")

    ax.set_xticks(range(len(chars)))
    ax.set_yticks(range(len(chars)))
    ax.set_xticklabels([u(c) for c in chars], color="#e5e5e5", fontsize=11)
    ax.set_yticklabels([u(c) for c in chars], color="#e5e5e5", fontsize=11)
    ax.set_xlabel("Attends to →", color="#999", fontsize=10)
    ax.set_ylabel("← Token", color="#999", fontsize=10)
    ax.set_title(title, color="#e5e5e5", fontsize=11, pad=10)
    ax.tick_params(colors="#999")
    for spine in ax.spines.values():
        spine.set_color("#333")

    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches="tight", facecolor="#0a0a0a")
    plt.close()
    print(f"✅ Saved: {filename}")


def main():
    with open(INPUT, encoding="utf-8") as f:
        data = json.load(f)

    print(f"Generating attention heatmaps for {len(data)} phrases...\n")

    # 1. Summary bar chart across all layers
    plot_head_behavior_summary(data)

    # 2. Per-phrase: show the most PREV head (L0) vs most LOCAL head (deep layer)
    for phrase, info in data.items():
        chars = info["chars"]
        behaviors = info["behaviors"]

        # Find most PREV head (early layer specialization)
        prev_heads = [(k, v) for k, v in behaviors.items()
                      if v["behavior"] == "PREV"]
        # Find most LOCAL head (word-level specialization)
        local_heads = [(k, v) for k, v in behaviors.items()
                       if v["behavior"] == "LOCAL"]

        safe_name = phrase.replace(" ", "_").replace("/", "_")[:20]

        # We stored only behavior data, not the full matrix in JSON
        # Show the behavior profile as a radar-style bar chart instead
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        fig.patch.set_facecolor("#0a0a0a")
        fig.suptitle(u(f"Phrase: {phrase}"), color="#e5e5e5", fontsize=13, y=1.02)

        for ax_idx, (ax, head_list, label) in enumerate(
            [(axes[0], prev_heads[:6], "PREV heads (L0 — character sequences)"),
             (axes[1], local_heads[:6], "LOCAL heads (deep — word patterns)")]
        ):
            ax.set_facecolor("#111111")
            if not head_list:
                ax.text(0.5, 0.5, "None", ha="center", va="center", color="#666")
                ax.set_title(label, color="#999", fontsize=9)
                continue

            keys = [h[0] for h in head_list]
            local_vals = [h[1]["local"] for h in head_list]
            prev_vals  = [h[1]["prev"]  for h in head_list]
            self_vals  = [h[1]["diag"]  for h in head_list]

            x = np.arange(len(keys))
            w = 0.25
            ax.bar(x - w, prev_vals,  w, label="prev",  color="#7F77DD", alpha=0.85)
            ax.bar(x,     local_vals, w, label="local", color="#1D9E75", alpha=0.85)
            ax.bar(x + w, self_vals,  w, label="self",  color="#D85A30", alpha=0.85)

            ax.set_xticks(x)
            ax.set_xticklabels(keys, color="#999", fontsize=8, rotation=30)
            ax.set_ylim(0, 1)
            ax.set_title(label, color="#e5e5e5", fontsize=9)
            ax.tick_params(colors="#999")
            ax.spines[['top','right']].set_visible(False)
            ax.spines[['bottom','left']].set_color("#333")
            if ax_idx == 0:
                ax.legend(facecolor="#1a1a1a", edgecolor="#333",
                          labelcolor="#ccc", fontsize=8)

        plt.tight_layout()
        out = OUTPUT / f"behavior_{safe_name}.png"
        plt.savefig(out, dpi=150, bbox_inches="tight", facecolor="#0a0a0a")
        plt.close()
        print(f"✅ Saved: {out}")

    print(f"\n✅ All heatmaps saved to {OUTPUT}/")
    print("   Use these in the usmanc.com P4 analysis post.")


if __name__ == "__main__":
    main()
