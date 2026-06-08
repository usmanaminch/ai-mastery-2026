"""
visualize_attention.py — Attention visualization for UrduGPT
=============================================================
Loads the trained model and extracts attention weights.
Answers the question: what did each attention head learn about Urdu?

This is the interpretability layer — the P4 Week 2 core deliverable.
Nobody has done attention/circuit analysis on a Urdu transformer before.

Run: python3 visualize_attention.py
"""

import torch
import json
import numpy as np
from pathlib import Path
from model import UrduGPT, DEVICE, BLOCK_SIZE, N_HEAD, N_LAYER, N_EMBD
from tokenizer import UrduTokenizer

CHECKPOINT   = Path("checkpoints/urdu_gpt_final.pt")
VOCAB_FILE   = Path("data/processed/vocab.json")
OUTPUT_DIR   = Path("attention_maps")
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Load model with attention capture ───────────────────────────────
class UrduGPTWithAttention(UrduGPT):
    """Extends UrduGPT to capture attention weights during forward pass."""

    def __init__(self):
        super().__init__()
        self.attention_weights = {}   # head_layer → (T, T) attention matrix

    def forward(self, idx, targets=None):
        B, T = idx.shape
        tok_emb = self.token_embedding(idx)
        pos_emb = self.position_embedding(torch.arange(T, device=DEVICE))
        x = tok_emb + pos_emb

        # Pass through blocks and capture attention weights
        for layer_idx, block in enumerate(self.blocks):
            # Capture attention weights from each head in this block
            x_normed = block.ln1(x)
            for head_idx, head in enumerate(block.attention.heads):
                B_, T_, C_ = x_normed.shape
                head_size = head.key.out_features
                k = head.key(x_normed)
                q = head.query(x_normed)
                scores = q @ k.transpose(-2, -1) * (head_size ** -0.5)
                scores = scores.masked_fill(head.tril[:T_, :T_] == 0, float("-inf"))
                weights = torch.softmax(scores, dim=-1)
                key = f"L{layer_idx}H{head_idx}"
                self.attention_weights[key] = weights[0].detach().cpu()

            x = block(x)

        x = self.ln_final(x)
        logits = self.lm_head(x)
        loss = None
        if targets is not None:
            B, T, V = logits.shape
            loss = torch.nn.functional.cross_entropy(
                logits.view(B*T, V), targets.view(B*T)
            )
        return logits, loss


def load_model(checkpoint_path: Path) -> UrduGPTWithAttention:
    """Load trained weights into the attention-capturing model."""
    model = UrduGPTWithAttention().to(DEVICE)
    state = torch.load(checkpoint_path, map_location=DEVICE, weights_only=True)
    model.load_state_dict(state)
    model.eval()
    print(f"✅ Model loaded from {checkpoint_path}")
    return model


def get_attention_for_text(model, tokenizer, text: str) -> dict:
    """Run a forward pass on text and return attention weights per head."""
    ids = tokenizer.encode(text)
    if len(ids) > BLOCK_SIZE:
        ids = ids[:BLOCK_SIZE]
    idx = torch.tensor([ids], dtype=torch.long, device=DEVICE)

    with torch.no_grad():
        model(idx)

    return {k: v[:len(ids), :len(ids)].numpy()
            for k, v in model.attention_weights.items()}


def terminal_heatmap(matrix: np.ndarray, chars: list, title: str):
    """Print a simple terminal attention heatmap."""
    T = len(chars)
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")

    # Header row
    header = "     " + " ".join(f"{c:>2}" for c in chars)
    print(header)

    for i, row_char in enumerate(chars):
        row = f"  {row_char:>2} "
        for j in range(T):
            val = matrix[i][j]
            # Map to block character density
            if val > 0.5:   block = "█"
            elif val > 0.3: block = "▓"
            elif val > 0.1: block = "▒"
            elif val > 0.02:block = "░"
            else:           block = " "
            row += f"  {block}"
        print(row)


