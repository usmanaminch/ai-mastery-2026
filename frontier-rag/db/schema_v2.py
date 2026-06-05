"""
db/schema_v2.py — Add model_metrics and watch_sources tables

Run this once to extend the existing schema.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.connection import get_engine
from sqlalchemy import text

V2_SQL = """
-- Model metrics: structured data extracted from model cards
CREATE TABLE IF NOT EXISTS model_metrics (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name      TEXT NOT NULL,
    creator         TEXT NOT NULL,
    context_window  TEXT,
    price_input     TEXT,   -- e.g. "$3.00 / 1M tokens"
    price_output    TEXT,
    speed_notes     TEXT,   -- qualitative: "fast", "slow for reasoning"
    key_strengths   TEXT[],
    safety_approach TEXT,
    open_source     BOOLEAN DEFAULT FALSE,
    country         TEXT,   -- US, China, France, etc.
    release_date    TEXT,
    source_doc_id   UUID REFERENCES documents(id),
    extracted_at    TIMESTAMP DEFAULT NOW(),
    UNIQUE(model_name, creator)
);

-- Watch sources: URLs to monitor for new content
CREATE TABLE IF NOT EXISTS watch_sources (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url             TEXT UNIQUE NOT NULL,
    entity_name     TEXT NOT NULL,
    source_type     TEXT NOT NULL,
    entity_type     TEXT NOT NULL DEFAULT 'company',
    last_checked    TIMESTAMP,
    last_hash       TEXT,
    check_frequency TEXT DEFAULT 'daily',  -- 'daily', 'weekly'
    auto_ingest     BOOLEAN DEFAULT TRUE,
    added_at        TIMESTAMP DEFAULT NOW()
);

-- Pre-populate watch sources with key feeds
INSERT INTO watch_sources (url, entity_name, source_type, entity_type, check_frequency)
VALUES
    ('https://www.anthropic.com/news',          'Anthropic',         'blog', 'company', 'daily'),
    ('https://www.anthropic.com/research',      'Anthropic',         'blog', 'company', 'daily'),
    ('https://mistral.ai/news/',                'Mistral AI',        'blog', 'company', 'daily'),
    ('https://deepmind.google/discover/blog/',  'Google DeepMind',   'blog', 'company', 'daily'),
    ('https://ai.meta.com/blog/',               'Meta AI',           'blog', 'company', 'weekly'),
    ('https://qwenlm.github.io/',               'Alibaba',           'blog', 'company', 'weekly'),
    ('https://www.deepseek.com/',               'DeepSeek',          'blog', 'company', 'weekly'),
    ('https://www.aisi.gov.uk/work',            'UK AI Safety Institute', 'regulatory', 'regulation', 'weekly'),
    ('https://www.cisa.gov/ai',                 'CISA',              'regulatory', 'regulation', 'weekly')
ON CONFLICT (url) DO NOTHING;
"""

def run():
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text(V2_SQL))
        conn.commit()
    print("✅ Schema v2 applied: model_metrics and watch_sources tables created")
    print("✅ 9 watch sources pre-populated")

if __name__ == "__main__":
    run()
