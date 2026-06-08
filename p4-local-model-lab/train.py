"""
train.py — Training loop for UrduGPT
=====================================
Trains the transformer on the Urdu corpus.
Logs loss every N steps, saves checkpoints, generates sample text.

Run: python3 train.py
"""

import torch
import time
import json
from pathlib import Path
from model import UrduGPT, DEVICE, BLOCK_SIZE, N_EMBD, N_HEAD, N_LAYER, VOCAB_SIZE
from dataloader import load_corpus, get_splits, get_batch, BATCH_SIZE, ENCODED_FILE
from tokenizer import UrduTokenizer

# ── Training config ─────────────────────────────────────────────────
MAX_STEPS    = 5000       # total training steps (increase for better results)
EVAL_STEPS   = 500        # evaluate on val set every N steps
SAVE_STEPS   = 1000       # save checkpoint every N steps
LR           = 3e-4       # learning rate (AdamW standard for transformers)
CHECKPOINT   = Path("checkpoints")
LOG_FILE     = Path("training_log.json")

CORPUS_FILE  = Path("data/processed/urdu_corpus.txt")
VOCAB_FILE   = Path("data/processed/vocab.json")
CHECKPOINT.mkdir(exist_ok=True)


@torch.no_grad()
def estimate_loss(model, train_data, val_data, eval_iters=50):
    """Estimate loss on train and val splits (average over eval_iters batches)."""
    model.eval()
    losses = {}
    for split_name, split_data in [("train", train_data), ("val", val_data)]:
        split_losses = []
        for _ in range(eval_iters):
            x, y = get_batch(split_data)
            _, loss = model(x, y)
            split_losses.append(loss.item())
        losses[split_name] = sum(split_losses) / len(split_losses)
    model.train()
    return losses


def generate_sample(model, tokenizer, seed_text="پاکستان", max_tokens=200):
    """Generate sample Urdu text from a seed string."""
    model.eval()
    encoded = tokenizer.encode(seed_text)
    if not encoded:
        encoded = [0]
    idx = torch.tensor([encoded], dtype=torch.long, device=DEVICE)
    with torch.no_grad():
        out = model.generate(idx, max_new_tokens=max_tokens)
    generated = tokenizer.decode(out[0].tolist())
    model.train()
    return generated


def train():
    print(f"{'='*60}")
    print(f"  UrduGPT Training")
    print(f"  Device:     {DEVICE}")
    print(f"  Steps:      {MAX_STEPS:,}")
    print(f"  Batch size: {BATCH_SIZE}")
    print(f"  Block size: {BLOCK_SIZE}")
    print(f"{'='*60}\n")

    # Load data
    data = load_corpus(CORPUS_FILE, VOCAB_FILE, ENCODED_FILE)
    train_data, val_data = get_splits(data)
    tokenizer = UrduTokenizer.from_vocab(VOCAB_FILE)

    # Init model
    model = UrduGPT().to(DEVICE)
    params = model.count_parameters()
    print(f"Model: {params:,} parameters ({params/1e6:.1f}M)\n")

    # Optimizer — AdamW is standard for transformers
    # Why AdamW over SGD? Adaptive learning rates per parameter + weight decay
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR)

    # Training log
    log = {"steps": [], "train_loss": [], "val_loss": [], "time_s": []}
    start_time = time.time()

    print(f"{'Step':>6}  {'Train Loss':>10}  {'Val Loss':>10}  {'Time':>8}")
    print("─" * 45)

    for step in range(MAX_STEPS + 1):
        # Evaluate periodically
        if step % EVAL_STEPS == 0:
            losses = estimate_loss(model, train_data, val_data)
            elapsed = time.time() - start_time
            print(f"{step:>6}  {losses['train']:>10.4f}  {losses['val']:>10.4f}  {elapsed:>6.0f}s")

            log["steps"].append(step)
            log["train_loss"].append(losses["train"])
            log["val_loss"].append(losses["val"])
            log["time_s"].append(elapsed)

            # Save log
            with open(LOG_FILE, "w") as f:
                json.dump(log, f, indent=2)

        # Save checkpoint
        if step % SAVE_STEPS == 0 and step > 0:
            ckpt_path = CHECKPOINT / f"urdu_gpt_step{step}.pt"
            torch.save({
                "step": step,
                "model_state": model.state_dict(),
                "optimizer_state": optimizer.state_dict(),
                "val_loss": losses["val"],
            }, ckpt_path)
            print(f"  → Checkpoint saved: {ckpt_path}")

        if step == MAX_STEPS:
            break

        # Training step
        x, y = get_batch(train_data)
        logits, loss = model(x, y)

        optimizer.zero_grad()
        loss.backward()
        # Gradient clipping — prevents exploding gradients
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

    # Final generation sample
    print(f"\n{'='*60}")
    print("Generating sample Urdu text...")
    sample = generate_sample(model, tokenizer, seed_text="پاکستان")
    print(f"Seed: پاکستان")
    print(f"Generated: {sample[:300]}")

    # Save final model
    final_path = CHECKPOINT / "urdu_gpt_final.pt"
    torch.save(model.state_dict(), final_path)
    print(f"\n✅ Training complete. Model saved: {final_path}")
    print(f"   Total time: {(time.time()-start_time)/60:.1f} minutes")


if __name__ == "__main__":
    train()