def analyze_head_behavior(attn_weights: dict, chars: list) -> dict:
    """
    Classify what each head appears to be doing:
    - Local: attends mostly to nearby positions
    - Uniform: spreads attention evenly
    - Previous: attends mostly to the previous token
    - Self: attends mostly to itself
    """
    T = len(chars)
    behaviors = {}

    for key, matrix in attn_weights.items():
        if matrix.shape[0] < 2:
            continue

        # Diagonal strength (self-attention)
        diag = np.mean([matrix[i][i] for i in range(T)])

        # Local attention (within 2 positions)
        local = np.mean([
            matrix[i][max(0,i-2):i+3].sum()
            for i in range(T)
        ])

        # Previous token attention
        prev = np.mean([matrix[i][max(0,i-1)] for i in range(1, T)])

        # Entropy (uniform = high entropy)
        safe = np.clip(matrix, 1e-9, 1.0)
        entropy = -np.sum(safe * np.log(safe), axis=1).mean()
        max_entropy = np.log(T)
        uniformity = entropy / max_entropy if max_entropy > 0 else 0

        if diag > 0.4:       behavior = "SELF"
        elif prev > 0.4:     behavior = "PREV"
        elif local > 0.6:    behavior = "LOCAL"
        elif uniformity > 0.7: behavior = "UNIFORM"
        else:                behavior = "MIXED"

        behaviors[key] = {
            "behavior": behavior,
            "diag": round(float(diag), 3),
            "local": round(float(local), 3),
            "prev": round(float(prev), 3),
            "uniformity": round(float(uniformity), 3),
        }
    return behaviors


def run_analysis():
    tokenizer = UrduTokenizer.from_vocab(VOCAB_FILE)
    model = load_model(CHECKPOINT)

    # Test phrases — common Urdu patterns
    test_phrases = [
        "پاکستان",           # Pakistan (proper noun)
        "وہ گھر گیا",        # He went home (simple sentence)
        "کتاب پڑھنا",        # Reading a book (verb phrase)
        "بہت اچھا ہے",       # Very good (predicate)
    ]

    print(f"\n{'='*60}")
    print(f"  UrduGPT Attention Analysis")
    print(f"  {N_LAYER} layers × {N_HEAD} heads = {N_LAYER * N_HEAD} total heads")
    print(f"{'='*60}")

    all_results = {}

    for phrase in test_phrases:
        encoded = tokenizer.encode(phrase)
        if not encoded:
            continue
        chars = [tokenizer.int_to_char.get(i, "?") for i in encoded]

        print(f"\n\nPhrase: {phrase}")
        print(f"Tokens: {chars}")

        attn = get_attention_for_text(model, tokenizer, phrase)
        behaviors = analyze_head_behavior(attn, chars)

        # Print behavior summary
        print(f"\n  Head behavior summary:")
        print(f"  {'Head':<8} {'Behavior':<10} {'Self':>6} {'Local':>6} {'Prev':>6} {'Uniform':>8}")
        print(f"  {'─'*50}")
        for key in sorted(behaviors.keys()):
            b = behaviors[key]
            print(f"  {key:<8} {b['behavior']:<10} {b['diag']:>6.3f} {b['local']:>6.3f} {b['prev']:>6.3f} {b['uniformity']:>8.3f}")

        # Show most interesting head (highest local attention — likely morphology)
        most_local = max(behaviors.items(), key=lambda x: x[1]['local'])
        terminal_heatmap(
            attn[most_local[0]],
            chars,
            f"Most local head: {most_local[0]} ({most_local[1]['behavior']})"
        )

        all_results[phrase] = {
            "chars": chars,
            "behaviors": behaviors
        }

    # Save results
    output = OUTPUT_DIR / "attention_analysis.json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n\n✅ Full analysis saved: {output}")
    print("   Next: plot_attention.py — generate visual heatmaps for usmanc.com")


if __name__ == "__main__":
    run_analysis()
