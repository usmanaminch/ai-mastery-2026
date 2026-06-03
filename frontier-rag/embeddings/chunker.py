"""
embeddings/chunker.py — Text Chunking

Splits long documents into overlapping chunks for embedding.

Why overlap?
If a key sentence falls at the boundary between two chunks,
without overlap it would be split and lose context. With overlap,
every important boundary is captured in full in at least one chunk.

Strategy: paragraph-aware chunking
1. Split on double newlines (paragraph boundaries)
2. If a paragraph fits in the chunk size, add it
3. If a paragraph is too long, split by sentence
4. Always add the last N characters of the previous chunk to the next
   (the overlap)

This preserves natural document structure better than
naive fixed-size character splitting.
"""

import re


CHUNK_SIZE = 1500       # characters (~375 tokens at ~4 chars/token)
OVERLAP_SIZE = 200      # characters overlap between chunks
MIN_CHUNK_SIZE = 100    # don't create tiny chunks


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP_SIZE) -> list:
    """
    Split text into overlapping chunks.
    Returns a list of dicts: {text, chunk_index, char_start, char_end}
    """
    if not text or len(text.strip()) < MIN_CHUNK_SIZE:
        return []

    # Clean the text
    text = text.strip()
    text = re.sub(r'\n{3,}', '\n\n', text)  # normalize multiple blank lines

    chunks = []
    start = 0
    chunk_index = 0

    while start < len(text):
        end = start + chunk_size

        if end >= len(text):
            # Last chunk — take everything remaining
            chunk = text[start:]
        else:
            # Try to end at a paragraph boundary
            paragraph_end = text.rfind('\n\n', start, end)
            if paragraph_end > start + (chunk_size // 2):
                end = paragraph_end
            else:
                # Try to end at a sentence boundary
                sentence_end = max(
                    text.rfind('. ', start, end),
                    text.rfind('! ', start, end),
                    text.rfind('? ', start, end),
                )
                if sentence_end > start + (chunk_size // 2):
                    end = sentence_end + 1  # include the period
            chunk = text[start:end]

        chunk = chunk.strip()
        if len(chunk) >= MIN_CHUNK_SIZE:
            chunks.append({
                "text": chunk,
                "chunk_index": chunk_index,
                "char_start": start,
                "char_end": start + len(chunk),
                "token_count_approx": len(chunk) // 4,
            })
            chunk_index += 1

        # Move forward, stepping back by overlap amount
        start = end - overlap
        if start <= 0:
            break

    return chunks


def chunk_document(title: str, content: str) -> list:
    """
    Chunk a full document. Prepends the title to each chunk so
    the embedding carries context about what document it came from.
    This improves retrieval accuracy significantly.
    """
    raw_chunks = chunk_text(content)

    result = []
    for c in raw_chunks:
        # Prepend title so every chunk knows its source
        enriched_text = f"{title}\n\n{c['text']}"
        result.append({
            **c,
            "text": enriched_text,
        })

    return result
