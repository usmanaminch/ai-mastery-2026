import streamlit as st
import anthropic
from dotenv import load_dotenv
from datetime import datetime
import json
from scraper import process_url, process_pasted_text
from sheets import get_unprocessed_links, get_all_links, mark_as_synthesized
from firebase_library import (
    add_record, load_library, get_library_stats,
    get_records_by_status, search_library, update_record_status, url_exists,
    get_pending_paste, add_pending_paste, remove_pending_paste
)

load_dotenv()

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
- Emoji bullets for scannability
- Short punchy paragraphs, no corporate fluff
- Technical enough to be credible, accessible for boards
- Always cite sources inline
- End with LET'S call to action

TIER 1 — Full article (800-1200 words):
🚨 Emoji headline with coined term
The Challenge — name and frame the problem
The Problem's True Size — make it urgent and real
The Solution — actionable numbered framework
Long-term vision
Sources cited inline
Hashtags + engagement question

TIER 2 — Substantive LinkedIn post (300-500 words):
🔥 Strong hook with coined term
Context — why this matters now
3-4 key insights with your CISO angle
What CISOs should do — specific action
"Link to source in the comments."
Hashtags

TIER 3 — Quick reaction post (150-300 words):
Hook line with emoji
"[Author] at [Publication] just published something worth reading."
"My top 3 CISO takeaways:"
⚖️ Takeaway 1 — named concept
⏱️ Takeaway 2 — named concept
🛡️ Takeaway 3 — named concept
"Link to the original in the comments."
LET'S closing line
Hashtags

NEVER reproduce large portions of source text.
Always distinguish your analysis from source claims.
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

tabs = st.tabs(["📰 Daily Brief", "📋 Reading List", "➕ Add Content", "📚 Library", "✍️ Write", "🔍 Search"])

