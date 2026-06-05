"""
ingest/watcher.py — Auto-watcher for content changes

Checks watch_sources table for URLs with changed content.
Only re-ingests when content hash changes — no wasted API calls.

Usage:
  python3 ingest/watcher.py           # check all due sources
  python3 ingest/watcher.py --force   # re-check all regardless of schedule
"""

import sys, os, hashlib, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from sqlalchemy import text
from db.connection import get_engine
from ingest.pipeline import ingest_url

def refresh_leaderboard():
    """Also refresh the model leaderboard when watcher runs."""
    try:
        from ingest.scrape_leaderboard import run as lb_run
        print("\nRefreshing model leaderboard...")
        lb_run()
    except Exception as e:
        print(f"  ⚠️ Leaderboard refresh failed: {e}")
from dotenv import load_dotenv

load_dotenv()

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; FrontierRAG/1.0; research bot)"}


def content_hash(url: str) -> tuple:
    """Fetch URL and return (hash, char_count). Returns (None, 0) on failure."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = soup.get_text()[:8000]  # hash first 8k chars
        return hashlib.sha256(text.encode()).hexdigest(), len(text)
    except Exception as e:
        return None, 0


def is_due(last_checked, frequency: str) -> bool:
    """Check if a source is due for re-checking based on frequency."""
    if not last_checked:
        return True
    delta = {"daily": timedelta(days=1), "weekly": timedelta(days=7)}
    return datetime.utcnow() - last_checked > delta.get(frequency, timedelta(days=1))


def run(force: bool = False):
    engine = get_engine()

    with engine.connect() as conn:
        sources = conn.execute(text("""
            SELECT id::text, url, entity_name, source_type, entity_type,
                   last_checked, last_hash, check_frequency, auto_ingest
            FROM watch_sources
            ORDER BY last_checked NULLS FIRST
        """)).fetchall()

    print(f"Checking {len(sources)} watch sources...\n")

    ingested, skipped, changed, errors = 0, 0, 0, 0

    for s in sources:
        sid, url, entity, stype, etype, last_checked, last_hash, freq, auto_ingest = s

        if not force and not is_due(last_checked, freq):
            print(f"⏭️  {entity:<20} {url[:50]} (not due)")
            skipped += 1
            continue

        print(f"🔍 {entity:<20} {url[:50]}")
        new_hash, char_count = content_hash(url)

        if not new_hash:
            print(f"   ❌ Failed to fetch")
            errors += 1
            continue

        # Update check timestamp
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE watch_sources
                SET last_checked = NOW(), last_hash = :hash
                WHERE id = CAST(:id AS UUID)
            """), {"hash": new_hash, "id": sid})
            conn.commit()

        if new_hash == last_hash:
            print(f"   ✓ No change ({char_count} chars)")
            skipped += 1
            continue

        changed += 1
        print(f"   🆕 Content changed! ({char_count} chars)")

        if auto_ingest:
            result = ingest_url(
                url=url,
                source_type=stype,
                entity_name=entity,
                entity_type=etype,
                force=True,  # re-ingest even if URL exists
            )
            if result["status"] == "success":
                ingested += 1
                print(f"   ✅ Re-ingested: {result.get('chunks', 0)} chunks")
            else:
                print(f"   ❌ Ingest failed: {result.get('error', '')}")

    print(f"\n── Watch summary ──")
    print(f"Changed & ingested: {ingested}")
    print(f"Unchanged / skipped: {skipped}")
    print(f"Errors: {errors}")

    # Always refresh leaderboard on watcher run
    refresh_leaderboard()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Check all sources regardless of schedule")
    args = parser.parse_args()
    run(force=args.force)
