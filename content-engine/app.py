import streamlit as st
import anthropic
import streamlit.components.v1 as components
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional
import json
import os
import io
from scraper import process_url, process_pasted_text
from sheets import (
    get_unprocessed_links, get_all_links,
    mark_as_synthesized, mark_as_skipped, mark_as_pending_paste,
    mark_as_duplicate, mark_as_dismissed,
)
from firebase_library import (
    add_record, load_library, get_library_stats,
    get_records_by_status, search_library, update_record_status, url_exists,
    get_pending_paste, add_pending_paste, remove_pending_paste,
    save_draft, delete_draft,
)

load_dotenv()

# ── Image generation (Google Imagen 3 via AI Studio) ─────────────────────────
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
IMAGEN_AVAILABLE = bool(GOOGLE_API_KEY)

def generate_image(prompt: str, aspect_ratio: str = "16:9") -> Optional[bytes]:
    """
    Generate an image using Google Imagen 3 via google-genai SDK.
    Returns raw PNG bytes or None on failure.
    aspect_ratio options: "16:9" (blog header), "1:1" (LinkedIn card), "4:3"
    """
    if not IMAGEN_AVAILABLE:
        return None
    MODELS_TO_TRY = [
        "imagen-3.0-generate-002",
        "imagen-3.0-fast-generate-001",
        "imagen-3.0-generate-001",
    ]
    last_error = None
    try:
        from google import genai as gai
        from google.genai import types as gai_types
        client = gai.Client(api_key=GOOGLE_API_KEY)
        for model_name in MODELS_TO_TRY:
            try:
                response = client.models.generate_images(
                    model=model_name,
                    prompt=prompt,
                    config=gai_types.GenerateImagesConfig(
                        number_of_images=1,
                        aspect_ratio=aspect_ratio,
                        safety_filter_level="BLOCK_SOME",
                    ),
                )
                if response.generated_images:
                    return response.generated_images[0].image.image_bytes
            except Exception as model_err:
                last_error = model_err
                continue
        st.warning(
            f"Image generation failed on all models. "
            f"Last error: {last_error}\n\n"
            f"**Fix:** Go to aistudio.google.com/apikey and click 'Set up billing' "
            f"next to your key. Imagen 3 requires billing to be enabled (~$0.04/image)."
        )
    except Exception as e:
        st.warning(f"Image generation failed: {e}")
    return None

st.set_page_config(page_title="Content Engine", page_icon="✍️", layout="wide")

st.markdown("""
<style>
.stExpander { border-left: 3px solid #d4a853; }
</style>
""", unsafe_allow_html=True)

