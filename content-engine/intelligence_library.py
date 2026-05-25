import json
import os
from datetime import datetime

LIBRARY_FILE = "intelligence_library.json"

def load_library() -> dict:
    """Load the intelligence library from disk"""
    if os.path.exists(LIBRARY_FILE):
        with open(LIBRARY_FILE, 'r') as f:
            return json.load(f)
    return {
        "records": [],
        "metadata": {
            "created": datetime.now().isoformat(),
            "total_records": 0,
            "last_updated": datetime.now().isoformat()
        }
    }

def save_library(library: dict):
    """Save the intelligence library to disk"""
    library["metadata"]["last_updated"] = datetime.now().isoformat()
    library["metadata"]["total_records"] = len(library["records"])
    with open(LIBRARY_FILE, 'w') as f:
        json.dump(library, f, indent=2)

def url_exists(url: str) -> bool:
    """Check if a URL already exists in the library"""
    library = load_library()
    return any(r["source_url"] == url for r in library["records"])

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
    """Add a new record to the intelligence library"""
    library = load_library()

    # Duplicate check
    if not allow_duplicate:
        existing = [r for r in library["records"] if r["source_url"] == source_url]
        if existing:
            return existing[0]  # Return existing record instead of adding duplicate

    record_id = f"{len(library['records']) + 1:04d}"

    record = {
        "id": record_id,
        "date_found": datetime.now().isoformat(),
        "source_url": source_url,
        "source_name": source_name,
        "author": author,
        "title": title,
        "synthesis": synthesis,
        "key_quotes": key_quotes,
        "content_angle": content_angle,
        "tier": tier,
        "themes": themes,
        "status": "synthesized",
        "used_in": [],
        "raw_content": raw_content[:2000] if raw_content else ""
    }

    library["records"].append(record)
    save_library(library)
    return record

def get_records_by_status(status: str) -> list:
    library = load_library()
    return [r for r in library["records"] if r["status"] == status]

def get_records_by_theme(theme: str) -> list:
    library = load_library()
    return [r for r in library["records"]
            if any(theme.lower() in t.lower() for t in r["themes"])]

def update_record_status(record_id: str, status: str, used_in: str = None):
    library = load_library()
    for record in library["records"]:
        if record["id"] == record_id:
            record["status"] = status
            if used_in:
                record["used_in"].append(used_in)
            break
    save_library(library)

def get_library_stats() -> dict:
    library = load_library()
    records = library["records"]
    return {
        "total": len(records),
        "synthesized": len([r for r in records if r["status"] == "synthesized"]),
        "drafting": len([r for r in records if r["status"] == "drafting"]),
        "published": len([r for r in records if r["status"] == "published"]),
        "tier1": len([r for r in records if r["tier"] == 1]),
        "tier2": len([r for r in records if r["tier"] == 2]),
        "tier3": len([r for r in records if r["tier"] == 3]),
        "themes": list(set(t for r in records for t in r["themes"]))
    }

def search_library(query: str) -> list:
    library = load_library()
    query_lower = query.lower()
    results = []
    for record in library["records"]:
        if (query_lower in record["title"].lower() or
            query_lower in record["synthesis"].lower() or
            any(query_lower in t.lower() for t in record["themes"])):
            results.append(record)
    return results

if __name__ == "__main__":
    stats = get_library_stats()
    print(f"Library stats: {stats}")
    print(f"Duplicate check test: {url_exists('https://example.com')}")
