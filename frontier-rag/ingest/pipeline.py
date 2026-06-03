"""
ingest/pipeline.py — Document Ingestion Pipeline

The main flow:
  URL → fetch HTML → clean to plain text → chunk → embed → store

Each ingested document becomes:
  1 row in documents (the raw content + metadata)
  N rows in chunks   (split + embedded pieces, ready for retrieval)

The ingester identity (claude-zt) is logged for every document,
so the audit trail shows which agent ingested what and when.
"""

import os
import sys
import json
import hashlib
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from bs4 import BeautifulSoup
from sqlalchemy import text
from dotenv import load_dotenv

from db.connection import get_engine
from embeddings.chunker import chunk_document
from embeddings.generator import embed_texts
from claude_zt.identity import new_ingester
from claude_zt.audit import AuditLogger

load_dotenv()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; FrontierRAG/1.0; research bot)"
}


# ── HTML cleaning ──────────────────────────────────────────────────

def fetch_and_clean(url: str) -> dict:
    """
    Fetch a URL and extract clean plain text.
    Returns: {title, text, status_code, error}
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        return {"title": "", "text": "", "error": str(e)}

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove noise elements
    for tag in soup(["script", "style", "nav", "footer", "header",
                     "aside", "form", "iframe", "noscript"]):
        tag.decompose()

    # Extract title
    title = ""
    if soup.title:
        title = soup.title.get_text(strip=True)
    elif soup.find("h1"):
        title = soup.find("h1").get_text(strip=True)

    # Extract body text
    # Prefer main content areas over full body
    main = (
        soup.find("main") or
        soup.find("article") or
        soup.find(id="content") or
        soup.find(class_="content") or
        soup.body
    )

    if not main:
        return {"title": title, "text": "", "error": "No content found"}

    # Get text with newlines between block elements
    lines = []
    for elem in main.find_all(["p", "h1", "h2", "h3", "h4", "li", "td", "blockquote"]):
        t = elem.get_text(strip=True)
        if t and len(t) > 20:  # skip very short fragments
            lines.append(t)

    text = "\n\n".join(lines)
    return {"title": title, "text": text, "error": None}


# ── Database storage ───────────────────────────────────────────────

def document_exists(url: str) -> bool:
    """Check if a URL has already been ingested."""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id FROM documents WHERE source_url = :url"),
            {"url": url}
        ).fetchone()
    return result is not None


def store_document(
    url: str,
    title: str,
    content: str,
    source_type: str,
    entity_name: str,
    entity_type: str,
    published_date=None,
    metadata: dict = None,
) -> str:
    """
    Store a document and its embedded chunks.
    Returns the document UUID.
    """
    engine = get_engine()

    with engine.connect() as conn:
        # Insert document
        result = conn.execute(text("""
            INSERT INTO documents
                (source_url, source_type, title, content,
                 entity_name, entity_type, published_date, metadata)
            VALUES
                (:url, :source_type, :title, :content,
                 :entity_name, :entity_type, :published_date, CAST(:metadata AS JSONB))
            ON CONFLICT (source_url) DO UPDATE
                SET title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    ingested_at = NOW()
            RETURNING id
        """), {
            "url": url,
            "source_type": source_type,
            "title": title,
            "content": content,
            "entity_name": entity_name,
            "entity_type": entity_type,
            "published_date": published_date,
            "metadata": json.dumps(metadata or {}),
        })
        doc_id = str(result.fetchone()[0])
        conn.commit()

    return doc_id


def store_chunks(doc_id: str, chunks: list, vectors: list):
    """Store chunks with their embeddings."""
    engine = get_engine()

    with engine.connect() as conn:
        # Remove old chunks for this document (re-ingestion)
        conn.execute(
            text("DELETE FROM chunks WHERE document_id = :id"),
            {"id": doc_id}
        )

        for chunk, vector in zip(chunks, vectors):
            # pgvector expects the vector as a string like '[0.1, 0.2, ...]'
            vec_str = "[" + ",".join(str(v) for v in vector) + "]"
            conn.execute(text("""
                INSERT INTO chunks
                    (document_id, chunk_index, content, embedding, token_count)
                VALUES
                    (:doc_id, :chunk_index, :content, CAST(:embedding AS vector), :token_count)
            """), {
                "doc_id": doc_id,
                "chunk_index": chunk["chunk_index"],
                "content": chunk["text"],
                "embedding": vec_str,
                "token_count": chunk.get("token_count_approx", 0),
            })

        conn.commit()


# ── Main ingestion function ────────────────────────────────────────

def ingest_url(
    url: str,
    source_type: str,
    entity_name: str,
    entity_type: str,
    published_date=None,
    metadata: dict = None,
    force: bool = False,
) -> dict:
    """
    Full pipeline: URL → clean → chunk → embed → store.

    Returns a result dict with status and stats.
    source_type: 'model_card', 'safety_eval', 'blog', 'benchmark', 'regulatory', 'zt_framework'
    entity_type: 'company', 'model', 'evaluation', 'regulation'
    """
    agent = new_ingester()
    start = time.time()

    print(f"{agent} Ingesting: {url}")

    # Skip if already ingested (unless forced)
    if not force and document_exists(url):
        print(f"  ↳ Already ingested — skipping")
        return {"status": "skipped", "url": url}

    # Fetch and clean
    print(f"  ↳ Fetching...")
    fetched = fetch_and_clean(url)
    if fetched["error"] or not fetched["text"]:
        print(f"  ↳ Failed: {fetched['error']}")
        return {"status": "error", "url": url, "error": fetched["error"]}

    title = fetched["title"] or url
    content = fetched["text"]
    print(f"  ↳ Got {len(content)} chars: '{title[:60]}'")

    # Chunk
    chunks = chunk_document(title, content)
    if not chunks:
        return {"status": "error", "url": url, "error": "No chunks produced"}
    print(f"  ↳ {len(chunks)} chunks")

    # Embed
    print(f"  ↳ Embedding...")
    texts = [c["text"] for c in chunks]
    vectors = embed_texts(texts, task_type="RETRIEVAL_DOCUMENT")

    # Store
    doc_id = store_document(
        url=url,
        title=title,
        content=content,
        source_type=source_type,
        entity_name=entity_name,
        entity_type=entity_type,
        published_date=published_date,
        metadata=metadata or {},
    )
    store_chunks(doc_id, chunks, vectors)

    elapsed = round(time.time() - start, 1)
    print(f"  ↳ Done in {elapsed}s — doc_id: {doc_id[:8]}...")

    return {
        "status": "success",
        "url": url,
        "doc_id": doc_id,
        "title": title,
        "chunks": len(chunks),
        "elapsed_s": elapsed,
    }


def ingest_batch(documents: list) -> list:
    """
    Ingest a list of document dicts.
    Each dict: {url, source_type, entity_name, entity_type, ...optional}
    """
    results = []
    for i, doc in enumerate(documents):
        print(f"\n[{i+1}/{len(documents)}]")
        result = ingest_url(**doc)
        results.append(result)
        # Small delay between requests to be polite to servers
        if i < len(documents) - 1:
            time.sleep(1)

    success = sum(1 for r in results if r["status"] == "success")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    errors = sum(1 for r in results if r["status"] == "error")
    print(f"\nBatch complete: {success} ingested, {skipped} skipped, {errors} errors")
    return results