# Session state
for key, default in {
    "active_record": None,
    "draft": "",
    "linkedin_draft": "",
    "processing_status": [],
    "paste_needed": [],
    "chat_messages": [],
    "deep_synthesis": None,
    "last_processed_results": [],
    "last_write_record_id": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

client = anthropic.Anthropic()

USMAN_VOICE = """
You write as Usman Chaudhary — Field CISO at Google Cloud, 17 years in security.
Audience: CISOs, boards, senior security leaders.

VOICE:
- Open with urgency — bold claim or named problem with emoji
- Coin memorable terms for concepts
- Short punchy paragraphs (max 4 sentences each)
- Technical enough to be credible, accessible for boards
- End with LET'S call to action

CITATIONS — NON-NEGOTIABLE:
- Every specific claim must be attributed: "[Author/Org] found..." or "(Source: Publication, Year)"
- Your original reasoning flagged explicitly: "From my CISO experience..." or "In my view..."
- NEVER present researched facts as your own original observations
- NEVER include raw search meta-text like "I searched for..." or "According to my search..."
- Clean citations into natural prose — read like a polished article, not a search dump
- T3: Credit the source article by name at the end
- T2: Cite claims inline + "📚 Sources" section at end (3-5 references)
- T1: Inline citations throughout + "📚 References" section at end (5-8 references), numbered

═══════════════════════════════
TIER 1 — FULL BLOG POST (1200-1800 words) for usmanc.com
Follow this structure EXACTLY:
═══════════════════════════════

# 🚨 [Emoji + Headline with Coined Term]
### [One-line subheading expanding the headline]

---

> **TL;DR for the busy CISO:** [2-3 sentences. Full argument in 50 words max.]

---

## The Challenge

[2-3 short paragraphs. Name the problem. Urgency. Open with a striking stat or event.]

> *"[Pull quote — single most powerful sentence in this section]"*

## Why This Matters More Than You Think

[2-3 paragraphs. Scale the problem. Data with citations. Show the blast radius.]

## [Third section — name based on content, e.g. "The Three Survival Paths"]

[Core insight. Use named subsections. Each gets 2-3 sentences max.]

### [Name 1]
[2-3 sentences]

### [Name 2]
[2-3 sentences]

### [Name 3]
[2-3 sentences]

## What CISOs Should Do This Quarter

1. **[Specific Action]** — [One sentence on how, with timeline]
2. **[Specific Action]** — [One sentence on how, with timeline]
3. **[Specific Action]** — [One sentence on how, with timeline]

---

**LET'S [call to action].**

---

📚 **References**
1. [Author, Publication, Year — brief description]
2. [Author, Publication, Year — brief description]
...

---
*Usman Chaudhary is Field CISO at Google Cloud, advising Fortune 500 boards and federal agencies on AI security risk.*

═══════════════════════════════
TIER 2 — BLOG POST (500-800 words)
Follow this structure EXACTLY:
═══════════════════════════════

# [Emoji + Headline]

*[Author] at [Publication] just gave every CISO a reason to pay attention.*

[Opening paragraph — 3-4 sentences. State the core insight immediately.]

---

## Why This Matters

[2-3 short paragraphs. Urgency and context. Cite the trigger article.]

## [Second section — name based on content]

- **[Point 1]:** [2 sentences with citation]
- **[Point 2]:** [2 sentences with citation]
- **[Point 3]:** [2 sentences with citation]

## What You Should Do

1. **[Action]** — [How and when]
2. **[Action]** — [How and when]

---

**LET'S [call to action].**

*Link to the original in the comments.*

📚 **Sources**
1. [Source 1]
2. [Source 2]

#Hashtags

═══════════════════════════════
TIER 3 — LINKEDIN REACTION (150-300 words)
Follow this structure EXACTLY:
═══════════════════════════════

[Emoji] **[Bold hook — one sentence]**

[Author] at [Publication] just published something worth reading.

**My top 3 CISO takeaways:**

⚖️ **[Named concept]** — [1-2 sentences]

⏱️ **[Named concept]** — [1-2 sentences]

🛡️ **[Named concept]** — [1-2 sentences]

Link to the original in the comments.

**LET'S [call to action].**

#Hashtags

═══════════════════════════════
UNIVERSAL RULES
═══════════════════════════════
- Follow the format structure exactly — do not add or remove sections
- Every paragraph max 4 sentences
- Sections separated by --- dividers
- No hedging language, no corporate fluff
- Hashtags only at the very end
- No bold text mid-sentence for decoration — only for named concepts and action items
"""

# ── Header ────────────────────────────────────────────────────────
stats = get_library_stats()
col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
with col1:
    st.title("✍️ Content Engine")
    st.caption("Intelligence synthesis and content creation — Usman Chaudhary")
with col2:
    st.metric("Library Records", stats["total"])
with col3:
    st.metric("Ready to Write", stats["synthesized"])
with col4:
    st.metric("Published", stats["published"])

tabs = st.tabs(["📰 Daily Brief", "📋 Reading List", "➕ Add Content", "📚 Library", "✍️ Write", "🔍 Search", "📅 Briefs"])


# ── HTML article export ──────────────────────────────────────────
def draft_to_html(draft_text: str, record: dict, header_image_bytes: bytes = None) -> str:
    """Convert markdown draft to a complete styled HTML article page."""
    import re as _re

    title = record.get("title", "Article")
    source = record.get("source_name", "")
    date = datetime.now().strftime("%B %d, %Y")
    year = datetime.now().year

    # Pre-process: join orphaned citation fragments back to preceding paragraph
    # Lines starting with ". " or ", " are citation continuations, not new paragraphs
    lines = draft_text.split("\n")
    joined = []
    for line in lines:
        stripped = line.strip()
        if joined and stripped and (stripped.startswith(". ") or stripped.startswith(", ")):
            # Merge with previous non-empty line
            for i in range(len(joined) - 1, -1, -1):
                if joined[i].strip():
                    joined[i] = joined[i].rstrip() + stripped
                    break
            else:
                joined.append(line)
        else:
            joined.append(line)
    draft_text = "\n".join(joined)
    lines = draft_text.split("\n")

    html_lines = []
    in_ol = False
    in_ul = False

    def inline_fmt(text):
        text = _re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        text = _re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
        return text

    for line in lines:
        stripped = line.strip()

        if stripped and stripped[0].isdigit() and ". " in stripped[:5]:
            if not in_ol:
                html_lines.append("<ol>")
                in_ol = True
            item = stripped.split(". ", 1)[1] if ". " in stripped else stripped
            html_lines.append(f"  <li>{inline_fmt(item)}</li>")
            continue
        elif in_ol:
            html_lines.append("</ol>")
            in_ol = False

        if stripped.startswith("- ") or stripped.startswith("• "):
            if not in_ul:
                html_lines.append("<ul>")
                in_ul = True
            html_lines.append(f"  <li>{inline_fmt(stripped[2:])}</li>")
            continue
        elif in_ul:
            html_lines.append("</ul>")
            in_ul = False

        if stripped.startswith("### "):
            html_lines.append(f"<h3>{inline_fmt(stripped[4:])}</h3>")
        elif stripped.startswith("## "):
            html_lines.append(f"<h2>{inline_fmt(stripped[3:])}</h2>")
        elif stripped.startswith("# "):
            html_lines.append(f"<h1>{inline_fmt(stripped[2:])}</h1>")
        elif stripped.startswith("> "):
            inner = inline_fmt(stripped[2:].strip("*").strip('"'))
            html_lines.append(f"<blockquote>{inner}</blockquote>")
        elif stripped == "---":
            html_lines.append("<hr>")
        elif stripped == "":
            html_lines.append("")
        else:
            html_lines.append(f"<p>{inline_fmt(stripped)}</p>")

    if in_ol: html_lines.append("</ol>")
    if in_ul: html_lines.append("</ul>")

    body = "\n".join(html_lines)

    # Header image embed
    hero_img_html = ""
    if header_image_bytes:
        import base64
        b64 = base64.b64encode(header_image_bytes).decode()
        hero_img_html = f'''<div class="hero-img">
      <img src="data:image/png;base64,{b64}" alt="{title}" style="width:100%;max-height:480px;object-fit:cover;display:block;">
    </div>'''

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — Usman Chaudhary</title>
<style>
:root{{--gold:#d4a853;--dark:#111;--surface:#1a1a1a;--text:#e8e8e8;--muted:#888;--border:#2a2a2a}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Georgia,serif;background:var(--dark);color:var(--text);line-height:1.8}}
header{{border-bottom:1px solid var(--border);padding:1.25rem 2rem}}
header a{{color:var(--gold);text-decoration:none;font-weight:600;font-size:1rem}}
.hero{{background:var(--surface);padding:4rem 2rem 3rem;text-align:center;border-bottom:1px solid var(--border)}}
.hero .tag{{color:var(--gold);font-size:.75rem;font-weight:700;letter-spacing:.15em;text-transform:uppercase;margin-bottom:1.25rem}}
.hero h1{{font-size:clamp(2rem,4.5vw,3.5rem);font-weight:800;line-height:1.15;max-width:900px;margin:0 auto 1.25rem;color:#fff}}
.hero .meta{{color:var(--muted);font-size:.9rem;margin-top:1.25rem}}
.hero .meta strong{{color:var(--gold)}}
article{{max-width:900px;margin:0 auto;padding:3.5rem 2.5rem 7rem}}
article h1{{display:none}}
article h2{{font-size:1.6rem;font-weight:700;color:#fff;margin:3.5rem 0 1.25rem;padding-bottom:.6rem;border-bottom:2px solid var(--gold)}}
article h3{{font-size:1.2rem;font-weight:700;color:var(--gold);margin:2.25rem 0 .75rem}}
article p{{margin-bottom:1.4rem;font-size:1.05rem;max-width:72ch}}
article blockquote{{border-left:4px solid var(--gold);background:var(--surface);padding:1.25rem 1.75rem;margin:2.5rem 0;border-radius:0 8px 8px 0;font-style:italic;color:#ccc;font-size:1.1rem;max-width:72ch}}
article strong{{color:#fff}}
article em{{color:var(--gold);font-style:normal}}
article hr{{border:none;border-top:1px solid var(--border);margin:3rem 0}}
article ol,article ul{{padding-left:1.75rem;margin-bottom:1.4rem;max-width:72ch}}
article li{{margin-bottom:.6rem;font-size:1.05rem}}
article .in-article-img{{margin:2.5rem 0;border-radius:8px;overflow:hidden}}
article .in-article-img img{{width:100%;height:auto;display:block}}
footer{{border-top:1px solid var(--border);padding:2rem;text-align:center;color:var(--muted);font-size:.85rem}}
footer a{{color:var(--gold);text-decoration:none}}
@media(max-width:700px){{article{{padding:2rem 1.25rem 4rem}}.hero{{padding:2.5rem 1rem}}article p,article li,article blockquote{{max-width:100%}}}}
</style>
</head>
<body>
<header><a href="https://usmanc.com">usmanc.com</a></header>
{hero_img_html}
<div class="hero">
  <div class="tag">Field CISO &middot; AI Security</div>
  <h1>{title}</h1>
  <div class="meta"><strong>Usman Chaudhary</strong> &middot; Field CISO, Google Cloud &middot; {date} &middot; {source}</div>
</div>
<article>{body}</article>
<footer>
  <a href="https://usmanc.com">usmanc.com</a> &middot; <a href="https://linkedin.com/in/usmanchaudhary">LinkedIn</a>
  <p style="margin-top:.5rem">&copy; {year} Usman Chaudhary</p>
</footer>
</body>
</html>"""


# ── Web research helper ───────────────────────────────────────────────────
def generate_with_research(prompt: str, system: str, max_tokens: int = 3000) -> str:
    """Generate content using Claude with web_search tool. Handles multi-turn."""
    messages = [{"role": "user", "content": prompt}]
    last_text = ""
    try:
        for _ in range(6):
            response = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=max_tokens,
                system=system,
                tools=[{"type": "web_search_20250305", "name": "web_search"}],
                messages=messages
            )
            last_text = "\n".join(
                b.text for b in response.content
                if hasattr(b, "type") and b.type == "text"
            )
            if response.stop_reason == "end_turn":
                return last_text
            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                tool_results = [
                    {"type": "tool_result", "tool_use_id": b.id, "content": ""}
                    for b in response.content
                    if hasattr(b, "type") and b.type == "tool_use"
                ]
                messages.append({"role": "user", "content": tool_results})
            else:
                return last_text
        return last_text or "Generation incomplete — try again."
    except Exception as e:
        # Fallback without web search
        fallback = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt +
                        "\n\n[Web search unavailable. Use your training knowledge and cite sources you know.]"}]
        )
        return fallback.content[0].text


# ═══════════════════════════════════════════════════════
# TAB 1 — DAILY BRIEF
# ═══════════════════════════════════════════════════════

def get_interest_profile() -> list:
    """Derive interest topics from library weighted by tier (T1=3, T2=2, T3=1)."""
    from collections import Counter
    library = load_library()
    weights = Counter()
    tier_w = {1: 3, 2: 2, 3: 1}
    for r in library["records"]:
        w = tier_w.get(r.get("tier", 3), 1)
        for theme in r.get("themes", []):
            weights[theme] += w
    return [t for t, _ in weights.most_common(8)]


def generate_daily_brief(profile: list) -> dict:
    """
    Generate a narrative intelligence brief via Claude web search.
    Returns: {brief_text, articles, generated_at}
    """
    from datetime import date as _date
    today = datetime.now().strftime("%A, %B %d, %Y")
    topics = "\n".join(f"- {t}" for t in profile)

    prompt = f"""Search the web for the most important developments published in the last 7 days
on these topics for a Field CISO at Google Cloud:
{topics}

Then write a professional intelligence brief following this EXACT format:

---
## 📰 Intelligence Brief — {today}

**Top Story**
[2-3 sentences on the single most important development. Name the source.]

## Key Developments

**[Topic area]: [Headline]**
[2-3 sentences. What happened, why it matters for enterprise security. Cite source.]

**[Topic area]: [Headline]**
[2-3 sentences. Cite source.]

**[Topic area]: [Headline]**
[2-3 sentences. Cite source.]

**[Topic area]: [Headline]**
[2-3 sentences. Cite source.]

## What CISOs Should Watch This Week
- [Specific thing to monitor with brief reason]
- [Specific thing to monitor with brief reason]
- [Specific thing to monitor with brief reason]

## 📚 Sources
1. [Exact article title] — [Publication] — [full URL]
2. [Exact article title] — [Publication] — [full URL]
3. [Exact article title] — [Publication] — [full URL]
4. [Exact article title] — [Publication] — [full URL]
5. [Exact article title] — [Publication] — [full URL]
---

Rules:
- Write in the style of a professional intelligence analyst briefing a CISO
- Be specific — name companies, numbers, dates
- Every claim must reference a real article you searched
- Keep total length 400-600 words
- Sources section must have real URLs you found"""

    brief_text = generate_with_research(
        prompt,
        "You are an intelligence analyst writing a daily brief for a Field CISO. Be specific and cite real sources.",
        max_tokens=2500
    )

    # Extract article URLs from the Sources section
    import re as _re
    articles = []
    sources_match = _re.search(r'##\s*📚\s*Sources\s*\n(.*?)(?:\n---|\Z)', brief_text, _re.DOTALL)
    if sources_match:
        for line in sources_match.group(1).strip().split('\n'):
            url_match = _re.search(r'https?://[^\s\)]+', line)
            title_match = _re.match(r'\d+\.\s*\*?\*?([^\*\—]+)', line)
            pub_match = _re.search(r'—\s*([^—\n]+)\s*—\s*https?://', line)
            if url_match:
                articles.append({
                    "title": title_match.group(1).strip() if title_match else "Article",
                    "source": pub_match.group(1).strip() if pub_match else "",
                    "url": url_match.group().rstrip(')')
                })

    return {
        "brief_text": brief_text,
        "articles": articles,
        "generated_at": datetime.now().isoformat(),
        "date": today,
        "profile": profile
    }


def save_daily_brief(data: dict) -> None:
    from firebase_library import _get_db
    from datetime import date
    db = _get_db()
    db.collection("daily_briefs").document(date.today().isoformat()).set(data)


def load_daily_brief(date_str: str = None) -> dict:
    from firebase_library import _get_db
    from datetime import date
    db = _get_db()
    key = date_str or date.today().isoformat()
    doc = db.collection("daily_briefs").document(key).get()
    return doc.to_dict() if doc.exists else {}


def list_saved_briefs() -> list:
    from firebase_library import _get_db
    db = _get_db()
    docs = db.collection("daily_briefs").order_by("generated_at", direction="DESCENDING").limit(14).get()
    return [{"id": d.id, **d.to_dict()} for d in docs]


with tabs[0]:
    st.markdown(f"### 📰 Daily Intelligence Brief — {datetime.now().strftime('%A, %B %d, %Y')}")

    # ── Interest profile ──────────────────────────────────────────
    profile = get_interest_profile()
    cached = load_daily_brief()

    st.markdown("**Your interest profile** *(auto-derived from library, weighted by tier)*")
    if profile:
        st.markdown("  ".join([f"`{t}`" for t in profile]))
    else:
        st.caption("Add articles to your library — interest profile builds automatically.")
    st.markdown("")

    # ── Generate / Refresh ────────────────────────────────────────
    col_btn, col_cache = st.columns([3, 1])
    with col_btn:
        btn_label = "🔍 Generate Today's Brief" if not cached else "🔄 Refresh Brief"
        gen_clicked = st.button(btn_label, type="primary", use_container_width=True)
    with col_cache:
        if cached and cached.get("generated_at"):
            st.caption(f"Cached {cached['generated_at'][11:16]}")

    if gen_clicked and profile:
        with st.spinner("Searching the web and writing your brief... (30-60 sec)"):
            brief = generate_daily_brief(profile)
            if brief.get("brief_text"):
                save_daily_brief(brief)
                cached = brief
                st.rerun()
            else:
                st.warning("Generation failed — try again.")
    elif gen_clicked and not profile:
        st.warning("Your library has no themes yet. Synthesize some articles first.")

    # ── Display the brief ─────────────────────────────────────────
    if cached and cached.get("brief_text"):
        st.markdown("---")
        st.markdown(cached["brief_text"])

        # ── Source articles → Add to Library ─────────────────────
        articles = cached.get("articles", [])
        if articles:
            st.markdown("---")
            st.markdown("### Add to Library")
            st.caption("Synthesize individual articles from today's brief into your intelligence library.")

            for i, a in enumerate(articles):
                url = a.get("url", "")
                title = a.get("title", "Article")[:70]
                source = a.get("source", "")
                already = url_exists(url) if url else False

                col_t, col_btn = st.columns([4, 1])
                with col_t:
                    if url:
                        st.markdown(f"**{title}** `{source}`")
                    else:
                        st.markdown(f"**{title}** `{source}`")
                with col_btn:
                    if already:
                        st.caption("✅ In library")
                    elif url:
                        if st.button("＋ Add", key=f"add_{i}_{url[-20:]}", use_container_width=True):
                            with st.spinner(f"Synthesizing..."):
                                result = process_url(url, depth="quick")
                                if result and result.get("success"):
                                    sp = result.get("suggested_piece", {})
                                    record = add_record(
                                        source_url=url,
                                        source_name=result.get("source_name", source),
                                        author=result.get("author", "Unknown"),
                                        title=result.get("title", title),
                                        synthesis=json.dumps({
                                            "tldr": result.get("tldr", ""),
                                            "key_points": result.get("key_points", []),
                                            "why_timely": result.get("why_timely", "")
                                        }),
                                        key_quotes=result.get("key_quotes", []),
                                        content_angle=json.dumps(sp),
                                        tier=sp.get("recommended_tier", result.get("tier", 3)),
                                        themes=result.get("themes", []),
                                        raw_content=result.get("raw_content", "")
                                    )
                                    st.success(f"✅ Added as #{record['id']} — T{sp.get('recommended_tier', 3)}")
                                    st.rerun()
                                else:
                                    st.error("Could not scrape — try via Reading List tab")

    # ── URL Processor (collapsed) ─────────────────────────────────
    st.markdown("---")
    with st.expander("🔗 Add content manually", expanded=False):
        urls_input = st.text_area("Paste URLs (one per line)", height=80, key="manual_urls")
        if st.button("🚀 Process", type="primary", use_container_width=True, key="proc_manual"):
            if urls_input.strip():
                urls = [u.strip() for u in urls_input.strip().split("\n") if u.strip()]
                for url in urls:
                    if url_exists(url):
                        st.info(f"⏭️ Already in library: `{url[:60]}`")
                        continue
                    with st.spinner(f"Processing {url[:50]}..."):
                        result = process_url(url, depth="quick")
                    if result and result["success"]:
                        sp = result.get("suggested_piece", {})
                        record = add_record(
                            source_url=url,
                            source_name=result.get("source_name", "Unknown"),
                            author=result.get("author", "Unknown"),
                            title=result.get("title", "Untitled"),
                            synthesis=json.dumps({
                                "tldr": result.get("tldr", ""),
                                "key_points": result.get("key_points", []),
                                "why_timely": result.get("why_timely", "")
                            }),
                            key_quotes=result.get("key_quotes", []),
                            content_angle=json.dumps(sp),
                            tier=sp.get("recommended_tier", 3),
                            themes=result.get("themes", []),
                            raw_content=result.get("raw_content", "")
                        )
                        st.success(f"✅ Added #{record['id']}: **{result.get('title','')[:50]}** — T{sp.get('recommended_tier',3)}")
                    else:
                        st.warning(f"⚠️ Needs paste: `{url[:60]}`")


# ═══════════════════════════════════════════════════════
# TAB 2 — READING LIST
# ═══════════════════════════════════════════════════════
with tabs[1]:
    st.subheader("📋 Reading List — Google Sheets Import")
    st.caption("Bulk synthesize your curated reading list. Column G tracks what the Content Engine has processed.")

    if "sheet_links" not in st.session_state:
        st.session_state.sheet_links = []
    if "sheet_processing" not in st.session_state:
        st.session_state.sheet_processing = False
    if "sheet_results" not in st.session_state:
        st.session_state.sheet_results = []
    if "last_synced" not in st.session_state:
        st.session_state.last_synced = None
    if "sync_stats" not in st.session_state:
        st.session_state.sync_stats = {}

    from datetime import datetime as dt
    now = dt.now()

    persistent_paste = get_pending_paste()
    if persistent_paste:
        st.error(f"🔴 ACTION REQUIRED — {len(persistent_paste)} links need your input")
        for item in persistent_paste:
            url = item['url']
            with st.expander(f"📋 Row {item['row']}: {url[:65]}"):
                pasted = st.text_area("Paste article content", key=f"persist_paste_{url}", height=150)
                c1, c2 = st.columns(2)
                with c1:
                    p_title = st.text_input("Title (optional)", key=f"persist_title_{url}")
                with c2:
                    p_author = st.text_input("Author (optional)", key=f"persist_author_{url}")

                btn_proc, btn_skip = st.columns([3, 1])
                with btn_proc:
                    process_clicked = st.button("✍️ Process", key=f"persist_btn_{url}",
                                                use_container_width=True, type="primary")
                with btn_skip:
                    skip_clicked = st.button("🚫 Skip", key=f"persist_skip_{url}",
                                             use_container_width=True)

                if skip_clicked:
                    remove_pending_paste(url)
                    mark_as_dismissed(item['row'])
                    st.session_state.sheet_results = [
                        r for r in st.session_state.sheet_results if r['url'] != url
                    ]
                    st.success(f"Dismissed row {item['row']}.")
                    st.rerun()

                if process_clicked:
                    if pasted:
                        title = p_title or url.split("/")[-2].replace("-", " ").title()
                        author = p_author or "Unknown"
                        source = url.split("/")[2].replace("www.", "") if "//" in url else "Unknown"
                        result = process_pasted_text(
                            text=pasted, url=url, source_name=source,
                            author=author, title=title, depth="quick"
                        )
                        if result["success"]:
                            sp = result.get("suggested_piece", {})
                            record = add_record(
                                source_url=url, source_name=source, author=author,
                                title=result.get("title") or title,
                                synthesis=json.dumps({
                                    "tldr": result.get("tldr", ""),
                                    "key_points": result.get("key_points", []),
                                    "why_timely": result.get("why_timely", "")
                                }),
                                key_quotes=result.get("key_quotes", []),
                                content_angle=json.dumps(sp),
                                tier=sp.get("recommended_tier", 3),
                                themes=result.get("themes", []),
                                raw_content=pasted[:2000]
                            )
                            mark_as_synthesized(item['row'])
                            remove_pending_paste(url)
                            st.session_state.sheet_results = [
                                r for r in st.session_state.sheet_results if r['url'] != url
                            ]
                            st.success(f"✅ Added as Record #{record['id']}!")
                            st.rerun()
                    else:
                        st.warning("Paste content or click Skip to dismiss.")
        st.markdown("---")

    if st.session_state.last_synced:
        elapsed = (now - st.session_state.last_synced).seconds // 60
        sync_label = f"Last synced {elapsed} min ago" if elapsed < 60 else f"Last synced {elapsed // 60}h ago"
        new_count = st.session_state.sync_stats.get("new_found", 0)
        if new_count > 0:
            st.info(f"🔄 {sync_label} — {new_count} new links found")
        else:
            st.success(f"✅ {sync_label} — library up to date")

    col1, col2, col3 = st.columns(3)

    if st.button("🔄 Refresh from Google Sheets", type="primary", use_container_width=False):
        with st.spinner("Reading your Google Sheet..."):
            all_links = get_all_links()
            unprocessed = get_unprocessed_links()
            st.session_state.sheet_links = unprocessed
            st.session_state.last_synced = now
            st.session_state.sync_stats = {"new_found": len(unprocessed)}
            synthesized_count = len([l for l in all_links if l['synthesized']])
            viewed_count = len([l for l in all_links if l['usman_viewed']])
            with col1:
                st.metric("Total in Sheet", len(all_links))
            with col2:
                st.metric("You've Viewed", viewed_count)
            with col3:
                st.metric("Ready to Synthesize", len(unprocessed))

    if st.session_state.sheet_links:
        st.markdown(f"### {len(st.session_state.sheet_links)} links ready to synthesize")

        col_a, col_b = st.columns(2)
        with col_a:
            show_viewed_only = st.checkbox("Show only links you've viewed (col F = Yes)")
        with col_b:
            batch_size = st.slider("Batch size", 5, 30, 10)

        links_to_show = st.session_state.sheet_links
        if show_viewed_only:
            links_to_show = [l for l in links_to_show if l.get('usman_viewed') in ['yes', 'y']]

        st.caption(f"Showing {len(links_to_show)} links")

        with st.expander(f"Preview links ({len(links_to_show[:batch_size])} will be processed)"):
            for item in links_to_show[:batch_size]:
                viewed = "👁" if item.get('usman_viewed') in ['yes', 'y'] else "○"
                st.caption(f"{viewed} Row {item['row']}: {item['url'][:80]}")

        st.markdown("---")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            process_btn = st.button(
                f"🚀 Synthesize next {min(batch_size, len(links_to_show))} links",
                type="primary", use_container_width=True
            )
        with col_btn2:
            st.caption("⚠️ Instagram, TikTok, and LinkedIn links need manual paste")

        if process_btn:
            batch = links_to_show[:batch_size]
            st.session_state.sheet_results = []
            progress = st.progress(0)
            status_box = st.empty()

            for i, item in enumerate(batch):
                url = item['url']
                row = item['row']
                status_box.info(f"Processing {i+1}/{len(batch)}: {url[:60]}...")

                skip_domains = ['instagram.com', 'tiktok.com', 'twitter.com', 'x.com', 'facebook.com']
                if any(domain in url for domain in skip_domains):
                    mark_as_skipped(row)
                    st.session_state.sheet_results.append({
                        "url": url, "row": row, "status": "skip",
                        "reason": "Platform cannot be auto-scraped"
                    })
                    progress.progress((i + 1) / len(batch))
                    continue

                if url_exists(url):
                    mark_as_duplicate(row)
                    st.session_state.sheet_results.append({
                        "url": url, "row": row, "status": "exists",
                        "title": "Already in library"
                    })
                    progress.progress((i + 1) / len(batch))
                    continue

                result = process_url(url, depth="quick")

                if result["success"]:
                    sp = result.get("suggested_piece", {})
                    record = add_record(
                        source_url=url,
                        source_name=result.get("source_name", "Unknown"),
                        author=result.get("author", "Unknown"),
                        title=result.get("title", "Untitled"),
                        synthesis=json.dumps({
                            "tldr": result.get("tldr", ""),
                            "key_points": result.get("key_points", []),
                            "why_timely": result.get("why_timely", "")
                        }),
                        key_quotes=result.get("key_quotes", []),
                        content_angle=json.dumps(sp),
                        tier=sp.get("recommended_tier", result.get("tier", 3) if result else 3),
                        themes=result.get("themes", []),
                        raw_content=result.get("raw_content", "")
                    )
                    mark_as_synthesized(row)
                    st.session_state.sheet_results.append({
                        "url": url, "row": row, "status": "success",
                        "title": result.get("title", ""),
                        "tier": sp.get("recommended_tier", result.get("tier", 3)),
                        "tldr": result.get("tldr", ""),
                        "record_id": record["id"]
                    })
                else:
                    add_pending_paste(url, row)
                    mark_as_pending_paste(row)
                    st.session_state.sheet_results.append({
                        "url": url, "row": row, "status": "needs_paste",
                        "error": result.get("error", "")
                    })

                progress.progress((i + 1) / len(batch))

            status_box.empty()
            st.session_state.sheet_links = get_unprocessed_links()
            st.session_state.last_synced = now

            success_count = len([r for r in st.session_state.sheet_results if r['status'] == 'success'])
            needs_paste_count = len([r for r in st.session_state.sheet_results if r['status'] == 'needs_paste'])
            skipped_count = len([r for r in st.session_state.sheet_results if r['status'] == 'skip'])
            dup_count = len([r for r in st.session_state.sheet_results if r['status'] == 'exists'])
            st.success(
                f"Done! {success_count} synthesized · {dup_count} duplicate · "
                f"{skipped_count} skipped · {needs_paste_count} need manual paste"
            )
            st.rerun()

        if st.session_state.sheet_results:
            skipped = [r for r in st.session_state.sheet_results if r['status'] == 'skip']
            succeeded = [r for r in st.session_state.sheet_results if r['status'] == 'success']
            existed = [r for r in st.session_state.sheet_results if r['status'] == 'exists']

            if skipped:
                st.markdown("---")
                st.warning(f"⏭️ SKIPPED — {len(skipped)} links from platforms that can't be auto-scraped")
                for item in skipped:
                    st.caption(f"  Row {item['row']}: {item['url'][:70]}")

            if succeeded:
                st.markdown("---")
                st.markdown(f"### ✅ Synthesized ({len(succeeded)})")
                for item in succeeded:
                    tier = item.get('tier', 3)
                    emoji = "🟡" if tier == 1 else ("🟣" if tier == 2 else "🔵")
                    with st.expander(f"{emoji} {item.get('title','')[:60]} | #{item.get('record_id')}"):
                        st.markdown(f"**TLDR:** {item.get('tldr','')}")
                        col_x, col_y = st.columns(2)
                        with col_x:
                            st.caption(f"Tier {tier} | Row {item['row']}")
                        with col_y:
                            if st.button("✍️ Write", key=f"sheet_write_{item.get('record_id')}"):
                                library = load_library()
                                rec = next((r for r in library["records"] if r["id"] == item["record_id"]), None)
                                if rec:
                                    st.session_state.active_record = rec
                                    st.rerun()

            if existed:
                st.markdown("---")
                st.caption(f"♻️ {len(existed)} duplicate(s) — marked Duplicate in sheet")


# ═══════════════════════════════════════════════════════
# TAB 3 — ADD CONTENT
# ═══════════════════════════════════════════════════════
with tabs[2]:
    st.subheader("Add Content to Library")

    input_method = st.radio(
        "Input method",
        ["🔗 URL", "📋 Paste text", "📎 PDF Upload", "💭 Topic idea"],
        horizontal=True
    )

    if input_method == "🔗 URL":
        url = st.text_input("Article or YouTube URL")
        if url and url_exists(url):
            st.warning("⚠️ This URL is already in your library.")
        depth = st.radio("Synthesis depth",
                         ["Quick (Haiku — fast)", "Deep (Sonnet — better for writing)"],
                         horizontal=True)
        if st.button("Process URL", type="primary"):
            if url:
                if url_exists(url):
                    st.error("Already in library. Use Library tab to view it.")
                else:
                    with st.spinner("Fetching and synthesizing..."):
                        d = "deep" if "Deep" in depth else "quick"
                        result = process_url(url, depth=d)
                    if result["success"]:
                        st.session_state.deep_synthesis = result
                        st.success("Done! Review below.")
                    else:
                        st.error(f"Failed: {result['error']}")
                        st.info("Try pasting the content manually.")

    elif input_method == "📋 Paste text":
        c1, c2, c3 = st.columns(3)
        with c1:
            p_url = st.text_input("Source URL (optional)")
        with c2:
            p_author = st.text_input("Author (optional)")
        with c3:
            p_source = st.text_input("Publication (optional)")
        p_title = st.text_input("Title (optional)")
        p_text = st.text_area("Paste content", height=250)
        depth = st.radio("Depth", ["Quick (Haiku)", "Deep (Sonnet)"], horizontal=True)

        if st.button("Process", type="primary"):
            if p_text:
                title = p_title or "Untitled"
                author = p_author or "Unknown"
                source = p_source or (p_url.split('/')[2].replace('www.', '') if p_url and '//' in p_url else "Unknown")
                with st.spinner("Synthesizing..."):
                    d = "deep" if "Deep" in depth else "quick"
                    result = process_pasted_text(
                        text=p_text, url=p_url or "manual",
                        source_name=source, author=author, title=title, depth=d
                    )
                if result["success"]:
                    st.session_state.deep_synthesis = result
                    st.success("Done!")
            else:
                st.error("Please paste some content first.")

    else:
        topic = st.text_input("Topic or idea")
        context = st.text_area("Your angle or context (optional)", height=100)
        if st.button("Save idea", type="primary"):
            if topic:
                add_record(
                    source_url=f"idea_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    source_name="Usman's Ideas",
                    author="Usman Chaudhary",
                    title=topic,
                    synthesis=json.dumps({"tldr": context or "Idea to develop", "key_points": [], "why_timely": ""}),
                    key_quotes=[],
                    content_angle=json.dumps({"what_to_write": context or topic, "recommended_tier": 1}),
                    tier=1, themes=["idea"], raw_content=""
                )
                st.success("Idea saved!")

    result = st.session_state.deep_synthesis
    if result and result.get("success"):
        st.markdown("---")
        st.markdown("### Preview")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{result.get('title', '')}**")
            st.caption(f"{result.get('author', '')} | {result.get('source_name', '')}")
            st.markdown(f"**TLDR:** {result.get('tldr', '')}")
            st.markdown("**Key Points:**")
            for p in result.get('key_points', []):
                st.markdown(f"• {p}")
            sp = result.get('suggested_piece', {})
            if sp:
                st.markdown("---")
                st.markdown("**Suggested Piece:**")
                st.markdown(f"• **What:** {sp.get('what_to_write', '')}")
                st.markdown(f"• **Why now:** {sp.get('why_now', '')}")
                st.markdown(f"• **Audience:** {sp.get('audience', '')}")
                st.markdown(f"• **Value:** {sp.get('value_to_audience', '')}")
                st.markdown(f"• **Your angle:** {sp.get('usman_angle', '')}")
                if sp.get('coined_term'):
                    st.markdown(f"• **Coined term:** _{sp.get('coined_term')}_")
                st.markdown(f"• **Tier:** {sp.get('recommended_tier', 3)}")
        with col2:
            sp = result.get('suggested_piece', {})
            tier_val = sp.get('recommended_tier', result.get('tier', 3))
            tier = st.selectbox("Tier", [1, 2, 3],
                                index=[1, 2, 3].index(tier_val) if tier_val in [1, 2, 3] else 2)
            themes = st.multiselect(
                "Themes",
                ["agentic SOC", "AI security", "AI governance", "post-quantum",
                 "cloud security", "zero trust", "SecOps", "threat intelligence",
                 "AI risk", "enterprise AI", "vibe coding", "data strategy"],
                default=result.get('themes', [])
            )
            if st.button("💾 Save to Library", type="primary", use_container_width=True):
                sp = result.get('suggested_piece', {})
                add_record(
                    source_url=result.get('url', ''),
                    source_name=result.get('source_name', ''),
                    author=result.get('author', ''),
                    title=result.get('title', ''),
                    synthesis=json.dumps({
                        "tldr": result.get("tldr", ""),
                        "key_points": result.get("key_points", []),
                        "why_timely": result.get("why_timely", "")
                    }),
                    key_quotes=result.get('key_quotes', []),
                    content_angle=json.dumps(sp),
                    tier=tier, themes=themes,
                    raw_content=result.get('raw_content', '')
                )
                st.success("Saved!")
                st.session_state.deep_synthesis = None
                st.rerun()


# ═══════════════════════════════════════════════════════
# TAB 4 — LIBRARY
# ═══════════════════════════════════════════════════════
with tabs[3]:
    st.subheader("Intelligence Library")

    c1, c2, c3 = st.columns(3)
    with c1:
        f_status = st.selectbox("Status", ["All", "synthesized", "drafting", "draft_saved", "published"])
    with c2:
        f_tier = st.selectbox("Tier", ["All", "1 - Full Article", "2 - Blog Post", "3 - Quick Reaction"])
    with c3:
        f_theme = st.selectbox("Theme", ["All"] + (stats.get("themes") or []))

    library = load_library()
    records = library["records"]

    if f_status != "All":
        records = [r for r in records if r["status"] == f_status]
    if f_tier != "All":
        t = int(f_tier[0])
        records = [r for r in records if r["tier"] == t]
    if f_theme != "All":
        records = [r for r in records if f_theme in r.get("themes", [])]

    st.caption(f"Showing {len(records)} records")

    for record in reversed(records):
        tier = record["tier"]
        emoji = "🟡" if tier == 1 else ("🟣" if tier == 2 else "🔵")
        draft_badge = " 💾" if record.get("draft_content") else ""
        with st.expander(f"{emoji} T{tier}{draft_badge} | {record['title'][:65]} | #{record['id']}"):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.caption(f"**{record['author']}** | {record['source_name']} | {record['date_found'][:10]}")
                try:
                    syn = json.loads(record['synthesis'])
                    st.markdown(f"**TLDR:** {syn.get('tldr', '')}")
                    if syn.get('key_points'):
                        st.markdown("**Key Points:**")
                        for p in syn['key_points']:
                            st.markdown(f"• {p}")
                except Exception:
                    st.markdown(f"{record['synthesis'][:300]}")
                try:
                    sp = json.loads(record.get('content_angle', '{}'))
                    if sp.get('what_to_write'):
                        st.markdown("---")
                        st.markdown(f"**Write:** {sp.get('what_to_write', '')}")
                        if sp.get('coined_term'):
                            st.markdown(f"**Coined term:** _{sp.get('coined_term')}_")
                except Exception:
                    pass
                st.markdown(f"[Source ↗]({record['source_url']})")
            with c2:
                st.markdown(f"**Status:** {record['status']}")
                st.markdown(f"**Themes:** {', '.join(record.get('themes', []))}")
                if record.get("draft_saved_at"):
                    st.caption(f"Draft saved: {record['draft_saved_at'][:10]}")
                if st.button("✍️ Write", key=f"lib_{record['id']}"):
                    st.session_state.active_record = record
                    st.rerun()


# ═══════════════════════════════════════════════════════
# TAB 5 — WRITE
# ═══════════════════════════════════════════════════════
with tabs[4]:
    st.subheader("Write Content")

    library = load_library()
    ready = [r for r in library["records"]
             if r["status"] in ["synthesized", "drafting", "draft_saved"]]

    if not ready:
        st.info("No records ready. Add content in Daily Brief or Add Content tabs first.")
    else:
        options = {f"#{r['id']} T{r['tier']} — {r['title'][:55]}": r for r in reversed(ready)}

        default_idx = 0
        if st.session_state.active_record:
            active_id = st.session_state.active_record.get("id")
            for i, key in enumerate(options.keys()):
                if f"#{active_id}" in key:
                    default_idx = i
                    break

        selected_key = st.selectbox("Select record", list(options.keys()), index=default_idx)
        record = options[selected_key]
        st.session_state.active_record = record

        # ── BUG FIX: Clear POV fields when record changes ────────────────────
        if st.session_state.get("last_write_record_id") != record["id"]:
            st.session_state["last_write_record_id"] = record["id"]
            for key in ["q1", "q2", "q3", "q4"]:
                st.session_state[key] = ""
            st.session_state.chat_messages = []
            st.session_state.linkedin_draft = ""
            st.session_state.pop("img_header", None)
            st.session_state.pop("img_linkedin", None)
            st.session_state.pop("img_suggestions", None)
            st.session_state.pop("img_prompt_val", None)
            # Pre-populate draft if record has a saved draft
            st.session_state.draft = record.get("draft_content", "")

        try:
            syn = json.loads(record["synthesis"])
        except Exception:
            syn = {"tldr": record.get("synthesis", ""), "key_points": [], "why_timely": ""}

        try:
            sp = json.loads(record.get("content_angle", "{}"))
        except Exception:
            sp = {}

        col_left, col_right = st.columns([1, 1])

        # ── LEFT: Article context + Research Chat ────────────────────────────
        with col_left:
            st.markdown(f"**{record['title']}**")
            st.caption(f"{record['author']} | {record['source_name']}")

            if record.get("draft_content"):
                st.success("💾 Saved draft loaded — edit or regenerate below")

            st.markdown(f"**TLDR:** {syn.get('tldr', '')}")

            with st.expander("Key Points"):
                for p in syn.get("key_points", []):
                    st.markdown(f"• {p}")

            if sp:
                with st.expander("Suggested Piece"):
                    st.markdown(f"**What:** {sp.get('what_to_write', '')}")
                    st.markdown(f"**Why now:** {sp.get('why_now', '')}")
                    st.markdown(f"**Audience:** {sp.get('audience', '')}")
                    st.markdown(f"**Your angle:** {sp.get('usman_angle', '')}")
                    if sp.get("coined_term"):
                        st.markdown(f"**Coined term:** _{sp.get('coined_term')}_")

            if st.button("🔬 Deep Synthesis (Sonnet)", use_container_width=True):
                with st.spinner("Running deep synthesis..."):
                    result = process_url(record["source_url"], depth="deep")
                    if result["success"]:
                        st.session_state.deep_synthesis = result
                        update_record_status(record["id"], "drafting")
                        st.success("Deep synthesis done!")
                        st.rerun()

            st.markdown("---")
            st.markdown("### 💬 Research Chat")
            st.caption("Develop your angle here — insights feed into the draft")

            chat_context = f"""
Article: {record['title']}
Author: {record['author']} | Source: {record['source_name']}
TLDR: {syn.get('tldr', '')}
Key points: {chr(10).join(f'- {p}' for p in syn.get('key_points', []))}
Usman's background: Field CISO at Google Cloud, 17 years security,
advises Fortune 500 boards and federal agencies on AI security risk.
"""
            for msg in st.session_state.chat_messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            if chat_prompt := st.chat_input("Ask about this topic..."):
                st.session_state.chat_messages.append({"role": "user", "content": chat_prompt})
                with st.chat_message("user"):
                    st.markdown(chat_prompt)
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        chat_resp = client.messages.create(
                            model="claude-sonnet-4-5",
                            max_tokens=600,
                            system=f"""You are a research assistant helping Usman Chaudhary
form his perspective on a security topic. Be direct, specific, cite real sources when you
reference them, and draw on enterprise CISO realities. Help him find angles others miss.

ARTICLE CONTEXT:
{chat_context}""",
                            messages=[{"role": m["role"], "content": m["content"]}
                                      for m in st.session_state.chat_messages]
                        )
                        reply = chat_resp.content[0].text
                        st.markdown(reply)
                st.session_state.chat_messages.append({"role": "assistant", "content": reply})

            if st.session_state.chat_messages:
                if st.button("🗑️ Clear chat", use_container_width=True):
                    st.session_state.chat_messages = []
                    st.rerun()

        # ── RIGHT: Draft generation ──────────────────────────────────────────
        with col_right:
            st.markdown("### ✍️ Draft")

            output_format = st.selectbox(
                "Output format",
                [
                    "📄 Tier 1 — Full article for usmanc.com (1200-1800 words)",
                    "🟣 Tier 2 — Blog post (500-800 words)",
                    "🔵 Tier 3 — Quick reaction (top 3 takeaways, link in comments)"
                ]
            )

            is_t1 = "Tier 1" in output_format
            is_t2 = "Tier 2" in output_format
            uses_research = is_t1 or is_t2

            st.markdown("**Your POV** _(optional but improves output significantly)_")

            q1 = st.text_area(
                "Your take from CISO experience?",
                placeholder="I've seen this play out at Fortune 500s where...",
                height=60, key="q1"
            )
            q2 = st.text_area(
                "Angle others are missing?",
                placeholder="Everyone focuses on X but nobody talks about Y...",
                height=60, key="q2"
            )

            if uses_research:
                source_count = "4-6" if is_t1 else "2-3"
                q4 = st.text_area(
                    f"Research direction — Claude will find {source_count} sources",
                    placeholder="Search for NIST PQC guidelines, find enterprise zero-trust agent identity examples, look for recent breaches...",
                    height=80, key="q4"
                )
            else:
                q4 = ""

            if is_t1:
                q3 = st.text_area(
                    "What should CISOs actually DO?",
                    placeholder="The first thing I'd tell my CISO peers is...",
                    height=60, key="q3"
                )
            else:
                q3 = ""

            if st.button("✍️ Generate Draft", type="primary", use_container_width=True):

                if is_t1:
                    tier_instruction = (
                        "Write a TIER 1 full article for usmanc.com. "
                        "Aim for 1200-1800 words — prioritise completing all sections over hitting a word count. "
                        "Comprehensive, authoritative, fully cited. Never truncate mid-section."
                    )
                    max_tokens = 7000
                elif is_t2:
                    tier_instruction = (
                        "Write a TIER 2 standalone blog post. "
                        "Target 500-800 words. One strong angle, fully cited."
                    )
                    max_tokens = 2000
                else:
                    tier_instruction = (
                        "Write a TIER 3 quick reaction post. 150-300 words. "
                        "End with 'Link to the original in the comments.' before hashtags."
                    )
                    max_tokens = 800

                deep = st.session_state.deep_synthesis or {}
                context_parts = [
                    f"SEED ARTICLE: {record['title']}",
                    f"AUTHOR: {record['author']} | SOURCE: {record['source_name']}",
                    f"URL: {record['source_url']}",
                    f"TLDR: {syn.get('tldr', '')}",
                    "KEY POINTS:\n" + "\n".join(f"- {p}" for p in syn.get("key_points", [])),
                ]
                if deep.get("core_argument"):
                    context_parts.append(f"CORE ARGUMENT: {deep['core_argument']}")
                if deep.get("key_stats"):
                    context_parts.append("KEY STATS:\n" + "\n".join(f"- {s}" for s in deep["key_stats"]))
                if sp.get("coined_term"):
                    context_parts.append(f"COINED TERM TO USE: {sp['coined_term']}")

                pov_parts = []
                if q1: pov_parts.append(f"My CISO experience: {q1}")
                if q2: pov_parts.append(f"Angle others miss: {q2}")
                if q3: pov_parts.append(f"What CISOs should do: {q3}")

                chat_insights = ""
                if st.session_state.chat_messages:
                    chat_insights = "\nINSIGHTS FROM RESEARCH CHAT:\n"
                    for m in st.session_state.chat_messages[-6:]:
                        chat_insights += f"{m['role'].upper()}: {m['content'][:300]}\n"

                if uses_research:
                    source_count = "4-6" if is_t1 else "2-3"
                    research_directive = q4 or (
                        f"Find {source_count} authoritative recent sources on this topic "
                        f"(2024-2026 preferred: industry reports, research papers, major publications)"
                    )
                    prompt = f"""{tier_instruction}

ARTICLE CONTEXT:
{chr(10).join(context_parts)}

USMAN'S POV:
{chr(10).join(pov_parts) if pov_parts else "Use the suggested angle from the synthesis."}
{chat_insights}

RESEARCH TASK:
Before writing, search the web for {source_count} authoritative sources.
Direction: {research_directive}

CITATION REQUIREMENTS (mandatory):
- Cite every specific claim: "[Author/Publication] found..." or "(Source: Publication, Year)"
- Flag your original reasoning: "From my CISO experience..." or "In my view..."
- Add a numbered 📚 {"References" if is_t1 else "Sources"} section at the end
- Usman's professional reputation depends on every claim being sourced

Now search, then write."""
                else:
                    prompt = f"""{tier_instruction}

ARTICLE CONTEXT:
{chr(10).join(context_parts)}

USMAN'S POV:
{chr(10).join(pov_parts) if pov_parts else "Use the suggested angle from the synthesis."}
{chat_insights}

Credit the source article by name. Follow the voice and format exactly."""

                spinner_msg = "Researching and writing..." if uses_research else "Writing..."
                with st.spinner(spinner_msg):
                    if uses_research:
                        draft_text = generate_with_research(prompt, USMAN_VOICE, max_tokens)
                    else:
                        response = client.messages.create(
                            model="claude-sonnet-4-5",
                            max_tokens=max_tokens,
                            system=USMAN_VOICE,
                            messages=[{"role": "user", "content": prompt}]
                        )
                        draft_text = response.content[0].text

                st.session_state.draft = draft_text
                update_record_status(record["id"], "drafting")

            # ── Draft output ─────────────────────────────────────────────────
            if st.session_state.draft:
                edit_tab, preview_tab = st.tabs(["✏️ Edit", "👁️ Preview"])

                with edit_tab:
                    edited = st.text_area(
                        "Edit your draft",
                        value=st.session_state.draft,
                        height=420
                    )

                with preview_tab:
                    st.markdown(st.session_state.draft)
                    edited = st.session_state.draft  # use unedited if only previewing

                # Row 1: Copy + Save Draft
                c1, c2 = st.columns(2)
                with c1:
                    copy_html = """
<textarea id="draft-copy" style="opacity:0;position:absolute;top:-9999px"></textarea>
<button id="copy-btn" onclick="
  var t=document.getElementById('draft-copy');
  t.select();document.execCommand('copy');
  document.getElementById('copy-btn').innerText='✅ Copied!';
  setTimeout(function(){{document.getElementById('copy-btn').innerText='📋 Copy to Clipboard'}},2000)
" style="
  background:#FF4B4B;color:white;border:none;padding:9px 0;
  border-radius:6px;cursor:pointer;width:100%;font-size:14px;font-weight:600
">📋 Copy to Clipboard</button>
<script>
document.getElementById('draft-copy').value = {draft_json};
</script>""".format(draft_json=json.dumps(edited))
                    components.html(copy_html, height=42)

                with c2:
                    if st.button("💾 Save Draft (file for later)", use_container_width=True):
                        save_draft(record["id"], edited)
                        st.success("Draft saved — come back when timing is right.")
                        st.rerun()

                # HTML export (embeds header image if generated)
                html_output = draft_to_html(
                    edited, record,
                    header_image_bytes=st.session_state.get("img_header")
                )
                slug = record['title'][:40].lower()
                slug = ''.join(c if c.isalnum() else '-' for c in slug).strip('-')
                st.download_button(
                    label="⬇️ Export as HTML (for usmanc.com)",
                    data=html_output.encode("utf-8"),
                    file_name=f"{slug}.html",
                    mime="text/html",
                    use_container_width=True
                )

                # Row 2: Regenerate + Published
                c3, c4 = st.columns(2)
                with c3:
                    if st.button("🔄 Regenerate", use_container_width=True):
                        st.session_state.draft = ""
                        st.rerun()
                with c4:
                    if st.button("✅ Mark Published", use_container_width=True):
                        update_record_status(record["id"], "published")
                        st.session_state.draft = ""
                        st.success("Marked published!")
                        st.rerun()

                # ── LinkedIn Content Pack ────────────────────────────────────
                st.markdown("---")
                st.markdown("### 📦 LinkedIn Content Pack")
                st.caption("5 different angles + image prompts + posting schedule")

                if st.button("📦 Generate LinkedIn Content Pack", type="primary", use_container_width=True):
                    pack_prompt = f"""Generate a LinkedIn Content Pack for this article.
Create 5 standalone posts — each different angle, each 150-250 words, each with its own image concept.

ARTICLE TITLE: {record['title']}
ARTICLE (first 2000 words):
{edited[:2000]}

AUTHOR: Usman Chaudhary — Field CISO, Google Cloud. 17 years security. Advises Fortune 500 boards and federal agencies.

Generate exactly 5 posts in this format for each:

---
**ANGLE [N]: [Angle Name]**
**Best posting day:** Day [1/3/7/14/21] after article publishes
**Target audience:** [Who this angle speaks to]

**POST:**
[Full LinkedIn post — 150-250 words, Usman's voice, emoji bullets, hashtags at end]

**IMAGE CONCEPT:**
[2-3 sentences describing the visual. Professional, abstract, no text in image.
Style: [choose one: photorealistic/illustrated/data visualization/conceptual art]
Colors: [suggest palette that fits the mood]
Suggested prompt for DALL-E 3 or Midjourney: "[exact prompt to paste in]"]

---

FIVE ANGLES TO COVER (in this order):
1. 🎯 THE BOARD CASE — Frame this as a liability/risk story. Audience: executives and boards.
2. ⚙️ THE PRACTITIONER REALITY — What security teams face day-to-day. Tactical. Audience: security engineers and architects.
3. 🚨 THE COST OF WAITING — What happens if you ignore this. Urgency framing. Audience: CISOs who haven't acted.
4. 🔄 THE CONTRARIAN — What everyone else is getting wrong. Provocative. Audience: thought leaders and skeptics.
5. 📖 THE STORY — Open with a specific scenario or anecdote that makes the abstract concrete. Audience: broad professional.

After the 5 posts, add:

---
**POSTING SCHEDULE**
- Day 1: Article + Angle 1 (Board Case)
- Day 3: Angle 2 (Practitioner)
- Day 7: Angle 3 (Cost of Waiting)
- Day 14: Angle 4 (Contrarian)
- Day 21: Angle 5 (Story) + link back to article

**FEATURED IMAGE PROMPT (for blog header):**
[DALL-E 3 prompt for 1792x1024 blog header. Abstract, professional, no text. Evokes the article's core theme.]"""

                    with st.spinner("Generating 5 LinkedIn angles + image prompts..."):
                        pack_resp = client.messages.create(
                            model="claude-sonnet-4-5",
                            max_tokens=4000,
                            messages=[{"role": "user", "content": pack_prompt}]
                        )
                        st.session_state.linkedin_draft = pack_resp.content[0].text

                if st.session_state.linkedin_draft:
                    st.markdown("#### Your Content Pack")
                    li_edited = st.text_area(
                        "Content pack (edit before use)",
                        value=st.session_state.linkedin_draft,
                        height=600
                    )
                    li_copy_html = """
<textarea id="li-copy" style="opacity:0;position:absolute;top:-9999px"></textarea>
<button id="li-btn" onclick="
  var t=document.getElementById('li-copy');
  t.select();document.execCommand('copy');
  document.getElementById('li-btn').innerText='✅ Copied!';
  setTimeout(function(){{document.getElementById('li-btn').innerText='📋 Copy Content Pack'}},2000)
" style="
  background:#0077B5;color:white;border:none;padding:9px 0;
  border-radius:6px;cursor:pointer;width:100%;font-size:14px;font-weight:600
">📋 Copy Content Pack</button>
<script>
document.getElementById('li-copy').value = {li_json};
</script>""".format(li_json=json.dumps(li_edited))
                    components.html(li_copy_html, height=42)
                    if IMAGEN_AVAILABLE:
                        st.caption("💡 Image prompts are included in the pack above — or use the Image Generator below.")
                    else:
                        st.caption("💡 Image prompts are included in the pack above — paste them into DALL-E (ChatGPT Plus) or Midjourney to generate the visuals.")

                # ── Image Generator ──────────────────────────────────────────
                if IMAGEN_AVAILABLE and st.session_state.draft:
                    st.markdown("---")
                    st.markdown("### 🎨 Image Generator")
                    st.caption("Powered by Google Imagen 3")

                    # Suggest contextual image prompts from the draft
                    if st.button("✨ Suggest Image Prompts from Draft", use_container_width=True):
                        with st.spinner("Reading your article and generating image concepts..."):
                            # Build context from the actual draft
                            try:
                                syn_data = json.loads(record.get("synthesis", "{}"))
                                tldr = syn_data.get("tldr", "")
                            except Exception:
                                tldr = str(record.get("synthesis", ""))[:200]

                            try:
                                sp_data = json.loads(record.get("content_angle", "{}"))
                                coined = sp_data.get("coined_term", "")
                            except Exception:
                                coined = ""

                            suggest_prompt = f"""Generate 3 distinct image prompts for a blog article.
Each prompt will be used with Google Imagen 3 to create a professional blog header image.

ARTICLE TITLE: {record.get('title', '')}
TLDR: {tldr}
COINED TERM: {coined if coined else 'N/A'}
DRAFT EXCERPT (first 500 chars): {st.session_state.draft[:500]}

Rules for each prompt:
- No text, logos, or words in the image
- Professional, corporate aesthetic matching dark/gold color scheme
- Abstract or conceptual — not literal illustration
- Photorealistic or high-quality digital art
- Wide format (16:9 landscape)
- Must directly evoke the article's core concept

Return exactly 3 prompts, numbered 1-3.
Each prompt on its own line, starting with the number.
No preamble, no explanation — just the 3 prompts."""

                            suggest_resp = client.messages.create(
                                model="claude-sonnet-4-5",
                                max_tokens=600,
                                messages=[{"role": "user", "content": suggest_prompt}]
                            )
                            st.session_state["img_suggestions"] = suggest_resp.content[0].text

                    if st.session_state.get("img_suggestions"):
                        st.markdown("**Pick a concept:**")
                        suggestions = [
                            line.strip().lstrip("123. ").strip()
                            for line in st.session_state["img_suggestions"].split("\n")
                            if line.strip() and line.strip()[0].isdigit()
                        ]
                        selected = st.radio(
                            "Image concepts",
                            suggestions,
                            label_visibility="collapsed"
                        ) if suggestions else None
                        if selected and st.button("Use this concept →", use_container_width=True):
                            st.session_state["img_prompt_val"] = selected
                            st.rerun()

                    img_prompt = st.text_area(
                        "Image prompt (edit or write your own)",
                        value=st.session_state.get("img_prompt_val", ""),
                        placeholder="Click 'Suggest Image Prompts' above to auto-generate from your draft, or write your own.",
                        height=100,
                        key="img_prompt"
                    )

                    img_col1, img_col2 = st.columns(2)
                    with img_col1:
                        if st.button("🖼️ Blog Header (16:9)", use_container_width=True):
                            if img_prompt:
                                with st.spinner("Generating blog header..."):
                                    img_bytes = generate_image(img_prompt, aspect_ratio="16:9")
                                if img_bytes:
                                    st.session_state["img_header"] = img_bytes
                                    st.rerun()
                    with img_col2:
                        if st.button("📱 LinkedIn Card (1:1)", use_container_width=True):
                            if img_prompt:
                                with st.spinner("Generating LinkedIn card..."):
                                    img_bytes = generate_image(img_prompt, aspect_ratio="1:1")
                                if img_bytes:
                                    st.session_state["img_linkedin"] = img_bytes
                                    st.rerun()

                    if st.session_state.get("img_header"):
                        st.markdown("**Blog Header**")
                        st.image(st.session_state["img_header"], use_column_width=True)
                        st.download_button(
                            "⬇️ Download Header",
                            data=st.session_state["img_header"],
                            file_name=f"header_{record['id']}.png",
                            mime="image/png",
                            use_container_width=True
                        )

                    if st.session_state.get("img_linkedin"):
                        st.markdown("**LinkedIn Card**")
                        st.image(st.session_state["img_linkedin"], use_column_width=True)
                        st.download_button(
                            "⬇️ Download LinkedIn Card",
                            data=st.session_state["img_linkedin"],
                            file_name=f"linkedin_{record['id']}.png",
                            mime="image/png",
                            use_container_width=True
                        )

                elif not IMAGEN_AVAILABLE and st.session_state.draft:
                    st.markdown("---")
                    st.info("🎨 Add `GOOGLE_API_KEY` to your `.env` to enable image generation with Google Imagen 3.")


# ═══════════════════════════════════════════════════════
# TAB 6 — SEARCH & BROWSE
# ═══════════════════════════════════════════════════════
with tabs[5]:
    st.subheader("Search & Browse by Theme")

    query = st.text_input("🔍 Search by keyword, topic, or theme",
                          placeholder="agentic SOC, zero trust, LLM security")

    library = load_library()
    all_records = library["records"]

    all_themes = sorted(set(t for r in all_records for t in r.get("themes", [])))
    published = [r for r in all_records if r["status"] == "published"]
    intelligence = [r for r in all_records if r["status"] != "published"]

    theme_counts = {}
    for theme in all_themes:
        intel_count = len([r for r in intelligence if theme in r.get("themes", [])])
        pub_count = len([r for r in published if theme in r.get("themes", [])])
        theme_counts[theme] = {"intel": intel_count, "published": pub_count}

    if not query:
        st.markdown("### 📂 Browse by Theme")
        st.caption("Click a theme to see all records and written pieces")

        cols = st.columns(3)
        for i, theme in enumerate(all_themes):
            with cols[i % 3]:
                counts = theme_counts[theme]
                label = f"**{theme}** — {counts['intel']} sources · {counts['published']} written"
                if st.button(label, key=f"theme_{theme}", use_container_width=True):
                    st.session_state["selected_theme"] = theme

        selected_theme = st.session_state.get("selected_theme")
        if selected_theme:
            st.markdown("---")
            st.markdown(f"### 🏷️ {selected_theme.title()}")

            theme_intel = [r for r in intelligence if selected_theme in r.get("themes", [])]
            theme_pub = [r for r in published if selected_theme in r.get("themes", [])]

            if len(theme_intel) > 1:
                if st.button(f"🔗 Cross-synthesize {len(theme_intel)} sources on '{selected_theme}'", type="primary"):
                    with st.spinner("Synthesizing with Sonnet..."):
                        summaries = []
                        for r in theme_intel[:6]:
                            try:
                                syn = json.loads(r['synthesis'])
                                summaries.append(f"- [{r['author']} / {r['source_name']}]: {syn.get('tldr', '')}")
                            except Exception:
                                summaries.append(f"- [{r['author']}]: {r['synthesis'][:100]}")

                        cross_resp = client.messages.create(
                            model="claude-sonnet-4-5",
                            max_tokens=800,
                            messages=[{"role": "user",
                                       "content": f"""Across {len(theme_intel)} sources on '{selected_theme}':
1. What is the consensus view?
2. Where do sources disagree?
3. What is the emerging trend?
4. What angle would a Field CISO at Google Cloud uniquely add?
5. Suggest a coined term for the combined insight.

SOURCES:
{chr(10).join(summaries)}"""}]
                        )
                        st.markdown("#### 🔗 Cross-Article Synthesis")
                        st.markdown(cross_resp.content[0].text)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"#### 📰 Intelligence Sources ({len(theme_intel)})")
                if theme_intel:
                    for r in reversed(theme_intel):
                        tier = r["tier"]
                        emoji = "🟡" if tier == 1 else ("🟣" if tier == 2 else "🔵")
                        with st.expander(f"{emoji} {r['title'][:55]} | #{r['id']}"):
                            st.caption(f"{r['author']} | {r['source_name']} | {r['date_found'][:10]}")
                            try:
                                syn = json.loads(r['synthesis'])
                                st.markdown(f"**TLDR:** {syn.get('tldr', '')}")
                            except Exception:
                                st.markdown(r['synthesis'][:150])
                            st.markdown(f"[Source ↗]({r['source_url']})")
                            if st.button("✍️ Write", key=f"theme_w_{r['id']}"):
                                st.session_state.active_record = r
                                st.rerun()
                else:
                    st.caption("No sources yet for this theme.")

            with col2:
                st.markdown(f"#### ✍️ Your Published Content ({len(theme_pub)})")
                if theme_pub:
                    for r in reversed(theme_pub):
                        with st.expander(f"✅ {r['title'][:55]}"):
                            st.caption(f"Published | {r['date_found'][:10]}")
                            try:
                                syn = json.loads(r['synthesis'])
                                st.markdown(f"**TLDR:** {syn.get('tldr', '')}")
                            except Exception:
                                st.markdown(r['synthesis'][:150])
                            if r["tier"] == 1:
                                st.markdown("📄 Published on usmanc.com")
                            elif r["tier"] == 2:
                                st.markdown("🟣 Published on LinkedIn")
                            else:
                                st.markdown("🔵 Published as LinkedIn reaction")
                else:
                    st.info(f"Nothing written yet on '{selected_theme}'. You have {len(theme_intel)} sources ready.")
                    if theme_intel:
                        if st.button(f"Write about {selected_theme} now →", use_container_width=True):
                            st.session_state.active_record = theme_intel[0]
                            st.rerun()

    if query:
        results = search_library(query)
        st.caption(f"Found {len(results)} records for '{query}'")

        if len(results) > 1:
            if st.button(f"🔗 Cross-synthesize all {len(results)} results", type="primary"):
                with st.spinner("Synthesizing across articles with Sonnet..."):
                    summaries = []
                    for r in results[:6]:
                        try:
                            syn = json.loads(r['synthesis'])
                            summaries.append(f"- [{r['author']} / {r['source_name']}]: {syn.get('tldr', '')}")
                        except Exception:
                            summaries.append(f"- [{r['author']}]: {r['synthesis'][:100]}")

                    cross_resp = client.messages.create(
                        model="claude-sonnet-4-5",
                        max_tokens=800,
                        messages=[{"role": "user",
                                   "content": f"""Across these {len(results)} articles on '{query}':
1. What is the consensus view?
2. Where do sources disagree?
3. What is the emerging trend?
4. What angle would a Field CISO at Google Cloud uniquely add?
5. Suggest a coined term for the combined insight.

SOURCES:
{chr(10).join(summaries)}"""}]
                    )
                    st.markdown("### 🔗 Cross-Article Synthesis")
                    st.markdown(cross_resp.content[0].text)

        search_intel = [r for r in results if r["status"] != "published"]
        search_pub = [r for r in results if r["status"] == "published"]

        if search_intel:
            st.markdown("#### 📰 Intelligence Sources")
            for r in search_intel:
                tier = r["tier"]
                emoji = "🟡" if tier == 1 else ("🟣" if tier == 2 else "🔵")
                with st.expander(f"{emoji} T{tier} | {r['title'][:65]} | #{r['id']}"):
                    st.caption(f"{r['author']} | {r['source_name']} | {r['date_found'][:10]}")
                    try:
                        syn = json.loads(r['synthesis'])
                        st.markdown(f"**TLDR:** {syn.get('tldr', '')}")
                        for p in syn.get('key_points', []):
                            st.markdown(f"• {p}")
                    except Exception:
                        st.markdown(r['synthesis'][:200])
                    st.markdown(f"[Source ↗]({r['source_url']})")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.caption(f"Themes: {', '.join(r.get('themes', []))}")
                    with c2:
                        if st.button("✍️ Write", key=f"sq_{r['id']}"):
                            st.session_state.active_record = r
                            st.rerun()

        if search_pub:
            st.markdown("#### ✍️ Your Published Content")
            for r in search_pub:
                with st.expander(f"✅ {r['title'][:65]}"):
                    st.caption(f"Published | Tier {r['tier']} | {r['date_found'][:10]}")
                    try:
                        syn = json.loads(r['synthesis'])
                        st.markdown(f"**TLDR:** {syn.get('tldr', '')}")
                    except Exception:
                        st.markdown(r['synthesis'][:150])

# ═══════════════════════════════════════════════════════
# TAB 7 — SAVED BRIEFS
# ═══════════════════════════════════════════════════════
with tabs[6]:
    st.subheader("📅 Saved Intelligence Briefs")
    st.caption("Your daily briefs — last 14 days")

    briefs = list_saved_briefs()

    if not briefs:
        st.info("No briefs saved yet. Generate your first brief in the Daily Brief tab.")
    else:
        for b in briefs:
            date_label = b.get("date", b.get("id", "Unknown date"))
            gen_time = b.get("generated_at", "")[:16] if b.get("generated_at") else ""
            is_today = b.get("id") == datetime.now().strftime("%Y-%m-%d")
            label = f"{'🟢 Today — ' if is_today else ''}{date_label}"
            if gen_time:
                label += f"  `{gen_time}`"

            with st.expander(label, expanded=is_today):
                if b.get("brief_text"):
                    st.markdown(b["brief_text"])
                    if b.get("profile"):
                        st.caption(f"Generated for: {' · '.join(b['profile'])}")
                else:
                    st.caption("Brief text not available")

