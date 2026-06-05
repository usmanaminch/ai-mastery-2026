"""
ingest/extract_metrics.py — Extract structured metrics from model cards

Reads model_card documents from the database and uses Claude to extract:
model name, context window, pricing, strengths, safety approach, etc.

Stores results in model_metrics table.
Run after ingesting new model cards: python3 ingest/extract_metrics.py
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import anthropic
from sqlalchemy import text
from db.connection import get_engine
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

EXTRACT_PROMPT = """Extract structured information from this AI model documentation.
Return ONLY valid JSON, no preamble:

{{
  "model_name": "exact model name (e.g. Claude 3.5 Sonnet, GPT-4o, Gemini 1.5 Pro)",
  "creator": "company name",
  "context_window": "context window size (e.g. 200K tokens, 1M tokens, unknown)",
  "price_input": "input price per 1M tokens (e.g. $3.00, unknown)",
  "price_output": "output price per 1M tokens (e.g. $15.00, unknown)",
  "speed_notes": "brief speed/latency note if mentioned",
  "key_strengths": ["strength 1", "strength 2", "strength 3"],
  "safety_approach": "1-2 sentence summary of safety approach",
  "open_source": true or false,
  "country": "country of origin (US, China, France, UK, etc.)",
  "release_date": "approximate release date if mentioned, else unknown"
}}

Document:
{content}"""


def extract_metrics_for_document(doc_id: str, title: str, content: str) -> dict:
    try:
        resp = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=800,
            messages=[{
                "role": "user",
                "content": EXTRACT_PROMPT.format(content=content[:4000])
            }]
        )
        raw = resp.content[0].text.strip()
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:-1])
        return json.loads(raw)
    except Exception as e:
        print(f"  ⚠️ Extraction failed for {title[:40]}: {e}")
        return None


def run():
    engine = get_engine()

    # Get all model_card documents not yet extracted
    with engine.connect() as conn:
        docs = conn.execute(text("""
            SELECT d.id::text, d.title, d.content, d.entity_name
            FROM documents d
            LEFT JOIN model_metrics m ON d.id = m.source_doc_id
            WHERE d.source_type = 'model_card'
              AND m.id IS NULL
            ORDER BY d.ingested_at
        """)).fetchall()

    print(f"Found {len(docs)} model card documents to extract metrics from\n")

    for doc_id, title, content, entity in docs:
        print(f"Extracting: {title[:60]}")
        metrics = extract_metrics_for_document(doc_id, title, content or "")

        if not metrics:
            continue

        # Ensure creator is set
        if not metrics.get("creator"):
            metrics["creator"] = entity

        try:
            with engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO model_metrics
                        (model_name, creator, context_window, price_input,
                         price_output, speed_notes, key_strengths, safety_approach,
                         open_source, country, release_date, source_doc_id)
                    VALUES
                        (:model_name, :creator, :context_window, :price_input,
                         :price_output, :speed_notes, :key_strengths, :safety_approach,
                         :open_source, :country, :release_date, CAST(:source_doc_id AS UUID))
                    ON CONFLICT (model_name, creator) DO UPDATE SET
                        context_window = EXCLUDED.context_window,
                        price_input = EXCLUDED.price_input,
                        extracted_at = NOW()
                """), {
                    "model_name": metrics.get("model_name", title[:80]),
                    "creator": metrics.get("creator", entity),
                    "context_window": metrics.get("context_window", ""),
                    "price_input": metrics.get("price_input", ""),
                    "price_output": metrics.get("price_output", ""),
                    "speed_notes": metrics.get("speed_notes", ""),
                    "key_strengths": metrics.get("key_strengths", []),
                    "safety_approach": metrics.get("safety_approach", ""),
                    "open_source": metrics.get("open_source", False),
                    "country": metrics.get("country", ""),
                    "release_date": metrics.get("release_date", ""),
                    "source_doc_id": doc_id,
                })
                conn.commit()
            print(f"  ✅ {metrics.get('model_name', '?')} by {metrics.get('creator', '?')}")
        except Exception as e:
            print(f"  ❌ DB error: {e}")

    print("\nDone. Run the app to see the comparison table.")

if __name__ == "__main__":
    run()
