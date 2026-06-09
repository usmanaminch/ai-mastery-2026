"""
generate.py — Interactive text generation from trained UrduGPT
==============================================================
Load the trained checkpoint and generate Urdu text from seeds.
Used for Week 3: compare outputs against Gemma 4 on same prompts.

Run: python3 generate.py
"""

import torch
import json
import time
import requests
from pathlib import Path
from model import UrduGPT, DEVICE, BLOCK_SIZE
from tokenizer import UrduTokenizer

CHECKPOINT = Path("checkpoints/urdu_gpt_final.pt")
VOCAB_FILE  = Path("data/processed/vocab.json")

# ── Comparison prompts for Week 3 ───────────────────────────────────
# Same seeds run on both UrduGPT and Gemma 4.
# Documents the capability gap — core of the P4 analysis.
COMPARISON_SEEDS = [
    "پاکستان",           # Pakistan (proper noun — did it learn geography?)
    "علم",              # knowledge (abstract concept)
    "محبت",             # love (emotional word)
    "کراچی میں",        # In Karachi (city + postposition — grammar test)
    "آج کا موسم",       # Today's weather (common phrase)
]


def load_model() -> UrduGPT:
    model = UrduGPT().to(DEVICE)
    state = torch.load(CHECKPOINT, map_location=DEVICE, weights_only=True)
    model.load_state_dict(state)
    model.eval()
    print(f"✅ UrduGPT loaded ({sum(p.numel() for p in model.parameters()):,} params)")
    return model


def generate(model: UrduGPT, tokenizer: UrduTokenizer,
             seed: str, max_tokens: int = 150,
             temperature: float = 0.8) -> str:
    """
    Generate text from a seed string.
    Temperature: 0.1 = conservative, 1.0 = creative, 1.5 = chaotic
    """
    ids = tokenizer.encode(seed)
    if not ids:
        ids = [0]
    idx = torch.tensor([ids], dtype=torch.long, device=DEVICE)

    with torch.no_grad():
        for _ in range(max_tokens):
            idx_cond = idx[:, -BLOCK_SIZE:]
            logits, _ = model(idx_cond)
            logits = logits[:, -1, :] / temperature
            probs = torch.softmax(logits, dim=-1)
            idx_next = torch.multinomial(probs, num_samples=1)
            idx = torch.cat([idx, idx_next], dim=1)

    return tokenizer.decode(idx[0].tolist())


def query_gemma(seed: str, max_tokens: int = 150) -> str:
    """Query local Gemma 4 12B via Ollama for comparison."""
    prompt = f"Continue this Urdu text naturally (respond only in Urdu script, no explanation):\n{seed}"
    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma3:12b",
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": max_tokens, "temperature": 0.8}
            },
            timeout=60
        )
        return resp.json().get("response", "Gemma unavailable")
    except Exception as e:
        return f"Gemma unavailable: {e}"


def run_comparison():
    tokenizer = UrduTokenizer.from_vocab(VOCAB_FILE)
    model = load_model()

    results = []

    print(f"\n{'='*65}")
    print("  UrduGPT vs Gemma 4 12B — Side by Side Comparison")
    print(f"  Temperature: 0.8 | Max tokens: 150")
    print(f"{'='*65}\n")

    for seed in COMPARISON_SEEDS:
        print(f"Seed: {seed}")
        print("─" * 65)

        # UrduGPT
        t0 = time.time()
        urdu_out = generate(model, tokenizer, seed, max_tokens=150)
        urdu_time = time.time() - t0
        print(f"UrduGPT ({urdu_time:.1f}s):")
        print(f"  {urdu_out[:200]}")

        print()

        # Gemma 4
        t0 = time.time()
        gemma_out = query_gemma(seed, max_tokens=150)
        gemma_time = time.time() - t0
        print(f"Gemma 4 12B ({gemma_time:.1f}s):")
        print(f"  {gemma_out[:200]}")

        print()

        results.append({
            "seed": seed,
            "urdu_gpt": urdu_out,
            "urdu_gpt_time_s": round(urdu_time, 2),
            "gemma": gemma_out,
            "gemma_time_s": round(gemma_time, 2),
        })

    # Save comparison results
    out = Path("results/urdu_vs_gemma.json")
    out.parent.mkdir(exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Comparison saved: {out}")
    print("   This is the Week 3 analysis input.")
    print("   Key question: why does Gemma succeed where UrduGPT produces structure without meaning?")


def interactive():
    """Interactive generation — type a seed, see output."""
    tokenizer = UrduTokenizer.from_vocab(VOCAB_FILE)
    model = load_model()

    print("\nInteractive generation. Type a seed in Urdu (or 'q' to quit).")
    print("Temperature 0.8 — adjust in code for more/less creativity.\n")

    while True:
        seed = input("Seed: ").strip()
        if seed.lower() == 'q':
            break
        if not seed:
            continue
        out = generate(model, tokenizer, seed, max_tokens=200)
        print(f"\nGenerated:\n{out}\n")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive()
    else:
        run_comparison()
