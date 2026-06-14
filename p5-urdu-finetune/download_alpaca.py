"""
download_alpaca.py — Download Urdu instruction dataset and prep for MLX-LM
Run: python3 download_alpaca.py
"""
import json, random
from pathlib import Path

OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)

TRAIN_SPLIT = 0.9
RANDOM_SEED = 42

def convert_to_mlx(examples):
    """Convert alpaca format to MLX-LM messages format."""
    out = []
    for ex in examples:
        instruction = ex.get("instruction", "").strip()
        input_text  = ex.get("input", "").strip()
        output      = ex.get("output", "").strip()
        if not instruction or not output:
            continue
        prompt = f"{instruction}\n{input_text}".strip() if input_text else instruction
        out.append({"messages": [
            {"role": "user",      "content": prompt},
            {"role": "assistant", "content": output}
        ]})
    return out

def load_and_save():
    from datasets import load_dataset

    # Try multiple known Urdu instruction dataset names
    candidates = [
        "umarbutool/alpaca-urdu-51k",
        "iproskawsar/alpaca-urdu",
        "HydraLM/alpaca-urdu",
        "iahsan-jalal/alpaca-data-urdu",
    ]

    dataset = None
    used_name = None
    for name in candidates:
        try:
            print(f"Trying: {name}...")
            dataset = load_dataset(name, split="train")
            used_name = name
            print(f"✅ Found: {name} ({len(dataset)} examples)")
            break
        except Exception as e:
            print(f"  Not found: {e}")
            continue

    if dataset is None:
        print("\n⚠️  No Urdu alpaca dataset found on HuggingFace.")
        print("   Falling back to Wikipedia corpus (already prepared).")
        print("   data/train.jsonl and data/valid.jsonl are already ready.")
        return

    # Convert to MLX format
    examples = [dataset[i] for i in range(len(dataset))]
    converted = convert_to_mlx(examples)
    print(f"Converted: {len(converted):,} valid examples")

    # Shuffle and split
    random.seed(RANDOM_SEED)
    random.shuffle(converted)
    split = int(len(converted) * TRAIN_SPLIT)
    train = converted[:split]
    valid = converted[split:]

    # Save
    with open(OUTPUT_DIR / "train.jsonl", "w", encoding="utf-8") as f:
        for ex in train:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    with open(OUTPUT_DIR / "valid.jsonl", "w", encoding="utf-8") as f:
        for ex in valid:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    print(f"\n✅ Train: {len(train):,} → data/train.jsonl")
    print(f"✅ Valid: {len(valid):,} → data/valid.jsonl")
    print(f"\nSample:")
    ex = train[0]
    print(f"  User: {ex['messages'][0]['content'][:80]}")
    print(f"  Asst: {ex['messages'][1]['content'][:80]}")
    print(f"\n✅ Ready. Run fine-tuning:")
    print(f"   python -m mlx_lm.lora \\")
    print(f"     --model models/llama-3.2-3b-instruct-4bit \\")
    print(f"     --train --data data/ \\")
    print(f"     --iters 1000 --batch-size 4 --lora-layers 8")

if __name__ == "__main__":
    load_and_save()
