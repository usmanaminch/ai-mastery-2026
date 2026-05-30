"""
firebase_library.py — Intelligence Library backed by Google Cloud Firestore

Replaces intelligence_library.py (JSON file) with cloud-persistent storage.
Same function signatures — drop-in replacement, no changes needed in app.py.

🧠 Firestore concepts:
- Collection: like a folder — we use 'intelligence_records'
- Document: like a file — each record is one document
- Fields: the data inside — title, tldr, synthesis, etc.
- No character limits, no row limits, free up to 1GB
"""

import json
import os
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

import firebase_admin
from firebase_admin import credentials, firestore

COLLECTION = "intelligence_records"

# Query params that are tracking junk and don't change the underlying article
TRACKING_PARAMS = {
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'utm_id',
    'fbclid', 'gclid', 'msclkid', 'dclid', 'igshid', 'si',
    'mc_eid', 'mc_cid',
    'linkid', 'rcm', 'ad_id', 'adset_id', 'campaign_id', 'placement',
    'site_source_name', 'aem',
    'e',                    # Google Cloud blog tracking
    'usp',                  # Google sharing tracking
    '_hsenc', '_hsmi',      # HubSpot
    'mkt_tok',              # Marketo
}


def normalize_url(url: str) -> str:
    """
    Canonical form of a URL for deduplication.
    Strips tracking params, trailing slashes, fragments; lowercases scheme/host.

    Example:
      https://cloud.google.com/blog/foo/?utm_source=x&utm_campaign=y#section
      → https://cloud.google.com/blog/foo
    """
    try:
        parsed = urlparse(url.strip())
        params = [
            (k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=False)
            if k.lower() not in TRACKING_PARAMS
        ]
        cleaned_query = urlencode(params)
        return urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip('/'),
            '',                  # params (rare; drop)
            cleaned_query,
            '',                  # fragment
        ))
    except Exception:
        return url


def _get_db():
    """
    Initialize Firebase connection.
    Works both locally (service account JSON) and on Streamlit Cloud (secrets).
    """
    if not firebase_admin._apps:
        try:
            # Try Streamlit secrets first (cloud deployment)
            import streamlit as st
            key_dict = json.loads(st.secrets["FIREBASE_KEY"])
            cred = credentials.Certificate(key_dict)
        except Exception:
            # Fall back to local service account file
            key_path = os.environ.get(
                "FIREBASE_KEY_PATH",
                os.path.join(os.path.dirname(__file__), "firebase-key.json")
            )
            cred = credentials.Certificate(key_path)

        firebase_admin.initialize_app(cred)

    return firestore.client()


def add_record(
    source_url: str,
    source_name: str,
    author: str,
    title: str,
    synthesis: str,
    key_quotes: list,
    content_angle: str,
    tier: int,
    themes: list,
    raw_content: str = "",
    allow_duplicate: bool = False
) -> dict:
    """Add a new intelligence record to Firestore"""
    db = _get_db()
    col = db.collection(COLLECTION)

    normalized = normalize_url(source_url)

    # Duplicate check — match against exact OR normalized URL
    if not allow_duplicate:
        # Exact match
        existing = col.where("source_url", "==", source_url).limit(1).get()
        if list(existing):
            doc = list(existing)[0]
            return {"id": doc.id, **doc.to_dict()}
        # Normalized match (catches URLs that differ only by tracking params)
        existing = col.where("normalized_url", "==", normalized).limit(1).get()
        if list(existing):
            doc = list(existing)[0]
            return {"id": doc.id, **doc.to_dict()}

    # Generate sequential ID
    count = len(list(col.get()))
    record_id = f"{count + 1:04d}"

    record = {
        "id": record_id,
        "date_found": datetime.now().isoformat(),
        "source_url": source_url,
        "normalized_url": normalized,    # NEW — enables smarter dedup
        "source_name": source_name,
        "author": author,
        "title": title,
        "synthesis": synthesis,          # JSON string: {tldr, key_points, why_timely}
        "key_quotes": key_quotes,
        "content_angle": content_angle,  # JSON string: {what_to_write, why_now, ...}
        "tier": tier,
        "themes": themes,
        "status": "synthesized",
        "used_in": [],
        "raw_content": raw_content[:2000] if raw_content else "",
        "draft": "",                     # full article draft stored here
        "linkedin_draft": "",            # LinkedIn post draft
        "pov_notes": ""                  # research chat insights
    }

    col.document(record_id).set(record)
    return record


