"""
process_urdu_corpus.py
======================
Extracts clean Urdu text from Wikipedia XML dump.

What it does:
1. Parses the bz2-compressed XML article by article
2. Strips all wiki markup (templates, links, headers, tables)
3. Keeps only Urdu Unicode characters (U+0600–U+06FF range)
4. Filters out short/garbage articles
5. Writes clean text to data/processed/urdu_corpus.txt
6. Prints stats: articles, characters, vocabulary size

Run: python3 process_urdu_corpus.py
"""

import bz2
import re
import os
import xml.etree.ElementTree as ET
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────
INPUT_FILE  = Path("data/raw/urwiki-latest-pages-articles.xml.bz2")
OUTPUT_FILE = Path("data/processed/urdu_corpus.txt")
MIN_LENGTH  = 200   # minimum chars per article (filter stubs)
MAX_ARTICLES = None # set to e.g. 5000 to limit for quick test

# ── Urdu Unicode range ───────────────────────────────────────────────
# Urdu uses Arabic script: U+0600–U+06FF (core Arabic/Urdu block)
# Plus U+0750–U+077F (Arabic Supplement) and U+FB50–U+FDFF (Arabic Presentation)
URDU_PATTERN = re.compile(r'[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\u200C\u200D\s]+')

def strip_wiki_markup(text: str) -> str:
    """Remove Wikipedia markup, leaving only readable text."""
    # Remove {{templates}}
    while '{{' in text:
        start = text.rfind('{{')
        end = text.find('}}', start)
        if end == -1:
            break
        text = text[:start] + text[end+2:]

    # Remove [[File:...]] and [[Image:...]]
    text = re.sub(r'\[\[(File|Image|تصویر|زمرہ|Category)[^\]]*\]\]', '', text, flags=re.IGNORECASE)

    # Convert [[link|display]] → display text only
    text = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]', r'\1', text)

    # Remove [external links]
    text = re.sub(r'\[https?://[^\s\]]*\s*([^\]]*)\]', r'\1', text)
    text = re.sub(r'https?://\S+', '', text)

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Remove wiki headers (== Header ==)
    text = re.sub(r'={2,}[^=]*={2,}', '', text)

    # Remove tables
    text = re.sub(r'\{\|.*?\|\}', '', text, flags=re.DOTALL)

    # Remove bold/italic markup
    text = re.sub(r"'{2,}", '', text)

    # Remove references and citations
    text = re.sub(r'<ref[^/]*/>', '', text)
    text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL)

    # Collapse whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)

    return text.strip()


def extract_urdu_text(text: str) -> str:
    """Keep only Urdu/Arabic script characters and whitespace."""
    # Find all sequences of Urdu characters
    matches = URDU_PATTERN.findall(text)
    return ' '.join(m.strip() for m in matches if m.strip())


def is_redirect(text: str) -> bool:
    return text.strip().lower().startswith('#redirect') or \
           text.strip().startswith('#رجوع_مکرر') or \
           'REDIRECT' in text[:100].upper()


def process_corpus():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    articles_processed = 0
    articles_skipped   = 0
    total_chars        = 0
    unique_chars       = set()

    print(f"Reading: {INPUT_FILE}")
    print(f"Output:  {OUTPUT_FILE}")
    print(f"Min article length: {MIN_LENGTH} chars\n")

    with bz2.open(INPUT_FILE, 'rt', encoding='utf-8') as f_in, \
         open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:

        # Parse XML incrementally (memory efficient)
        context = ET.iterparse(f_in, events=('start', 'end'))
        _, root = next(context)

        ns = ''  # namespace prefix
        title = ''

        for event, elem in context:
            tag = elem.tag.split('}')[-1]  # strip namespace

            if event == 'end' and tag == 'title':
                title = elem.text or ''

            if event == 'end' and tag == 'text':
                raw_text = elem.text or ''

                # Skip redirects and empty pages
                if is_redirect(raw_text) or not raw_text.strip():
                    articles_skipped += 1
                    elem.clear()
                    root.clear()
                    continue

                # Clean markup
                cleaned = strip_wiki_markup(raw_text)

                # Extract Urdu text only
                urdu_text = extract_urdu_text(cleaned)

                # Filter short articles
                if len(urdu_text) < MIN_LENGTH:
                    articles_skipped += 1
                    elem.clear()
                    root.clear()
                    continue

                # Write to corpus
                f_out.write(urdu_text + '\n\n')
                total_chars += len(urdu_text)
                unique_chars.update(urdu_text)
                articles_processed += 1

                if articles_processed % 500 == 0:
                    print(f"  {articles_processed:,} articles | {total_chars:,} chars")

                if MAX_ARTICLES and articles_processed >= MAX_ARTICLES:
                    break

                elem.clear()
                root.clear()

    print(f"\n{'='*50}")
    print(f"✅ Corpus extraction complete")
    print(f"   Articles kept:    {articles_processed:,}")
    print(f"   Articles skipped: {articles_skipped:,}")
    print(f"   Total characters: {total_chars:,}")
    print(f"   Unique characters:{len(unique_chars):,}")
    print(f"   Output file:      {OUTPUT_FILE}")
    print(f"   File size:        {OUTPUT_FILE.stat().st_size / 1024 / 1024:.1f} MB")
    print(f"\nUnique Urdu characters found:")
    urdu_chars = sorted([c for c in unique_chars if c.strip()])
    print('  ' + ''.join(urdu_chars))


if __name__ == "__main__":
    process_corpus()
