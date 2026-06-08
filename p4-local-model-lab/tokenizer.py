"""
tokenizer.py — Character-level tokenizer for Urdu text
=======================================================

What this does:
- Reads the corpus and builds a vocabulary of every unique character
- Creates char→int (encode) and int→char (decode) mappings
- Saves the vocabulary to vocab.json for reproducibility
- Provides encode() and decode() functions the model will use

Why character-level (not word/subword)?
- Urdu morphology is complex — words have many forms
- Character-level sidesteps the tokenization problem entirely
- Every possible Urdu text is representable with our 327-char vocab
- The model learns morphology from scratch — that's the interesting part

Run: python3 tokenizer.py
"""

import json
from pathlib import Path

CORPUS_FILE = Path("data/processed/urdu_corpus.txt")
VOCAB_FILE  = Path("data/processed/vocab.json")


def build_vocabulary(corpus_path: Path) -> dict:
    """Read corpus and extract all unique characters."""
    print(f"Reading corpus: {corpus_path}")
    text = corpus_path.read_text(encoding="utf-8")
    print(f"Corpus size: {len(text):,} characters")

    # Every unique character in the corpus
    chars = sorted(set(text))
    vocab_size = len(chars)
    print(f"Vocabulary size: {vocab_size} unique characters")

    # Build mappings
    char_to_int = {ch: i for i, ch in enumerate(chars)}
    int_to_char = {i: ch for i, ch in enumerate(chars)}

    return {
        "chars": chars,
        "vocab_size": vocab_size,
        "char_to_int": char_to_int,
        "int_to_char": {str(k): v for k, v in int_to_char.items()},  # JSON keys must be strings
    }


def save_vocabulary(vocab: dict, path: Path):
    """Save vocabulary to JSON for reproducibility."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(vocab, f, ensure_ascii=False, indent=2)
    print(f"Vocabulary saved: {path}")


def load_vocabulary(path: Path) -> dict:
    """Load vocabulary from JSON."""
    with open(path, encoding="utf-8") as f:
        vocab = json.load(f)
    vocab["int_to_char"] = {int(k): v for k, v in vocab["int_to_char"].items()}
    return vocab


class UrduTokenizer:
    """
    Character-level tokenizer for Urdu text.

    Usage:
        tokenizer = UrduTokenizer.from_corpus("data/processed/urdu_corpus.txt")
        ids = tokenizer.encode("پاکستان")
        text = tokenizer.decode(ids)
    """

    def __init__(self, vocab: dict):
        self.chars        = vocab["chars"]
        self.vocab_size   = vocab["vocab_size"]
        self.char_to_int  = vocab["char_to_int"]
        self.int_to_char  = vocab["int_to_char"]

    @classmethod
    def from_corpus(cls, corpus_path: Path, vocab_path: Path = VOCAB_FILE):
        """Build tokenizer from corpus file, save vocab, return tokenizer."""
        vocab = build_vocabulary(corpus_path)
        save_vocabulary(vocab, vocab_path)
        return cls(vocab)

    @classmethod
    def from_vocab(cls, vocab_path: Path = VOCAB_FILE):
        """Load tokenizer from saved vocab file."""
        vocab = load_vocabulary(vocab_path)
        return cls(vocab)

    def encode(self, text: str) -> list[int]:
        """Convert text to list of integer token IDs."""
        return [self.char_to_int[ch] for ch in text if ch in self.char_to_int]

    def decode(self, ids: list[int]) -> str:
        """Convert list of integer token IDs back to text."""
        return "".join(self.int_to_char.get(i, "?") for i in ids)

    def __repr__(self):
        return f"UrduTokenizer(vocab_size={self.vocab_size})"


def demo(tokenizer: UrduTokenizer):
    """Show tokenizer working on sample Urdu words."""
    samples = [
        "پاکستان",          # Pakistan
        "زبان",             # language
        "محبت",             # love
        "علم",              # knowledge
        "آسمان",            # sky
    ]

    print("\n── Tokenizer Demo ──────────────────────")
    print(f"{'Word':<15} {'Encoded':<40} {'Decoded'}")
    print("─" * 70)
    for word in samples:
        encoded = tokenizer.encode(word)
        decoded = tokenizer.decode(encoded)
        match = "✓" if decoded == word else "✗"
        print(f"{word:<15} {str(encoded):<40} {decoded} {match}")

    print(f"\nVocab size: {tokenizer.vocab_size}")
    print(f"First 20 chars: {tokenizer.chars[:20]}")
    print(f"Last  20 chars: {tokenizer.chars[-20:]}")


if __name__ == "__main__":
    # Build tokenizer from corpus
    tokenizer = UrduTokenizer.from_corpus(CORPUS_FILE, VOCAB_FILE)

    # Run demo
    demo(tokenizer)

    print("\n✅ Tokenizer ready. vocab.json saved.")
    print("   Next: dataloader.py — batch sequences for training")
