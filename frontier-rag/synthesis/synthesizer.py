"""
synthesis/synthesizer.py — Claude synthesis layer

Takes retrieved chunks and generates:
- Standard mode: factual synthesis with citations and opinions
- Field CISO mode: same query filtered through security/procurement lens
- Disagreement surfacing: flags when sources conflict

This is what separates a RAG system from a search engine.
Search returns documents. Synthesis returns answers.
"""

import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import anthropic
from dotenv import load_dotenv

from retrieval.search import hybrid_search, format_context
from claude_zt.identity import new_synthesizer
from claude_zt.audit import AuditLogger

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-5"

SYSTEM_STANDARD = """You are the Frontier AI Intelligence system — a knowledge base covering
frontier AI models, companies, safety evaluations, and security implications.

Your corpus includes content from Anthropic, Google DeepMind, Meta, Microsoft, Amazon,
Mistral, DeepSeek, Alibaba, and major AI safety organizations (METR, Apollo Research,
UK AISI, NIST, CISA).

When answering:
- Synthesize across sources — don't just quote, form a view
- Cite your sources inline as [Company/Org]
- Surface disagreements: if sources conflict, say so explicitly
- Be specific — name models, dates, numbers when available
- Lead with the most important insight, not background
- Keep answers focused and direct — no preamble"""

SYSTEM_FIELD_CISO = """You are the Frontier AI Intelligence system in Field CISO Mode.

You are advising a Field CISO at a major cloud provider. Every answer must be filtered
through this lens:
- What are the security implications?
- What does this mean for enterprise procurement decisions?
- What are the compliance and regulatory considerations?
- What should a CISO be monitoring or preparing for?

Cite sources as [Company/Org]. Surface disagreements explicitly.
Be direct — no preamble, lead with the security insight.
Assume the reader has a technical security background."""


def synthesize(
    query: str,
    top_k: int = 8,
    field_ciso_mode: bool = False,
    entity_filter: str = None,
) -> dict:
    """
    Main synthesis function.
    Retrieves relevant chunks then has Claude synthesize an answer.

    Returns: {answer, sources, chunks_used, latency_ms, agent_id}
    """
    agent = new_synthesizer()
    start = time.time()

    # Retrieve
    chunks = hybrid_search(
        query,
        top_k=top_k,
        field_ciso_mode=field_ciso_mode,
        entity_filter=entity_filter,
    )

    if not chunks:
        return {
            "answer": "No relevant documents found for this query. Try adding more sources to the corpus.",
            "sources": [],
            "chunks_used": 0,
            "latency_ms": 0,
            "agent_id": agent.agent_id,
        }

    # Format context
    context = format_context(chunks)

    # Build prompt
    system = SYSTEM_FIELD_CISO if field_ciso_mode else SYSTEM_STANDARD

    user_prompt = f"""Based on the following sources from my knowledge base, answer this question:

QUESTION: {query}

SOURCES:
{context}

Provide a synthesis that:
1. Directly answers the question with a clear position or finding
2. Cites specific sources using [Company/Org] notation
3. Notes any significant disagreements or gaps between sources
4. For Field CISO Mode: leads with the security/procurement implication"""

    # Call Claude
    response = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=system,
        messages=[{"role": "user", "content": user_prompt}]
    )

    answer = response.content[0].text
    latency_ms = int((time.time() - start) * 1000)

    # Extract unique sources
    sources = []
    seen = set()
    for c in chunks:
        key = c["title"]
        if key not in seen:
            sources.append({
                "title": c["title"],
                "entity": c["entity_name"],
                "url": c.get("source_url", ""),
                "source_type": c.get("source_type", ""),
            })
            seen.add(key)

    # Log to audit trail
    with AuditLogger(agent) as logger:
        logger.log(
            query_text=query,
            mode="field_ciso" if field_ciso_mode else "standard",
            chunks_retrieved=len(chunks),
            response_text=answer[:5000],
        )

    return {
        "answer": answer,
        "sources": sources,
        "chunks_used": len(chunks),
        "latency_ms": latency_ms,
        "agent_id": agent.agent_id,
    }


def find_disagreements(query: str, top_k: int = 10) -> dict:
    """
    Explicitly searches for conflicting perspectives on a topic.
    Useful for: 'Where do sources disagree on X?'
    """
    agent = new_synthesizer()
    start = time.time()

    chunks = hybrid_search(query, top_k=top_k)
    if not chunks:
        return {"answer": "No sources found.", "sources": [], "latency_ms": 0}

    context = format_context(chunks)

    response = client.messages.create(
        model=MODEL,
        max_tokens=1200,
        system=SYSTEM_STANDARD,
        messages=[{"role": "user", "content": f"""Analyze these sources for DISAGREEMENTS and TENSIONS on this topic:

TOPIC: {query}

SOURCES:
{context}

Identify:
1. Points where sources explicitly contradict each other
2. Differences in emphasis or priority across organizations
3. Gaps — important aspects one org addresses that others ignore
4. Evolution — has the position shifted over time?

Be specific. Name the organizations and what they each say."""}]
    )

    answer = response.content[0].text
    latency_ms = int((time.time() - start) * 1000)

    sources = list({c["entity_name"] for c in chunks})

    with AuditLogger(agent) as logger:
        logger.log(
            query_text=f"[DISAGREEMENT] {query}",
            mode="disagreement",
            chunks_retrieved=len(chunks),
            response_text=answer[:5000],
        )

    return {
        "answer": answer,
        "sources": sources,
        "chunks_used": len(chunks),
        "latency_ms": latency_ms,
    }
