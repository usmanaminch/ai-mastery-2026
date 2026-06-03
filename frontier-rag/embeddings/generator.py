"""
embeddings/generator.py — Vertex AI text-embedding-004

Uses the google-genai SDK (the replacement for the deprecated
vertexai.language_models API which is removed June 24, 2026).

Converts text into 768-dimensional vectors. Similar meanings
produce vectors close together in 768-dimensional space.

Two task types:
- RETRIEVAL_DOCUMENT : embed chunks going into the database
- RETRIEVAL_QUERY    : embed the user's question at search time

Why different types? The model is fine-tuned so that query vectors
and document vectors are compatible — "what is prompt injection?"
will land close to chunks that explain prompt injection, even
though the phrasing is completely different.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

GCP_PROJECT = os.getenv("GCP_PROJECT", "frontier-rag")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-east4")
EMBEDDING_MODEL = "text-embedding-004"
EMBEDDING_DIMS = 768

_client = None


def get_client():
    """Lazy-initialize the Vertex AI genai client."""
    global _client
    if _client is None:
        _client = genai.Client(
            vertexai=True,
            project=GCP_PROJECT,
            location=GCP_LOCATION,
        )
    return _client


def embed_texts(
    texts: list,
    task_type: str = "RETRIEVAL_DOCUMENT",
    batch_size: int = 20,
) -> list:
    """
    Embed a list of texts. Returns a list of 768-float vectors.

    Batches automatically — Vertex AI allows up to 250 per call
    but 20 is safe for rate limits.

    task_type:
    - "RETRIEVAL_DOCUMENT" : for chunks being stored (ingestion)
    - "RETRIEVAL_QUERY"    : for user queries at search time
    - "SEMANTIC_SIMILARITY": for comparing two pieces of text
    """
    client = get_client()
    all_vectors = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        result = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=batch,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=EMBEDDING_DIMS,
            ),
        )
        all_vectors.extend([e.values for e in result.embeddings])

    return all_vectors


def embed_query(query: str) -> list:
    """Embed a single user query for retrieval."""
    return embed_texts([query], task_type="RETRIEVAL_QUERY")[0]


def embed_document(text: str) -> list:
    """Embed a single document chunk for storage."""
    return embed_texts([text], task_type="RETRIEVAL_DOCUMENT")[0]
