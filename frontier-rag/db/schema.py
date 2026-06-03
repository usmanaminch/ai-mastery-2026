"""
Database schema for Frontier AI Intelligence RAG.

Three tables:
- documents : raw ingested content (one row per article/paper/page)
- chunks    : documents split into pieces for retrieval + embedding
- queries   : claude-zt audit trail — every query logged with agent identity

Why split documents into chunks?
Embedding models have a token limit (~8k tokens). Long papers need to be
split into overlapping chunks so we can embed and retrieve specific sections.
An embedding represents the MEANING of text as a vector of numbers.
Similar meanings = vectors that are close together in space.
"""

import sqlalchemy
from sqlalchemy import text
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.connection import get_engine

SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS documents (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_url     TEXT UNIQUE,
    source_type    TEXT NOT NULL,
    title          TEXT,
    content        TEXT,
    entity_name    TEXT,
    entity_type    TEXT,
    published_date DATE,
    ingested_at    TIMESTAMP DEFAULT NOW(),
    metadata       JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS chunks (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content     TEXT NOT NULL,
    embedding   vector(1536),
    token_count INTEGER,
    metadata    JSONB DEFAULT '{}'::jsonb,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS queries (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id         TEXT NOT NULL,
    agent_role       TEXT NOT NULL,
    query_text       TEXT NOT NULL,
    mode             TEXT DEFAULT 'standard',
    chunks_retrieved INTEGER,
    response_text    TEXT,
    latency_ms       INTEGER,
    created_at       TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS chunks_document_idx
    ON chunks (document_id);

CREATE INDEX IF NOT EXISTS documents_entity_idx
    ON documents (entity_name, entity_type);

CREATE INDEX IF NOT EXISTS documents_source_type_idx
    ON documents (source_type);

CREATE INDEX IF NOT EXISTS queries_agent_idx
    ON queries (agent_id, created_at);
"""

def create_schema():
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text(SCHEMA_SQL))
        conn.commit()
    print("Schema created successfully")
    print("Tables: documents, chunks, queries")

def verify_schema():
    engine = get_engine()
    with engine.connect() as conn:
        tables = conn.execute(text("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)).fetchall()
        ext = conn.execute(text("""
            SELECT extname, extversion FROM pg_extension
            WHERE extname = 'vector'
        """)).fetchone()
    print(f"pgvector: {ext[0]} v{ext[1]}")
    print(f"Tables: {[t[0] for t in tables]}")

if __name__ == "__main__":
    create_schema()
    verify_schema()