# ═══════════════════════════════════════════════════════
# TAB 1 — DAILY BRIEF
# ═══════════════════════════════════════════════════════
with tabs[0]:
    st.subheader(f"Intelligence Brief — {datetime.now().strftime('%A, %B %d, %Y')}")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 🔥 Process New Content")
        urls_input = st.text_area(
            "Paste URLs to process (one per line)",
            height=120,
            placeholder="https://cloud.google.com/blog/...\nhttps://youtube.com/watch?v=..."
        )

        if st.button("🚀 Process All URLs", type="primary", use_container_width=True):
            if urls_input.strip():
                urls = [u.strip() for u in urls_input.strip().split('\n') if u.strip()]
                st.session_state.processing_status = []
                st.session_state.paste_needed = []
                st.session_state.last_processed_results = []

                progress = st.progress(0)
                status_box = st.empty()

                for i, url in enumerate(urls):
                    # FIX 3: Skip duplicates
                    if url_exists(url):
                        st.session_state.processing_status.append({
                            "url": url, "status": "duplicate",
                            "title": "Already in library"
                        })
                        progress.progress((i + 1) / len(urls))
                        continue

                    status_box.info(f"Processing {i+1}/{len(urls)}: {url[:60]}...")
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
                        st.session_state.processing_status.append({
                            "url": url, "status": "success",
                            "title": result.get("title", ""),
                            "tier": sp.get("recommended_tier", result.get("tier", 3)),
                            "record_id": record["id"],
                            "tldr": result.get("tldr", ""),
                            "key_points": result.get("key_points", []),
                            "coined_term": sp.get("coined_term", ""),
                            "what_to_write": sp.get("what_to_write", ""),
                            "why_now": sp.get("why_now", ""),
                        })
                        st.session_state.last_processed_results.append(record)
                    else:
                        st.session_state.processing_status.append({
                            "url": url, "status": "needs_paste",
                            "error": result.get("error", "")
                        })
                        st.session_state.paste_needed.append(url)

                    progress.progress((i + 1) / len(urls))

                status_box.empty()
                st.success(f"Done! Processed {len(urls)} URLs.")
                st.rerun()

        # FIX 2: Show full synthesis inline after processing
        if st.session_state.processing_status:
            st.markdown("### 📊 Processing Results")
            for item in st.session_state.processing_status:
                if item["status"] == "success":
                    tier = item.get("tier", 3)
                    emoji = "🟡" if tier == 1 else ("🟣" if tier == 2 else "🔵")
                    with st.expander(
                        f"{emoji} **{item.get('title', '')[:60]}** — Tier {tier} | Record #{item.get('record_id')}",
                        expanded=True
                    ):
                        st.markdown(f"**TLDR:** {item.get('tldr', '')}")
                        if item.get('key_points'):
                            st.markdown("**Key Points:**")
                            for p in item['key_points']:
                                st.markdown(f"• {p}")
                        if item.get('what_to_write'):
                            st.markdown(f"**Suggested:** {item.get('what_to_write', '')}")
                        if item.get('coined_term'):
                            st.markdown(f"**Coined term:** _{item.get('coined_term')}_")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("✍️ Write now", key=f"write_now_{item['record_id']}"):
                                library = load_library()
                                rec = next((r for r in library["records"] if r["id"] == item["record_id"]), None)
                                if rec:
                                    st.session_state.active_record = rec
                                    st.rerun()
                elif item["status"] == "duplicate":
                    st.info(f"⏭️ Already in library: `{item['url'][:60]}`")
                else:
                    st.warning(f"⚠️ Needs paste: `{item['url'][:60]}`")

        # Paste needed — FIX 1: title/author/publisher optional
        if st.session_state.paste_needed:
            st.markdown("### ⚠️ Paste content for blocked URLs")
            for url in st.session_state.paste_needed:
                with st.expander(f"📋 {url[:70]}"):
                    pasted = st.text_area(
                        "Paste article content here",
                        key=f"paste_{url}", height=200
                    )
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        p_title = st.text_input("Title (optional)", key=f"title_{url}")
                    with c2:
                        p_author = st.text_input("Author (optional)", key=f"author_{url}")
                    with c3:
                        p_source = st.text_input("Publication (optional)", key=f"source_{url}")

                    # FIX 1: Process works even without title/author/publisher
                    if st.button("Process pasted content", key=f"btn_{url}"):
                        if pasted:
                            # Smart defaults if fields left blank
                            title = p_title or url.split('/')[-2].replace('-', ' ').title() if '/' in url else "Untitled"
                            author = p_author or "Unknown"
                            source = p_source or url.split('/')[2].replace('www.', '') if '//' in url else "Unknown"

                            result = process_pasted_text(
                                text=pasted, url=url,
                                source_name=source,
                                author=author,
                                title=title,
                                depth="quick"
                            )
                            if result["success"]:
                                sp = result.get("suggested_piece", {})
                                record = add_record(
                                    source_url=url,
                                    source_name=source,
                                    author=author,
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
                                st.success(f"Added as Record #{record['id']}!")
                                st.markdown(f"**TLDR:** {result.get('tldr', '')}")
                                st.session_state.paste_needed.remove(url)
                                st.rerun()
                        else:
                            st.error("Please paste the article content first.")

    with col2:
        st.markdown("### 📊 Library Stats")
        st.metric("Total", stats["total"])
        st.metric("Tier 1 Articles", stats["tier1"])
        st.metric("Tier 2 Posts", stats.get("tier2", 0))
        st.metric("Tier 3 Reactions", stats["tier3"])

        st.markdown("### 💡 Write Today")
        ready = get_records_by_status("synthesized")
        tier1 = [r for r in ready if r["tier"] == 1]
        tier3 = [r for r in ready if r["tier"] == 3]

        if tier1:
            r = tier1[0]
            try:
                sp = json.loads(r.get("content_angle", "{}"))
            except Exception:
                sp = {}
            st.info(f"📄 **{r['title'][:40]}**\n\n_{sp.get('what_to_write', '')[:80]}_")
            if st.button("Write this →", key="today_write"):
                st.session_state.active_record = r
                st.rerun()
        if tier3:
            r = tier3[0]
            st.info(f"💬 Quick post: **{r['title'][:40]}**")


# ═══════════════════════════════════════════════════════
# TAB 2 — READING LIST (Google Sheets Import)
# ═══════════════════════════════════════════════════════
with tabs[1]:
    st.subheader("📋 Reading List — Google Sheets Import")
    st.caption("Bulk synthesize your curated reading list. Column G tracks what the Content Engine has processed.")

    # Session state for reading list
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

    # Auto-sync status
    from datetime import datetime as dt
    now = dt.now()

    # ── PERSISTENT ACTION REQUIRED ─────────────────────────
    # Always show at top — pulled from session state regardless of batch
    persistent_paste = get_pending_paste()
    if persistent_paste:
        st.error(f"🔴 ACTION REQUIRED — {len(persistent_paste)} links need your input")
        for item in persistent_paste:
            url = item['url']
            with st.expander(f"📋 Row {item['row']}: {url[:65]}"):
                pasted = st.text_area("Paste article content",
                                     key=f"persist_paste_{url}", height=150)
                c1, c2 = st.columns(2)
                with c1:
                    p_title = st.text_input("Title (optional)", key=f"persist_title_{url}")
                with c2:
                    p_author = st.text_input("Author (optional)", key=f"persist_author_{url}")
                if st.button("Process", key=f"persist_btn_{url}"):
                    if pasted:
                        title = p_title or url.split("/")[-2].replace("-"," ").title()
                        author = p_author or "Unknown"
                        source = url.split("/")[2].replace("www.","") if "//" in url else "Unknown"
                        result = process_pasted_text(
                            text=pasted, url=url,
                            source_name=source, author=author,
                            title=title, depth="quick"
                        )
                        if result["success"]:
                            sp = result.get("suggested_piece", {})
                            record = add_record(
                                source_url=url,
                                source_name=source, author=author,
                                title=result.get("title") or title,
                                synthesis=json.dumps({
                                    "tldr": result.get("tldr",""),
                                    "key_points": result.get("key_points",[]),
                                    "why_timely": result.get("why_timely","")
                                }),
                                key_quotes=result.get("key_quotes",[]),
                                content_angle=json.dumps(sp),
                                tier=sp.get("recommended_tier",3),
                                themes=result.get("themes",[]),
                                raw_content=pasted[:2000]
                            )
                            mark_as_synthesized(item['row'])
                            st.session_state.sheet_results = [
                                r for r in st.session_state.sheet_results
                                if r['url'] != url
                            ]
                            st.success(f"✅ Added as Record #{record['id']}!")
                            st.rerun()
        st.markdown("---")

    # Show last synced status
    if st.session_state.last_synced:
        elapsed = (now - st.session_state.last_synced).seconds // 60
        if elapsed < 60:
            sync_label = f"Last synced {elapsed} min ago"
        else:
            sync_label = f"Last synced {elapsed // 60}h ago"
        new_count = st.session_state.sync_stats.get("new_found", 0)
        if new_count > 0:
            st.info(f"🔄 {sync_label} — {new_count} new links found")
        else:
            st.success(f"✅ {sync_label} — library up to date")

    # Overview
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

        # Filter options
        col_a, col_b = st.columns(2)
        with col_a:
            show_viewed_only = st.checkbox("Show only links you've viewed (col F = Yes)")
        with col_b:
            batch_size = st.slider("Batch size (process at a time)", 5, 30, 10)

        links_to_show = st.session_state.sheet_links
        if show_viewed_only:
            links_to_show = [l for l in links_to_show if l.get('usman_viewed') in ['yes', 'y']]

        st.caption(f"Showing {len(links_to_show)} links")

        # Preview list
        with st.expander(f"Preview links ({len(links_to_show[:batch_size])} will be processed)"):
            for item in links_to_show[:batch_size]:
                viewed = "👁" if item.get('usman_viewed') in ['yes','y'] else "○"
                st.caption(f"{viewed} Row {item['row']}: {item['url'][:80]}")

        st.markdown("---")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            process_btn = st.button(
                f"🚀 Synthesize next {min(batch_size, len(links_to_show))} links",
                type="primary",
                use_container_width=True
            )
        with col_btn2:
            st.caption("⚠️ Instagram, TikTok, and LinkedIn links will need manual paste")

        if process_btn:
            batch = links_to_show[:batch_size]
            st.session_state.sheet_results = []
            needs_paste = []

            progress = st.progress(0)
            status_box = st.empty()

            for i, item in enumerate(batch):
                url = item['url']
                status_box.info(f"Processing {i+1}/{len(batch)}: {url[:60]}...")

                # Skip platforms that can't be scraped
                skip_domains = ['instagram.com', 'tiktok.com', 'twitter.com', 'x.com', 'facebook.com']
                if any(domain in url for domain in skip_domains):
                    st.session_state.sheet_results.append({
                        "url": url, "row": item['row'],
                        "status": "skip", "reason": "Platform cannot be auto-scraped"
                    })
                    progress.progress((i + 1) / len(batch))
                    continue

                # Skip if already in library
                if url_exists(url):
                    mark_as_synthesized(item['row'])
                    st.session_state.sheet_results.append({
                        "url": url, "row": item['row'],
                        "status": "exists", "title": "Already in library"
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
                    # Mark as Done in column G
                    mark_as_synthesized(item['row'])
                    st.session_state.sheet_results.append({
                        "url": url, "row": item['row'],
                        "status": "success",
                        "title": result.get("title", ""),
                        "tier": sp.get("recommended_tier", result.get("tier", 3)),
                        "tldr": result.get("tldr", ""),
                        "record_id": record["id"]
                    })
                else:
                    st.session_state.sheet_results.append({
                        "url": url, "row": item['row'],
                        "status": "needs_paste",
                        "error": result.get("error", "")
                    })
                    add_pending_paste(url, item['row'])
                    needs_paste.append(item)

                progress.progress((i + 1) / len(batch))

            status_box.empty()

            # Remove processed from session list
            processed_urls = {r['url'] for r in st.session_state.sheet_results
                            if r['status'] in ['success', 'exists', 'skip']}
            st.session_state.sheet_links = [
                l for l in st.session_state.sheet_links
                if l['url'] not in processed_urls
            ]

            success_count = len([r for r in st.session_state.sheet_results if r['status'] == 'success'])
            needs_paste_count = len([r for r in st.session_state.sheet_results if r['status'] == 'needs_paste'])
            # Refresh count from sheet
            st.session_state.sheet_links = get_unprocessed_links()
            st.session_state.last_synced = now
            st.success(f"Done! {success_count} synthesized, {needs_paste_count} need manual paste.")
            st.rerun()

        # ── RESULTS — ACTION REQUIRED AT TOP ─────────────────
        if st.session_state.sheet_results:
            needs_paste = [r for r in st.session_state.sheet_results if r['status'] == 'needs_paste']
            skipped = [r for r in st.session_state.sheet_results if r['status'] == 'skip']
            succeeded = [r for r in st.session_state.sheet_results if r['status'] == 'success']
            existed = [r for r in st.session_state.sheet_results if r['status'] == 'exists']

            # 🔴 ACTION REQUIRED — top, impossible to miss
            if needs_paste:
                st.markdown("---")
                st.error(f"🔴 ACTION REQUIRED — {len(needs_paste)} links need your input")
                for item in needs_paste:
                    url = item['url']
                    with st.expander(f"📋 Row {item['row']}: {url[:65]}"):
                        pasted = st.text_area("Paste article content", key=f"rl_paste_{url}", height=150)
                        c1, c2 = st.columns(2)
                        with c1:
                            p_title = st.text_input("Title (optional)", key=f"rl_title_{url}")
                        with c2:
                            p_author = st.text_input("Author (optional)", key=f"rl_author_{url}")
                        if st.button("Process", key=f"rl_btn_{url}"):
                            if pasted:
                                title = p_title or url.split("/")[-2].replace("-"," ").title()
                                author = p_author or "Unknown"
                                source = url.split("/")[2].replace("www.","") if "//" in url else "Unknown"
                                result = process_pasted_text(
                                    text=pasted, url=url,
                                    source_name=source, author=author,
                                    title=title, depth="quick"
                                )
                                if result["success"]:
                                    sp = result.get("suggested_piece", {})
                                    record = add_record(
                                        source_url=url,
                                        source_name=source, author=author,
                                        title=result.get("title") or title,
                                        synthesis=json.dumps({
                                            "tldr": result.get("tldr",""),
                                            "key_points": result.get("key_points",[]),
                                            "why_timely": result.get("why_timely","")
                                        }),
                                        key_quotes=result.get("key_quotes",[]),
                                        content_angle=json.dumps(sp),
                                        tier=sp.get("recommended_tier",3),
                                        themes=result.get("themes",[]),
                                        raw_content=pasted[:2000]
                                    )
                                    mark_as_synthesized(item['row'])
                                    # Remove from needs_paste list
                                    remove_pending_paste(url)
                                    st.success(f"✅ Added as Record #{record['id']}!")
                                    st.rerun()

            # ⏭️ SKIPPED — platforms that can't be auto-scraped
            if skipped:
                st.markdown("---")
                st.warning(f"⏭️ SKIPPED — {len(skipped)} links from platforms that can't be auto-scraped")
                st.caption("Instagram, TikTok, Twitter — open these manually and paste content above")
                for item in skipped:
                    st.caption(f"  Row {item['row']}: {item['url'][:70]}")

            # ✅ SYNTHESIZED — successful results
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

            # Already existed
            if existed:
                st.caption(f"⏭️ {len(existed)} already in library — marked Done in Sheet")

# ═══════════════════════════════════════════════════════
# TAB 2 — ADD CONTENT
# ═══════════════════════════════════════════════════════
with tabs[2]:
    st.subheader("Add Content to Library")

    input_method = st.radio(
        "Input method",
        ["🔗 URL", "📋 Paste text", "💭 Topic idea"],
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
                        source_name=source, author=author,
                        title=title, depth=d
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

    # Preview result
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
                               index=[1,2,3].index(tier_val) if tier_val in [1,2,3] else 2)
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
# TAB 3 — LIBRARY
# ═══════════════════════════════════════════════════════
with tabs[3]:
    st.subheader("Intelligence Library")

    c1, c2, c3 = st.columns(3)
    with c1:
        f_status = st.selectbox("Status", ["All", "synthesized", "drafting", "published"])
    with c2:
        f_tier = st.selectbox("Tier", ["All", "1 - Full Article", "2 - LinkedIn Post", "3 - Quick Reaction"])
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
        with st.expander(f"{emoji} T{tier} | {record['title'][:65]} | #{record['id']}"):
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
                        st.markdown(f"**Audience:** {sp.get('audience', '')}")
                        if sp.get('coined_term'):
                            st.markdown(f"**Coined term:** _{sp.get('coined_term')}_")
                except Exception:
                    pass
                st.markdown(f"[Source ↗]({record['source_url']})")
            with c2:
                st.markdown(f"**Status:** {record['status']}")
                st.markdown(f"**Themes:** {', '.join(record.get('themes', []))}")
                if st.button("✍️ Write", key=f"lib_{record['id']}"):
                    st.session_state.active_record = record
                    st.rerun()

# ═══════════════════════════════════════════════════════
# TAB 4 — WRITE
# ═══════════════════════════════════════════════════════
with tabs[4]:
    st.subheader("Write Content")

    library = load_library()
    ready = [r for r in library["records"] if r["status"] in ["synthesized", "drafting"]]

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

        try:
            syn = json.loads(record['synthesis'])
        except Exception:
            syn = {"tldr": record.get('synthesis', ''), "key_points": [], "why_timely": ""}

        try:
            sp = json.loads(record.get('content_angle', '{}'))
        except Exception:
            sp = {}

        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.markdown(f"**{record['title']}**")
            st.caption(f"{record['author']} | {record['source_name']}")
            st.markdown(f"**TLDR:** {syn.get('tldr', '')}")

            with st.expander("Key Points"):
                for p in syn.get('key_points', []):
                    st.markdown(f"• {p}")

            if sp:
                with st.expander("Suggested Piece"):
                    st.markdown(f"**What:** {sp.get('what_to_write', '')}")
                    st.markdown(f"**Why now:** {sp.get('why_now', '')}")
                    st.markdown(f"**Audience:** {sp.get('audience', '')}")
                    st.markdown(f"**Value:** {sp.get('value_to_audience', '')}")
                    st.markdown(f"**Your angle:** {sp.get('usman_angle', '')}")
                    if sp.get('coined_term'):
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
            st.caption("Ask Claude to help form your POV before writing")

            chat_context = f"""
Article: {record['title']}
Author: {record['author']} | Source: {record['source_name']}
TLDR: {syn.get('tldr', '')}
Key points: {chr(10).join(f'- {p}' for p in syn.get('key_points', []))}
Usman's background: Field CISO at Google Cloud, 17 years security,
advises Fortune 500 boards and federal agencies on AI security.
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
form his perspective on a security topic. Be direct, specific, and draw on 
enterprise CISO realities. Help him find angles others miss.

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

        with col_right:
            st.markdown("### ✍️ Draft")

            output_format = st.selectbox(
                "Output format",
                [
                    "📄 Tier 1 — Full article for usmanc.com",
                    "🟣 Tier 2 — Substantive LinkedIn post (300-500 words)",
                    "🔵 Tier 3 — Quick reaction (top 3 takeaways, link in comments)"
                ]
            )

            st.markdown("**Your POV** _(optional but improves output significantly)_")
            q1 = st.text_area("Your take from CISO experience?",
                             placeholder="I've seen this play out at Fortune 500s where...",
                             height=60, key="q1")
            q2 = st.text_area("Angle others are missing?",
                             placeholder="Everyone focuses on X but nobody talks about Y...",
                             height=60, key="q2")
            if "Tier 1" in output_format:
                q3 = st.text_area("What should CISOs actually DO?",
                                 placeholder="The first thing I'd tell my CISO peers is...",
                                 height=60, key="q3")
            else:
                q3 = ""

            if st.button("✍️ Generate Draft", type="primary", use_container_width=True):
                if "Tier 1" in output_format:
                    tier_instruction = "Write a TIER 1 full article for usmanc.com (800-1200 words)"
                elif "Tier 2" in output_format:
                    tier_instruction = "Write a TIER 2 substantive LinkedIn post (300-500 words)"
                else:
                    tier_instruction = "Write a TIER 3 quick reaction post (150-300 words). End with 'Link to the original in the comments.' before hashtags."

                deep = st.session_state.deep_synthesis or {}
                context_parts = [
                    f"ARTICLE: {record['title']}",
                    f"SOURCE: {record['author']} | {record['source_name']}",
                    f"URL: {record['source_url']}",
                    f"TLDR: {syn.get('tldr', '')}",
                    "KEY POINTS:\n" + "\n".join(f"- {p}" for p in syn.get('key_points', [])),
                ]
                if deep.get('core_argument'):
                    context_parts.append(f"CORE ARGUMENT: {deep['core_argument']}")
                if deep.get('key_stats'):
                    context_parts.append("STATS:\n" + "\n".join(f"- {s}" for s in deep['key_stats']))
                if deep.get('key_quotes'):
                    context_parts.append("QUOTES:\n" + "\n".join(f'- "{q}"' for q in deep['key_quotes']))
                if sp.get('coined_term'):
                    context_parts.append(f"COINED TERM TO USE: {sp['coined_term']}")

                pov_parts = []
                if q1: pov_parts.append(f"My CISO experience: {q1}")
                if q2: pov_parts.append(f"Angle others miss: {q2}")
                if q3: pov_parts.append(f"What CISOs should do: {q3}")

                chat_insights = ""
                if st.session_state.chat_messages:
                    chat_insights = "\nINSIGHTS FROM RESEARCH CHAT:\n"
                    for m in st.session_state.chat_messages[-4:]:
                        chat_insights += f"{m['role'].upper()}: {m['content'][:200]}\n"

                prompt = f"""{tier_instruction}

INTELLIGENCE:
{chr(10).join(context_parts)}

USMAN'S POV:
{chr(10).join(pov_parts) if pov_parts else "Use the suggested angle from the synthesis."}
{chat_insights}

Follow the voice and format exactly for the tier requested."""

                with st.spinner("Writing with Claude Sonnet..."):
                    response = client.messages.create(
                        model="claude-sonnet-4-5",
                        max_tokens=2000,
                        system=USMAN_VOICE,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    st.session_state.draft = response.content[0].text
                    update_record_status(record["id"], "drafting")

            if st.session_state.draft:
                edited = st.text_area("Edit your draft",
                                     value=st.session_state.draft, height=400)

                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.button("📋 Copy", use_container_width=True):
                        st.code(edited)
                        st.info("Select all and copy")
                with c2:
                    if st.button("🔄 Regenerate", use_container_width=True):
                        st.session_state.draft = ""
                        st.rerun()
                with c3:
                    if st.button("✅ Published", use_container_width=True):
                        update_record_status(record["id"], "published")
                        st.session_state.draft = ""
                        st.success("Marked published!")
                        st.rerun()

                if "Tier 1" in output_format:
                    if st.button("📱 Generate LinkedIn promo post", use_container_width=True):
                        with st.spinner("Generating..."):
                            li_resp = client.messages.create(
                                model="claude-sonnet-4-5",
                                max_tokens=400,
                                system=USMAN_VOICE,
                                messages=[{"role": "user",
                                          "content": f"Write a Tier 3 LinkedIn post promoting this article. Hook + 3 key insights + 'Full article in the comments' + hashtags. 200 words max.\n\nARTICLE:\n{edited[:1500]}"}]
                            )
                            st.session_state.linkedin_draft = li_resp.content[0].text

                if st.session_state.linkedin_draft:
                    st.markdown("### 📱 LinkedIn Promo")
                    st.text_area("Post", value=st.session_state.linkedin_draft, height=200)

# ═══════════════════════════════════════════════════════
# TAB 5 — SEARCH & BROWSE
# ═══════════════════════════════════════════════════════
with tabs[5]:
    st.subheader("Search & Browse by Theme")

    # ── Search bar ─────────────────────────────────────
    query = st.text_input("🔍 Search by keyword, topic, or theme",
                          placeholder="agentic SOC, zero trust, LLM security")

    # ── Theme browser ──────────────────────────────────
    library = load_library()
    all_records = library["records"]

    # Build theme map
    all_themes = sorted(set(t for r in all_records for t in r.get("themes", [])))
    published = [r for r in all_records if r["status"] == "published"]
    intelligence = [r for r in all_records if r["status"] != "published"]

    # Theme counts
    theme_counts = {}
    for theme in all_themes:
        intel_count = len([r for r in intelligence if theme in r.get("themes", [])])
        pub_count = len([r for r in published if theme in r.get("themes", [])])
        theme_counts[theme] = {"intel": intel_count, "published": pub_count}

    if not query:
        st.markdown("### 📂 Browse by Theme")
        st.caption("Click a theme to see all records and written pieces")

        # Theme grid
        cols = st.columns(3)
        theme_selected = None
        for i, theme in enumerate(all_themes):
            with cols[i % 3]:
                counts = theme_counts[theme]
                intel_n = counts["intel"]
                pub_n = counts["published"]
                label = f"**{theme}** — {intel_n} sources · {pub_n} written"
                if st.button(label, key=f"theme_{theme}", use_container_width=True):
                    st.session_state["selected_theme"] = theme

        # Show selected theme content
        selected_theme = st.session_state.get("selected_theme")
        if selected_theme:
            st.markdown(f"---")
            st.markdown(f"### 🏷️ {selected_theme.title()}")

            theme_intel = [r for r in intelligence if selected_theme in r.get("themes", [])]
            theme_pub = [r for r in published if selected_theme in r.get("themes", [])]

            # Cross-synthesize button
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
                            # Link to usmanc.com if it was a Tier 1 article
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

    # ── Search results ─────────────────────────────────
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

        # Split results into intelligence vs published
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
