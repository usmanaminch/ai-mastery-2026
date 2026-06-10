"""
prepare_corpus.py — Convert Urdu Wikipedia to MLX-LM instruction format
========================================================================
Reads the P4 processed corpus and creates JSONL instruction pairs
for fine-tuning Llama 3.2 3B with MLX-LM.

Two types of training examples:
1. Completion: raw Urdu text chunks (teaches language patterns)
2. Instruction: template-based Q&A pairs (teaches task behavior)

Output:
  data/train.jsonl  — 90% of data
  data/valid.jsonl  — 10% of data

Run: python3 prepare_corpus.py
"""

import json
import random
from pathlib import Path

CORPUS_FILE = Path("../p4-local-model-lab/data/processed/urdu_corpus.txt")
OUTPUT_DIR  = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Config ───────────────────────────────────────────────────────────
CHUNK_SIZE      = 300    # chars per training example (~50 Urdu words)
MIN_CHUNK_SIZE  = 100    # skip chunks shorter than this
MAX_EXAMPLES    = 50_000 # cap to keep training time reasonable
TRAIN_SPLIT     = 0.9
RANDOM_SEED     = 42

# ── Instruction templates ────────────────────────────────────────────
# Simple Urdu prompts that frame the Wikipedia text as an answer
INSTRUCTION_TEMPLATES = [
    ("اس متن کو مکمل کریں:",     "completion"),   # Complete this text
    ("اردو میں لکھیں:",           "completion"),   # Write in Urdu
    ("درج ذیل عبارت پڑھیں:",      "reading"),      # Read the following
    ("یہ معلومات بتائیں:",        "info"),         # Share this information
    ("اردو میں وضاحت کریں:",      "explain"),      # Explain in Urdu
]


def clean_text(text: str) -> str:
    """Remove extra whitespace and very short lines."""
    lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 20]
    return ' '.join(lines)


def make_completion_example(chunk: str) -> dict:
    """Simple text completion — model learns Urdu language patterns."""
    return {"text": chunk}


def make_instruction_example(chunk: str) -> dict:
    """Instruction-following example using Wikipedia text as response."""
    template, _ = random.choice(INSTRUCTION_TEMPLATES)
    # Split chunk: first sentence as context, rest as completion
    sentences = chunk.split('۔')
    if len(sentences) >= 2:
        prompt = template + " " + sentences[0] + "۔"
        response = '۔'.join(sentences[1:]).strip()
    else:
        prompt = template
        response = chunk

    return {
        "messages": [
            {"role": "user",      "content": prompt},
            {"role": "assistant", "content": response}
        ]
    }


def prepare():
    print(f"Reading corpus: {CORPUS_FILE}")
    if not CORPUS_FILE.exists():
        print(f"❌ Corpus not found at {CORPUS_FILE}")
        print("   Make sure you're running from p5-urdu-finetune/")
        return

    with open(CORPUS_FILE, encoding="utf-8") as f:
        text = f.read()

    print(f"Corpus size: {len(text):,} chars")

    # Split into chunks
    chunks = []
    for i in range(0, len(text) - CHUNK_SIZE, CHUNK_SIZE // 2):  # 50% overlap
        chunk = clean_text(text[i:i + CHUNK_SIZE])
        if len(chunk) >= MIN_CHUNK_SIZE:
            chunks.append(chunk)

    print(f"Total chunks: {len(chunks):,}")

    # Sample to MAX_EXAMPLES
    random.seed(RANDOM_SEED)
    if len(chunks) > MAX_EXAMPLES:
        chunks = random.sample(chunks, MAX_EXAMPLES)
    print(f"Using: {len(chunks):,} examples")

    # Build examples — mix completion and instruction styles
    examples = []
    for i, chunk in enumerate(chunks):
        if i % 3 == 0:
            # 1/3 instruction-following format
            examples.append(make_instruction_example(chunk))
        else:
            # 2/3 raw completion format
            examples.append(make_completion_example(chunk))

    # Shuffle and split
    random.shuffle(examples)
    split = int(len(examples) * TRAIN_SPLIT)
    train = examples[:split]
    valid = examples[split:]

    # Save JSONL
    train_path = OUTPUT_DIR / "train.jsonl"
    valid_path = OUTPUT_DIR / "valid.jsonl"

    with open(train_path, "w", encoding="utf-8") as f:
        for ex in train:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    with open(valid_path, "w", encoding="utf-8") as f:
        for ex in valid:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    print(f"\n✅ Train: {len(train):,} examples → {train_path}")
    print(f"✅ Valid: {len(valid):,} examples → {valid_path}")

    # Preview 3 examples
    print(f"\n── Sample examples ──────────────────────")
    for ex in examples[:3]:
        if "text" in ex:
            print(f"\n[Completion]\n{ex['text'][:120]}...")
        else:
            print(f"\n[Instruction]")
            print(f"  User: {ex['messages'][0]['content'][:80]}...")
            print(f"  Asst: {ex['messages'][1]['content'][:80]}...")

    print(f"\n✅ Corpus ready for MLX-LM fine-tuning")
    print(f"   Next: mlx_lm.lora --model models/llama-3.2-3b-instruct-4bit --train --data data/")

if __name__ == "__main__":
    prepare()
