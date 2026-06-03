#!/usr/bin/env python3
"""
reclassify_tiers.py — Re-evaluate tier for all records using stored synthesis.
Run from the content-engine/ directory: python reclassify_tiers.py
"""

import json
import anthropic
from firebase_library import _get_db, COLLECTION

TIER_PROMPT = """Classify this article as Tier 1, 2, or 3 for a CISO content strategy.

TIER 3 (DEFAULT — most articles):
  Quick LinkedIn reaction. Use for: news, podcast episodes, blog posts, opinion pieces,
  LinkedIn posts from others. When in doubt, this is the right tier.

TIER 2 (substantive sources):
  Standalone blog post. Use only if this single article has enough original depth,
  data, or insight to anchor a full dedicated write-up.

TIER 1 (rare — landmark primary sources only):
  Full long-form article. Only for: Verizon DBIR, Google Threat Horizons, government
  regulations, original industry studies. Podcast episodes and blog posts are NOT T1.

ARTICLE: {title}
SOURCE: {source}
URL: {url}
SUMMARY: {tldr}
KEY POINTS:
{points}

Reply with ONLY a single digit: 1, 2, or 3."""


def get_synthesis(record):
    """
    Handle synthesis stored in any format:
    - Native dict (Firestore map)
    - JSON string → {"tldr": ..., "key_points": [...]}
    - Plain string → use as tldr directly
    """
    raw = record.get("synthesis", {})

    if isinstance(raw, dict):
        return raw

    if isinstance(raw, str) and raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
        # Plain string — use as the summary directly
        return {"tldr": raw[:300], "key_points": []}

    return {}


def reclassify_all():
    client = anthropic.Anthropic()
    db = _get_db()

    docs = db.collection(COLLECTION).order_by("date_found").get()
    records = [doc.to_dict() for doc in docs]

    print(f"Re-classifying {len(records)} records...\n")
    print(f"  {'ID':<6} {'OLD':>3} {'NEW':>3}  TITLE")
    print(f"  {'─'*6} {'─'*3} {'─'*3}  {'─'*55}")

    tier_counts = {1: 0, 2: 0, 3: 0}
    changed = 0
    skipped = 0

    for record in records:
        record_id = record.get("id", "?")
        title = record.get("title", "Unknown")[:55]
        source_name = record.get("source_name", "Unknown")
        source_url = record.get("source_url", "")[:80]
        old_tier = record.get("tier", "?")

        syn = get_synthesis(record)
        tldr = syn.get("tldr", "").strip()
        key_points = syn.get("key_points", [])

        if not tldr:
            print(f"  #{record_id:<5} {str(old_tier):>3}  {'—':>3}  [skipped — no summary]")
            skipped += 1
            continue

        points_text = "\n".join(f"- {p}" for p in key_points[:3]) or "- (see summary above)"

        prompt = TIER_PROMPT.format(
            title=record.get("title", "Unknown"),
            source=source_name,
            url=source_url,
            tldr=tldr,
            points=points_text
        )

        try:
            response = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=5,
                messages=[{"role": "user", "content": prompt}]
            )

            answer = response.content[0].text.strip()
            new_tier = None
            for ch in answer:
                if ch in "123":
                    new_tier = int(ch)
                    break

            if new_tier not in [1, 2, 3]:
                new_tier = 3

            db.collection(COLLECTION).document(record_id).update({"tier": new_tier})

            tier_counts[new_tier] += 1
            if new_tier != old_tier:
                changed += 1
            marker = "←" if new_tier != old_tier else " "
            print(f"  #{record_id:<5} {str(old_tier):>3} {str(new_tier):>3}{marker} {title}")

        except Exception as e:
            print(f"  #{record_id:<5} {str(old_tier):>3}  ERR  {e}")
            skipped += 1

    print(f"\n{'─'*72}")
    print(f"✅ Done — {changed} tiers changed, {skipped} skipped")
    print(f"   T1: {tier_counts[1]}  T2: {tier_counts[2]}  T3: {tier_counts[3]}")
    print(f"\nExpected: ~2-3 T1, ~15-18 T2, ~28-32 T3")


if __name__ == "__main__":
    reclassify_all()