def url_exists(url: str) -> bool:
    """
    Check if a URL (or its normalized form) already exists in Firestore.
    Catches duplicates that differ only by tracking params or trailing slashes.
    """
    db = _get_db()

    # Exact match
    existing = db.collection(COLLECTION).where(
        "source_url", "==", url
    ).limit(1).get()
    if list(existing):
        return True

    # Normalized match (only catches records with normalized_url stored)
    normalized = normalize_url(url)
    if normalized != url:
        existing = db.collection(COLLECTION).where(
            "normalized_url", "==", normalized
        ).limit(1).get()
        if list(existing):
            return True

    return False


def backfill_normalized_urls() -> int:
    """
    One-time migration: add normalized_url field to existing records that lack it.
    Run via: python firebase_library.py
    Returns number of records updated.
    """
    db = _get_db()
    docs = db.collection(COLLECTION).get()
    updated = 0
    for doc in docs:
        data = doc.to_dict()
        if "normalized_url" not in data and data.get("source_url"):
            normalized = normalize_url(data["source_url"])
            db.collection(COLLECTION).document(doc.id).update({
                "normalized_url": normalized
            })
            updated += 1
            print(f"  Backfilled #{doc.id}: {normalized[:70]}")
    return updated


def load_library() -> dict:
    """Load all records — returns same format as JSON library for compatibility"""
    db = _get_db()
    docs = db.collection(COLLECTION).order_by("date_found").get()
    records = [doc.to_dict() for doc in docs]
    return {
        "records": records,
        "metadata": {
            "total_records": len(records),
            "last_updated": datetime.now().isoformat()
        }
    }


def get_records_by_status(status: str) -> list:
    """Get all records with a given status"""
    db = _get_db()
    docs = db.collection(COLLECTION).where("status", "==", status).get()
    return [doc.to_dict() for doc in docs]


def get_records_by_theme(theme: str) -> list:
    """Get records matching a theme"""
    db = _get_db()
    docs = db.collection(COLLECTION).where(
        "themes", "array_contains", theme
    ).get()
    return [doc.to_dict() for doc in docs]


def update_record_status(record_id: str, status: str, used_in: str = None):
    """Update a record's status"""
    db = _get_db()
    ref = db.collection(COLLECTION).document(record_id)
    update_data = {"status": status}
    if used_in:
        doc = ref.get()
        if doc.exists:
            current = doc.to_dict().get("used_in", [])
            current.append(used_in)
            update_data["used_in"] = current
    ref.update(update_data)


def update_record_draft(record_id: str, draft: str, linkedin_draft: str = "",
                        pov_notes: str = ""):
    """Save draft content back to the record"""
    db = _get_db()
    update_data = {}
    if draft:
        update_data["draft"] = draft
        update_data["status"] = "drafting"
    if linkedin_draft:
        update_data["linkedin_draft"] = linkedin_draft
    if pov_notes:
        update_data["pov_notes"] = pov_notes
    if update_data:
        db.collection(COLLECTION).document(record_id).update(update_data)


def get_library_stats() -> dict:
    """Get summary statistics"""
    library = load_library()
    records = library["records"]
    return {
        "total": len(records),
        "synthesized": len([r for r in records if r.get("status") == "synthesized"]),
        "drafting": len([r for r in records if r.get("status") == "drafting"]),
        "published": len([r for r in records if r.get("status") == "published"]),
        "tier1": len([r for r in records if r.get("tier") == 1]),
        "tier2": len([r for r in records if r.get("tier") == 2]),
        "tier3": len([r for r in records if r.get("tier") == 3]),
        "themes": list(set(t for r in records for t in r.get("themes", [])))
    }


