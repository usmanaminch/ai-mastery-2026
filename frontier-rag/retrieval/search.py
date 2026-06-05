"""
retrieval/search.py — Hybrid BM25 + Vector Search

Two searches run in parallel, combined with Reciprocal Rank Fusion (RRF).

Vector search  : semantic similarity via pgvector cosine distance
Full-text search: PostgreSQL ts_vector keyword matching

RRF formula: score = 1 / (k + rank), summed across both result lists
k=60 is the standard constant — dampens the impact of high ranks.

Why hybrid over vector-only?
- Vector search misses exact terminology: "GPT-4o", "RLHF", "Constitutional AI"
- Full-text misses semantic similarity: "alignment" vs "value learning"
- Hybrid captures both: beats either approach alone by 10-15% on most benchmarks
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from db.connection import get_engine
from embeddings.generator import embed_query as get_embedding

RRF_K = 60          # Standard RRF constant
DEFAULT_TOP_K = 8   # Chunks to return per query


def vector_search(query_vector: list, top_k: int = 20, entity_filter: str = None) -> list:
    """
    Find chunks by semantic similarity using pgvector cosine distance.
    Returns list of {chunk_id, content, title, entity_name, score, rank}
    """
    vec_str = "[" + ",".join(str(v) for v in query_vector) + "]"

    entity_clause = ""
    params = {"vec": vec_str, "k": top_k}
    if entity_filter:
        entity_clause = "AND d.entity_name ILIKE :entity"
        params["entity"] = f"%{entity_filter}%"

    sql = f"""
        SELECT
            c.id::text AS chunk_id,
            c.content,
            c.chunk_index,
            d.title,
            d.entity_name,
            d.source_type,
            d.source_url,
            1 - (c.embedding <=> CAST(:vec AS vector)) AS score
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE c.embedding IS NOT NULL
        {entity_clause}
        ORDER BY c.embedding <=> CAST(:vec AS vector)
        LIMIT :k
    """

    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(text(sql), params).fetchall()

    return [
        {
            "chunk_id": r[0],
            "content": r[1],
            "chunk_index": r[2],
            "title": r[3],
            "entity_name": r[4],
            "source_type": r[5],
            "source_url": r[6],
            "vector_score": float(r[7]),
            "vector_rank": i + 1,
        }
        for i, r in enumerate(rows)
    ]


def fulltext_search(query: str, top_k: int = 20, entity_filter: str = None) -> list:
    """
    Find chunks by keyword matching using PostgreSQL full-text search.
    Handles stemming, stop words, and ranking automatically.
    """
    entity_clause = ""
    params = {"query": query, "k": top_k}
    if entity_filter:
        entity_clause = "AND d.entity_name ILIKE :entity"
        params["entity"] = f"%{entity_filter}%"

    sql = f"""
        SELECT
            c.id::text AS chunk_id,
            c.content,
            c.chunk_index,
            d.title,
            d.entity_name,
            d.source_type,
            d.source_url,
            ts_rank(
                to_tsvector('english', c.content),
                plainto_tsquery('english', :query)
            ) AS score
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', :query)
        {entity_clause}
        ORDER BY score DESC
        LIMIT :k
    """

    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(text(sql), params).fetchall()

    return [
        {
            "chunk_id": r[0],
            "content": r[1],
            "chunk_index": r[2],
            "title": r[3],
            "entity_name": r[4],
            "source_type": r[5],
            "source_url": r[6],
            "fts_score": float(r[7]),
            "fts_rank": i + 1,
        }
        for i, r in enumerate(rows)
    ]


def reciprocal_rank_fusion(
    vector_results: list,
    fts_results: list,
    top_k: int = DEFAULT_TOP_K,
    vector_weight: float = 0.6,
    fts_weight: float = 0.4,
    max_per_document: int = 2,
) -> list:
    """
    Combine vector and full-text results using Reciprocal Rank Fusion.

    RRF score = vector_weight * (1/(k + vector_rank))
              + fts_weight   * (1/(k + fts_rank))

    Chunks appearing in both lists score higher.
    max_per_document: limits chunks from any single document.
    Prevents one large document from dominating all result slots.
    """
    scores = {}
    metadata = {}

    for r in vector_results:
        cid = r["chunk_id"]
        scores[cid] = scores.get(cid, 0) + vector_weight * (1 / (RRF_K + r["vector_rank"]))
        metadata[cid] = {**r, "found_by": "vector"}

    for r in fts_results:
        cid = r["chunk_id"]
        scores[cid] = scores.get(cid, 0) + fts_weight * (1 / (RRF_K + r["fts_rank"]))
        if cid in metadata:
            metadata[cid]["found_by"] = "both"
            metadata[cid]["fts_score"] = r["fts_score"]
        else:
            metadata[cid] = {**r, "found_by": "fulltext"}

    # Sort all candidates by RRF score
    all_ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # Apply diversity filter: max N chunks per source document
    results = []
    doc_counts = {}
    for cid, rrf_score in all_ranked:
        doc_title = metadata[cid]["title"]
        doc_counts[doc_title] = doc_counts.get(doc_title, 0) + 1
        if doc_counts[doc_title] > max_per_document:
            continue
        results.append({
            **metadata[cid],
            "rrf_score": round(rrf_score, 6),
            "final_rank": len(results) + 1,
        })
        if len(results) >= top_k:
            break

    return results


def hybrid_search(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    entity_filter: str = None,
    field_ciso_mode: bool = False,
) -> list:
    """
    Main search function. Runs vector + full-text, combines with RRF.

    field_ciso_mode: appends security/procurement context to the query
    before embedding, biasing results toward security implications.
    """
    search_query = query
    if field_ciso_mode:
        search_query = (
            f"{query} "
            "security implications enterprise risk procurement "
            "CISO federal compliance FedRAMP"
        )

    # Embed the query
    query_vector = get_embedding(search_query)

    # Run both searches with wider net (3x top_k), then RRF narrows
    vec_results = vector_search(query_vector, top_k=top_k * 3, entity_filter=entity_filter)
    fts_results = fulltext_search(query, top_k=top_k * 3, entity_filter=entity_filter)

    # Combine
    combined = reciprocal_rank_fusion(vec_results, fts_results, top_k=top_k)

    return combined


def format_context(chunks: list, max_chars: int = 12000) -> str:
    """
    Format retrieved chunks into a context string for Claude.
    Each chunk is labelled with source so Claude can cite accurately.
    """
    parts = []
    total = 0

    for c in chunks:
        header = f"[{c['entity_name']} — {c['title'][:60]}]"
        block = f"{header}\n{c['content']}"
        if total + len(block) > max_chars:
            break
        parts.append(block)
        total += len(block)

    return "\n\n---\n\n".join(parts)
