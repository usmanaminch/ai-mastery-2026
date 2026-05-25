import json
import os
from datetime import datetime
from typing import Optional

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
    raw_content: str = ""
) -> dict:
    """Add a new record to the intelligence library"""
    library = load_library()

    # Generate ID
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
        "status": "synthesized",  # synthesized → drafting → published
        "used_in": [],             # article IDs this fed into
        "raw_content": raw_content[:2000] if raw_content else ""  # store first 2000 chars
    }

    library["records"].append(record)
    save_library(library)
    return record

def get_records_by_status(status: str) -> list:
    """Get all records with a given status"""
    library = load_library()
    return [r for r in library["records"] if r["status"] == status]

def get_records_by_theme(theme: str) -> list:
    """Get all records matching a theme"""
    library = load_library()
    return [r for r in library["records"]
            if any(theme.lower() in t.lower() for t in r["themes"])]

def update_record_status(record_id: str, status: str, used_in: str = None):
    """Update a record's status"""
    library = load_library()
    for record in library["records"]:
        if record["id"] == record_id:
            record["status"] = status
            if used_in:
                record["used_in"].append(used_in)
            break
    save_library(library)

def get_library_stats() -> dict:
    """Get summary statistics"""
    library = load_library()
    records = library["records"]
    return {
        "total": len(records),
        "synthesized": len([r for r in records if r["status"] == "synthesized"]),
        "drafting": len([r for r in records if r["status"] == "drafting"]),
        "published": len([r for r in records if r["status"] == "published"]),
        "tier1": len([r for r in records if r["tier"] == 1]),
        "tier3": len([r for r in records if r["tier"] == 3]),
        "themes": list(set(t for r in records for t in r["themes"]))
    }

def search_library(query: str) -> list:
    """Simple search across titles, synthesis, and themes"""
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
    # Test with a sample record
    record = add_record(
        source_url="https://medium.com/anton-on-security/test",
        source_name="Anton on Security / Medium",
        author="Anton Chuvakin",
        title="Test Article",
        synthesis="This is a test synthesis of the article content.",
        key_quotes=["Quote one from the article"],
        content_angle="Could write about X because of Y",
        tier=1,
        themes=["agentic SOC", "AI security"]
    )
    print(f"Added record: {record['id']}")
    print(f"Library stats: {get_library_stats()}")