"""
model.py — Urdu GPT: Transformer built from scratch
=====================================================
Following Karpathy's nanoGPT approach, implemented from first principles.

Architecture:
    Token embeddings → Positional encodings → N × Transformer blocks → Language model head

Each Transformer block:
    LayerNorm → Multi-Head Self-Attention → Residual
    LayerNorm → Feed-Forward Network      → Residual

Why each component exists:
    - Token embeddings:      convert integer IDs to dense vectors the model can reason about
    - Positional encodings:  tell the model WHERE in the sequence each token is
    - Self-attention:        let every token look at every other token and decide what's relevant
    - Multi-head attention:  run attention multiple times in parallel, each head learns different patterns
    - Feed-forward:          after attention gathers context, FFN transforms each token independently
    - Residual connections:  let gradients flow backward without vanishing (key for deep networks)
    - Layer norm:            stabilize activations so training doesn't blow up

Run: python3 model.py  (instantiates model, prints parameter count)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math

# ── Hyperparameters ─────────────────────────────────────────────────
# These are deliberately small — we're on a Mac, not an A100 cluster.
# GPT-2 Small: n_layer=12, n_head=12, n_embd=768 → 117M params
# Ours:        n_layer=6,  n_head=6,  n_embd=384 → ~10M params

VOCAB_SIZE  = 327    # unique Urdu characters (from tokenizer)
BLOCK_SIZE  = 256    # context window (chars the model sees at once)
N_EMBD      = 384    # embedding dimension (each token → 384-dim vector)
N_HEAD      = 6      # attention heads (384 / 6 = 64 dims per head)
N_LAYER     = 6      # transformer blocks stacked
DROPOUT     = 0.1    # randomly zero 10% of activations during training (regularization)

DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"


# ── Component 1: Single Attention Head ──────────────────────────────
class Head(nn.Module):
    """
    One head of self-attention.

    The core idea: each token computes a Query (what am I looking for?),
    and each token also has a Key (what do I offer?) and Value (what's my content?).
    Attention score = Query · Key^T / sqrt(d_k)
    Attention weight = softmax(scores)  [masked so we can't look at future tokens]
    Output = weighted sum of Values

    Why masking? We're building a language model that predicts the NEXT token.
    If it could see future tokens during training, it would just cheat.
    """
    def __init__(self, head_size: int):
        super().__init__()
        self.key   = nn.Linear(N_EMBD, head_size, bias=False)
        self.query = nn.Linear(N_EMBD, head_size, bias=False)
        self.value = nn.Linear(N_EMBD, head_size, bias=False)
        self.dropout = nn.Dropout(DROPOUT)

        # Causal mask: lower triangular matrix of ones
        # tril[i][j] = 1 means position i CAN attend to position j
        # Positions can only attend to themselves and earlier positions
        self.register_buffer(
            "tril",
            torch.tril(torch.ones(BLOCK_SIZE, BLOCK_SIZE))
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, T, C = x.shape  # Batch, Time (seq length), Channels (embed dim)
        head_size = self.key.out_features

        k = self.key(x)    # (B, T, head_size)
        q = self.query(x)  # (B, T, head_size)
        v = self.value(x)  # (B, T, head_size)

        # Compute attention scores: Q · K^T scaled by 1/sqrt(head_size)
        # Scaling prevents dot products from getting too large → unstable softmax
        scores = q @ k.transpose(-2, -1) * (head_size ** -0.5)  # (B, T, T)

        # Apply causal mask — fill future positions with -inf so softmax → 0
        scores = scores.masked_fill(self.tril[:T, :T] == 0, float("-inf"))

        # Softmax → attention weights (sum to 1 across the T dimension)
        weights = F.softmax(scores, dim=-1)   # (B, T, T)
        weights = self.dropout(weights)

        # Weighted sum of values
        out = weights @ v  # (B, T, head_size)
        return out


# ── Component 2: Multi-Head Attention ───────────────────────────────
class MultiHeadAttention(nn.Module):
    """
    Run N_HEAD attention heads in parallel, then concatenate and project.

    Why multiple heads? Each head can specialize in different relationships:
    - Head 1 might learn grammar (subject-verb agreement)
    - Head 2 might learn proximity (nearby words)
    - Head 3 might learn semantics (related concepts)
    In Urdu, some heads might learn morphological patterns specific to Nastaliq.
    """
    def __init__(self, num_heads: int, head_size: int):
        super().__init__()
        self.heads = nn.ModuleList([Head(head_size) for _ in range(num_heads)])
        self.proj  = nn.Linear(N_EMBD, N_EMBD)   # project concatenated heads back to N_EMBD
        self.dropout = nn.Dropout(DROPOUT)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Run all heads in parallel, concatenate along last dimension
        out = torch.cat([h(x) for h in self.heads], dim=-1)  # (B, T, N_EMBD)
        out = self.dropout(self.proj(out))
        return out


# ── Component 3: Feed-Forward Network ───────────────────────────────
class FeedForward(nn.Module):
    """
    Two linear layers with a ReLU in between.

    After attention gathers context from across the sequence,
    the FFN lets each token process that context independently.
    The expansion to 4×N_EMBD gives the model more capacity to transform.
    """
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(N_EMBD, 4 * N_EMBD),   # expand
            nn.ReLU(),
            nn.Linear(4 * N_EMBD, N_EMBD),   # contract
            nn.Dropout(DROPOUT),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


# ── Component 4: Transformer Block ──────────────────────────────────
class Block(nn.Module):
    """
    One full transformer block = attention + feed-forward, both with residuals.

    Residual connection: output = x + sublayer(LayerNorm(x))
    This means the GRADIENT always has a direct path back through the +x term,
    preventing vanishing gradients in deep networks.

    LayerNorm before each sublayer (Pre-LN) stabilizes training.
    """
    def __init__(self):
        super().__init__()
        head_size = N_EMBD // N_HEAD         # 384 // 6 = 64 per head
        self.attention = MultiHeadAttention(N_HEAD, head_size)
        self.ffn       = FeedForward()
        self.ln1       = nn.LayerNorm(N_EMBD)
        self.ln2       = nn.LayerNorm(N_EMBD)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.attention(self.ln1(x))   # attention with residual
        x = x + self.ffn(self.ln2(x))         # FFN with residual
        return x


# ── Component 5: Full Urdu GPT Model ────────────────────────────────
class UrduGPT(nn.Module):
    """
    The complete language model.

    Input:  integer token IDs  shape (B, T)
    Output: logits over vocab  shape (B, T, vocab_size)

    At inference: sample from softmax(logits) to pick the next character.
    At training:  compute cross-entropy loss between logits and targets.
    """
    def __init__(self):
        super().__init__()
        # Token embedding: each of 327 chars → 384-dim vector
        self.token_embedding = nn.Embedding(VOCAB_SIZE, N_EMBD)
        # Position embedding: each of 256 positions → 384-dim vector
        self.position_embedding = nn.Embedding(BLOCK_SIZE, N_EMBD)
        # Stack of transformer blocks
        self.blocks = nn.Sequential(*[Block() for _ in range(N_LAYER)])
        # Final layer norm
        self.ln_final = nn.LayerNorm(N_EMBD)
        # Language model head: project from N_EMBD → VOCAB_SIZE (logits over chars)
        self.lm_head = nn.Linear(N_EMBD, VOCAB_SIZE)

    def forward(self, idx: torch.Tensor, targets: torch.Tensor = None):
        B, T = idx.shape

        # Token + position embeddings
        tok_emb = self.token_embedding(idx)                              # (B, T, N_EMBD)
        pos_emb = self.position_embedding(torch.arange(T, device=DEVICE))  # (T, N_EMBD)
        x = tok_emb + pos_emb                                           # (B, T, N_EMBD)

        # Pass through transformer blocks
        x = self.blocks(x)       # (B, T, N_EMBD)
        x = self.ln_final(x)     # (B, T, N_EMBD)
        logits = self.lm_head(x) # (B, T, VOCAB_SIZE)

        # Compute loss if targets provided (training mode)
        loss = None
        if targets is not None:
            B, T, V = logits.shape
            loss = F.cross_entropy(logits.view(B*T, V), targets.view(B*T))

        return logits, loss

    @torch.no_grad()
    def generate(self, idx: torch.Tensor, max_new_tokens: int) -> torch.Tensor:
        """
        Autoregressive generation: given a seed sequence, generate max_new_tokens chars.
        This is how the model actually produces text after training.
        """
        for _ in range(max_new_tokens):
            # Crop to block_size (context window limit)
            idx_cond = idx[:, -BLOCK_SIZE:]
            # Forward pass
            logits, _ = self(idx_cond)
            # Take logits at the last position only
            logits = logits[:, -1, :]                # (B, VOCAB_SIZE)
            # Sample from distribution
            probs = F.softmax(logits, dim=-1)        # (B, VOCAB_SIZE)
            idx_next = torch.multinomial(probs, num_samples=1)  # (B, 1)
            # Append to sequence
            idx = torch.cat([idx, idx_next], dim=1)  # (B, T+1)
        return idx

    def count_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters())


if __name__ == "__main__":
    print(f"Device: {DEVICE}")
    print(f"\nModel config:")
    print(f"  vocab_size  = {VOCAB_SIZE}")
    print(f"  block_size  = {BLOCK_SIZE}")
    print(f"  n_embd      = {N_EMBD}")
    print(f"  n_head      = {N_HEAD}")
    print(f"  n_layer     = {N_LAYER}")

    # Instantiate model
    model = UrduGPT().to(DEVICE)
    params = model.count_parameters()
    print(f"\nTotal parameters: {params:,}  ({params/1e6:.1f}M)")
    print(f"  (GPT-2 Small = 117M, GPT-2 Large = 762M, GPT-4 ≈ 1.8T)")

    # Test forward pass with dummy data
    dummy_x = torch.zeros((2, 10), dtype=torch.long, device=DEVICE)
    dummy_y = torch.zeros((2, 10), dtype=torch.long, device=DEVICE)
    logits, loss = model(dummy_x, dummy_y)
    print(f"\nForward pass test:")
    print(f"  Input shape:  {dummy_x.shape}")
    print(f"  Logits shape: {logits.shape}  (batch=2, seq=10, vocab={VOCAB_SIZE})")
    print(f"  Initial loss: {loss.item():.4f}  (random init ≈ ln({VOCAB_SIZE}) = {math.log(VOCAB_SIZE):.4f})")
    print(f"\n✅ Model architecture complete. Next: train.py — the training loop")