def search_library(query: str) -> list:
    """Search across titles, synthesis, and themes"""
    library = load_library()
    query_lower = query.lower()
    results = []
    for record in library["records"]:
        if (query_lower in record.get("title", "").lower() or
            query_lower in record.get("synthesis", "").lower() or
            any(query_lower in t.lower() for t in record.get("themes", []))):
            results.append(record)
    return results


def migrate_from_json(json_path: str = "intelligence_library.json") -> int:
    """
    One-time migration: move existing JSON records to Firestore.
    Returns number of records migrated.
    """
    if not os.path.exists(json_path):
        print(f"No JSON file found at {json_path}")
        return 0

    with open(json_path, 'r') as f:
        data = json.load(f)

    records = data.get("records", [])
    migrated = 0

    for record in records:
        if not url_exists(record["source_url"]):
            db = _get_db()
            db.collection(COLLECTION).document(record["id"]).set(record)
            migrated += 1
            print(f"  Migrated: #{record['id']} — {record['title'][:50]}")
        else:
            print(f"  Skipped (exists): #{record['id']}")

    print(f"\n✅ Migrated {migrated}/{len(records)} records to Firestore")
    return migrated



def get_pending_paste() -> list:
    """Get URLs that need manual paste — persists across sessions"""
    try:
        db = _get_db()
        docs = db.collection("pending_paste").order_by("added").get()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        import streamlit as st
        st.warning(f"⚠️ Could not load pending paste queue: {e}")
        return []

def add_pending_paste(url: str, row: int):
    """Add a URL to persistent paste queue"""
    db = _get_db()
    doc_id = url.replace("/","_").replace(".","_").replace("?","_")[:100]
    db.collection("pending_paste").document(doc_id).set({
        "url": url,
        "row": row,
        "added": datetime.now().isoformat()
    })

def remove_pending_paste(url: str):
    """Remove URL from paste queue after processing"""
    db = _get_db()
    doc_id = url.replace("/","_").replace(".","_").replace("?","_")[:100]
    db.collection("pending_paste").document(doc_id).delete()

def save_draft(record_id: str, draft_content: str) -> None:
    """Save a draft for a record to Firestore."""
    db = _get_db()
    db.collection("intelligence_records").document(record_id).update({
        "draft": draft_content,
        "status": "draft_saved",
        "draft_saved_at": datetime.now().isoformat()
    })

def delete_draft(record_id: str) -> None:
    """Remove saved draft from a record."""
    db = _get_db()
    db.collection("intelligence_records").document(record_id).update({
        "draft": "",
        "status": "synthesized",
        "draft_saved_at": ""
    })

def save_daily_brief(data: dict) -> None:
    """Save today's daily brief to Firestore."""
    from datetime import date
    db = _get_db()
    data["generated_at"] = datetime.now().isoformat()
    db.collection("daily_briefs").document(date.today().isoformat()).set(data)

def load_daily_brief(date_str: str = None) -> dict:
    """Load a daily brief from Firestore. Defaults to today."""
    from datetime import date
    db = _get_db()
    key = date_str or date.today().isoformat()
    doc = db.collection("daily_briefs").document(key).get()
    return doc.to_dict() if doc.exists else {}

def list_saved_briefs(limit: int = 14) -> list:
    """List the last N saved briefs, most recent first."""
    db = _get_db()
    docs = db.collection("daily_briefs").order_by(
        "generated_at", direction="DESCENDING"
    ).limit(limit).get()
    return [{"id": d.id, **d.to_dict()} for d in docs]


if __name__ == "__main__":
    print("Testing Firebase connection...")
    db = _get_db()
    print("✅ Connected to Firestore")

    stats = get_library_stats()
    print(f"Library stats: {stats}")

    print("\nBackfilling normalized_url on existing records...")
    n = backfill_normalized_urls()
    print(f"Backfilled {n} records")

    print("\nRunning migration from JSON (if file exists)...")
    migrated = migrate_from_json()
    print(f"Migration complete: {migrated} records moved")

    stats = get_library_stats()
    print(f"Updated stats: {stats}")
