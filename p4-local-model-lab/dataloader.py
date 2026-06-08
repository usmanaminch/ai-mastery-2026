"""
dataloader.py — Batch data loader for transformer training
===========================================================

What this does:
- Loads the encoded corpus into memory as a tensor
- Splits into train (90%) and validation (10%)
- Provides get_batch() — the function the training loop calls every step

Why this matters:
- Transformers learn by predicting the NEXT character given previous ones
- get_batch() returns (x, y) where y is x shifted by 1 position
- block_size is the context window — how many chars the model sees at once
- batch_size controls how many sequences train in parallel (GPU efficiency)

Run: python3 dataloader.py  (runs a quick sanity check)
"""

import torch
import json
from pathlib import Path
from tokenizer import UrduTokenizer

# ── Config ──────────────────────────────────────────────────────────
CORPUS_FILE  = Path("data/processed/urdu_corpus.txt")
VOCAB_FILE   = Path("data/processed/vocab.json")
ENCODED_FILE = Path("data/processed/corpus_encoded.pt")

BLOCK_SIZE   = 256   # context window — chars the model sees at once
BATCH_SIZE   = 32    # sequences per training step
TRAIN_SPLIT  = 0.9   # 90% train, 10% validation

# Use MPS (Apple Silicon GPU) if available, else CPU
DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"


def encode_and_save_corpus(corpus_path: Path, vocab_path: Path, output_path: Path) -> torch.Tensor:
    """
    Encode full corpus to integers and save as a PyTorch tensor.
    This runs once — subsequent runs load from the .pt file.
    """
    print("Encoding corpus (first time — this takes ~30 seconds)...")
    tokenizer = UrduTokenizer.from_vocab(vocab_path)
    text = corpus_path.read_text(encoding="utf-8")

    # Encode in chunks to avoid memory issues
    chunk_size = 1_000_000
    encoded = []
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i+chunk_size]
        encoded.extend(tokenizer.encode(chunk))
        if (i // chunk_size) % 10 == 0:
            print(f"  {i:,} / {len(text):,} chars encoded...")

    data = torch.tensor(encoded, dtype=torch.long)
    torch.save(data, output_path)
    print(f"Encoded corpus saved: {output_path} ({data.shape[0]:,} tokens)")
    return data


def load_corpus(corpus_path: Path, vocab_path: Path, encoded_path: Path) -> torch.Tensor:
    """Load encoded corpus — from cache if available, else encode fresh."""
    if encoded_path.exists():
        print(f"Loading cached encoded corpus: {encoded_path}")
        data = torch.load(encoded_path, weights_only=True)
        print(f"Loaded {data.shape[0]:,} tokens")
        return data
    return encode_and_save_corpus(corpus_path, vocab_path, encoded_path)


def get_splits(data: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Split data into train and validation sets."""
    n = int(TRAIN_SPLIT * len(data))
    return data[:n], data[n:]


def get_batch(split_data: torch.Tensor, batch_size: int = BATCH_SIZE,
              block_size: int = BLOCK_SIZE, device: str = DEVICE):
    """
    Sample a random batch of sequences for training.

    Returns:
        x: input sequences  shape (batch_size, block_size)
        y: target sequences shape (batch_size, block_size)
           y is x shifted right by 1 — the model predicts y[i] from x[:i+1]

    Example with block_size=4:
        x = [ک, ت, ا, ب]   (the word "کتاب" = book, first 4 chars)
        y = [ت, ا, ب, ...]  (targets: predict each next char)
    """
    # Random starting positions (ensure full block fits)
    ix = torch.randint(len(split_data) - block_size, (batch_size,))
    x = torch.stack([split_data[i:i+block_size] for i in ix])
    y = torch.stack([split_data[i+1:i+block_size+1] for i in ix])
    return x.to(device), y.to(device)


if __name__ == "__main__":
    print(f"Device: {DEVICE}")
    print(f"Block size: {BLOCK_SIZE} chars")
    print(f"Batch size: {BATCH_SIZE} sequences\n")

    # Load or encode corpus
    data = load_corpus(CORPUS_FILE, VOCAB_FILE, ENCODED_FILE)

    # Split
    train_data, val_data = get_splits(data)
    print(f"\nTrain tokens: {len(train_data):,}")
    print(f"Val tokens:   {len(val_data):,}")

    # Sample a batch
    x, y = get_batch(train_data)
    print(f"\nSample batch:")
    print(f"  x shape: {x.shape}  (batch_size={BATCH_SIZE}, block_size={BLOCK_SIZE})")
    print(f"  y shape: {y.shape}")
    print(f"  x[0][:10]: {x[0][:10].tolist()}")
    print(f"  y[0][:10]: {y[0][:10].tolist()}")

    # Decode first sequence to verify
    tokenizer = UrduTokenizer.from_vocab(VOCAB_FILE)
    print(f"\nFirst sequence (x[0]) decoded:")
    print(f"  '{tokenizer.decode(x[0][:50].tolist())}'")
    print(f"\n✅ Dataloader ready. Next: model.py — build the transformer")
