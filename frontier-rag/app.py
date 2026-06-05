"""
Frontier AI Intelligence — Streamlit UI

Query interface for the RAG system covering:
- Frontier AI models and companies
- Safety evaluations and frameworks
- Security implications (Field CISO Mode)
- Disagreement surfacing across sources
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="Frontier AI Intelligence",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Lazy imports (skip if DB not available) ──────────────────────
@st.cache_resource
def get_synthesizer():
    from synthesis.synthesizer import synthesize, find_disagreements
    return synthesize, find_disagreements

@st.cache_resource
def get_db_stats():
    try:
        from db.connection import get_engine
        from sqlalchemy import text
        engine = get_engine()
        with engine.connect() as conn:
            docs = conn.execute(text("SELECT COUNT(*) FROM documents")).scalar()
            chunks = conn.execute(text("SELECT COUNT(*) FROM chunks")).scalar()
            entities = conn.execute(text(
                "SELECT entity_name, COUNT(*) as cnt FROM documents GROUP BY entity_name ORDER BY cnt DESC"
            )).fetchall()
        return {"docs": docs, "chunks": chunks, "entities": entities}
    except Exception as e:
        return {"docs": 0, "chunks": 0, "entities": [], "error": str(e)}


# ── Sidebar ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔍 Frontier AI Intelligence")
    st.caption("RAG system across frontier AI labs, safety evals, and security frameworks")
    st.markdown("---")

    # Stats — only load when user clicks (avoids blocking startup render)
    if st.button("📊 Load corpus stats", use_container_width=True):
        try:
            stats = get_db_stats()
            st.metric("Documents", stats.get("docs", 0))
            if stats.get("entities"):
                st.markdown("**Coverage:**")
                for entity, count in stats.get("entities", []):
                    bar = "█" * min(count * 2, 10)
                    st.caption(f"`{entity[:20]:<20}` {bar} {count}")
            if stats.get("error"):
                st.error(f"DB: {stats['error'][:80]}")
        except Exception as e:
            st.error(f"DB error: {str(e)[:80]}")
    else:
        st.caption("30+ documents · Anthropic, OpenAI, Google, Mistral, DeepSeek, CISA, UK AISI")

    st.markdown("---")
    st.markdown("**Query modes:**")
    st.caption("🔵 **Standard** — factual synthesis with citations")
    st.caption("🛡️ **Field CISO** — security and procurement lens")
    st.caption("⚡ **Disagreements** — surface conflicting views")

    st.markdown("---")
    entity_filter = st.selectbox(
        "Filter by organization",
        ["All"]
    )
    if entity_filter == "All":
        entity_filter = None


# ── Main UI ──────────────────────────────────────────────────────
st.markdown("# Frontier AI Intelligence")
st.markdown("*Query across 30+ documents from Anthropic, Google DeepMind, Meta, Mistral, DeepSeek, CISA, UK AISI, and more.*")

# Query mode tabs
mode_tab, compare_tab, disagree_tab, watch_tab, add_tab, history_tab = st.tabs(["💬 Query", "📊 Model Comparison", "⚡ Find Disagreements", "🔄 Auto-Watcher", "➕ Add Content", "📋 Query History"])


# ── QUERY TAB ────────────────────────────────────────────────────
with mode_tab:
    query = st.text_area(
        "Ask anything about frontier AI models, safety, or security",
        height=80,
        placeholder="e.g. How do Anthropic and Google DeepMind approach alignment differently?\n"
                    "e.g. What are the security risks of agentic AI systems?\n"
                    "e.g. Which models are most capable for enterprise use?",
        key="main_query"
    )

    col_mode, col_btn = st.columns([2, 1])
    with col_mode:
        ciso_mode = st.toggle("🛡️ Field CISO Mode", value=False,
                              help="Filters answers through security, procurement, and compliance lens")
    with col_btn:
        submit = st.button("Search", type="primary", use_container_width=True)

    if submit and query.strip():
        synthesize_fn, _ = get_synthesizer()

        with st.spinner("Retrieving and synthesizing..." if not ciso_mode
                        else "Analyzing through Field CISO lens..."):
            result = synthesize_fn(
                query.strip(),
                top_k=8,
                field_ciso_mode=ciso_mode,
                entity_filter=entity_filter,
            )

        # Mode badge
        if ciso_mode:
            st.markdown("🛡️ **Field CISO Mode** — filtered through security and procurement lens")

        # Answer
        st.markdown("---")
        st.markdown(result["answer"])

        # Sources
        st.markdown("---")
        st.markdown("**Sources used:**")
        source_cols = st.columns(min(len(result["sources"]), 4))
        for i, src in enumerate(result["sources"]):
            with source_cols[i % 4]:
                label = f"[{src['entity']}]({src['url']})" if src.get("url") else src["entity"]
                st.markdown(f"📄 {label}")
                st.caption(src["title"][:50])

        # Metadata
        st.caption(
            f"Chunks retrieved: {result['chunks_used']} · "
            f"Latency: {result['latency_ms']}ms · "
            f"Agent: `{result['agent_id'][:8]}`"
        )

    elif submit:
        st.warning("Enter a question first.")


# ── DISAGREEMENTS TAB ─────────────────────────────────────────────
with disagree_tab:
    st.markdown("**Surface where sources disagree or diverge on a topic.**")
    st.caption("Useful for: 'What do labs disagree on regarding safety?', 'Where do approaches differ?'")

    disagree_query = st.text_input(
        "Topic to analyze for disagreements",
        placeholder="e.g. AI safety approaches · open vs closed models · agent oversight"
    )
    disagree_btn = st.button("Find Disagreements", type="primary")

    if disagree_btn and disagree_query.strip():
        _, find_disagreements_fn = get_synthesizer()
        with st.spinner("Analyzing sources for tensions and conflicts..."):
            result = find_disagreements_fn(disagree_query.strip(), top_k=10)

        st.markdown("---")
        st.markdown(result["answer"])
        st.caption(f"Sources analyzed: {', '.join(result['sources']) if isinstance(result['sources'], list) else result['sources']}")
        st.caption(f"Latency: {result['latency_ms']}ms")


# ── COMPARISON TABLE TAB ─────────────────────────────────────────
with compare_tab:
    import pandas as pd

    st.markdown("### 📊 Frontier Model Leaderboard")
    st.caption("Live benchmark data from llm-stats.com — Reasoning, Coding, Agent scores + pricing")

    if st.button("🔄 Refresh Leaderboard Data", type="primary"):
        import io, contextlib
        output = io.StringIO()
        with st.spinner("Scraping llm-stats.com..."):
            try:
                from ingest.scrape_leaderboard import run as lb_run
                with contextlib.redirect_stdout(output):
                    lb_run()
                st.success("Leaderboard updated!")
                st.rerun()
            except Exception as e:
                st.error(f"Scraping failed: {e}")
                st.code(output.getvalue())

    try:
        from db.connection import get_engine as _ge
        from sqlalchemy import text as _t
        _eng = _ge()
        with _eng.connect() as _c:
            lb_rows = _c.execute(_t("""
                SELECT rank, model_name, creator, llm_score, reasoning,
                       coding, agent, arena, context_win, speed,
                       price_input, license, scraped_at
                FROM leaderboard
                ORDER BY rank
                LIMIT 60
            """)).fetchall()

        if lb_rows:
            df = pd.DataFrame(lb_rows, columns=[
                "Rank", "Model", "Creator", "Intelligence", "Reasoning",
                "Coding", "Agent", "Arena", "Context", "Speed",
                "$/1M", "License", "Updated"
            ])
            scraped = str(df["Updated"].iloc[0])[:16]
            st.caption(f"Last updated: {scraped} · {len(df)} models — source: llm-stats.com")

            c1, c2, c3 = st.columns(3)
            with c1:
                creators = ["All"] + sorted(df["Creator"].dropna().unique().tolist())
                cf = st.selectbox("Creator", creators, key="lb_creator")
            with c2:
                licenses = ["All", "Open Source", "Proprietary"]
                lf = st.selectbox("License", licenses, key="lb_license")
            with c3:
                top_n = st.selectbox("Show top", [10, 20, 30, 50], index=1, key="lb_topn")

            filtered = df.copy()
            if cf != "All":
                filtered = filtered[filtered["Creator"] == cf]
            if lf != "All":
                filtered = filtered[filtered["License"] == lf]
            filtered = filtered.head(top_n)
            display = filtered.drop(columns=["Updated", "Creator"])

            def score_color(val):
                if pd.isna(val): return ""
                if val >= 60: return "background-color: #1a3a1a; color: #4ade80"
                if val >= 45: return "background-color: #2a2a0a; color: #facc15"
                return "background-color: #2a1a1a; color: #f87171"

            def price_color(val):
                if pd.isna(val): return ""
                if val <= 2: return "background-color: #1a3a1a; color: #4ade80"
                if val <= 5: return "background-color: #2a2a0a; color: #facc15"
                return "background-color: #2a1a1a; color: #f87171"

            score_cols = [col for col in ["Intelligence", "Reasoning", "Coding", "Agent"] if col in display.columns]
            styled = display.style.map(
                score_color, subset=score_cols
            ).map(
                price_color, subset=["$/1M"]
            ).format({
                "Intelligence": lambda x: f"{x:.1f}" if pd.notna(x) else "—",
                "Reasoning":    lambda x: f"{x:.1f}" if pd.notna(x) else "—",
                "Coding":       lambda x: f"{x:.1f}" if pd.notna(x) else "—",
                "Agent":        lambda x: f"{x:.1f}" if pd.notna(x) else "—",
                "Arena":        lambda x: f"{int(x):,}" if pd.notna(x) else "—",
                "$/1M":         lambda x: f"${x:.2f}" if pd.notna(x) else "—",
            }, na_rep="—")

            st.dataframe(styled, use_container_width=True, height=520)

            st.markdown("---")
            st.markdown("**Current leaders:**")
            lc1, lc2, lc3, lc4 = st.columns(4)
            top = df.dropna(subset=["Intelligence"]).nlargest(1, "Intelligence")
            cheap = df.dropna(subset=["$/1M"]).nsmallest(1, "$/1M")
            open_top = df[df["License"]=="Open Source"].dropna(subset=["Intelligence"]).nlargest(1,"Intelligence")
            with lc1:
                if not top.empty:
                    st.metric("🏆 Highest Score", top.iloc[0]["Model"][:18], f"{top.iloc[0]['Intelligence']:.1f}")
            with lc2:
                if not cheap.empty:
                    st.metric("💰 Cheapest", cheap.iloc[0]["Model"][:18], f"${cheap.iloc[0]['$/1M']:.2f}/M")
            with lc3:
                if not open_top.empty:
                    st.metric("🔓 Best Open", open_top.iloc[0]["Model"][:18], f"{open_top.iloc[0]['Intelligence']:.1f}")
            with lc4:
                china = df[df["Creator"].str.contains("Alibaba|DeepSeek|Baidu|Moonshot|Qwen|01.AI|Kimi|Zhipu|ByteDance", na=False, case=False)]
                if not china.empty and "Intelligence" in china.columns:
                    best_cn = china.dropna(subset=["Intelligence"]).nlargest(1,"Intelligence")
                    if not best_cn.empty:
                        st.metric("🇨🇳 Best Chinese", best_cn.iloc[0]["Model"][:18], f"{best_cn.iloc[0]['Intelligence']:.1f}")

        else:
            st.info("No leaderboard data yet. Click **Refresh Leaderboard Data** above to pull live data.")

    except Exception as e:
        st.warning(f"Leaderboard table not found — click Refresh: {e}")

    # ── Benchmark Leaders (from Vellum) ──────────────────────────
    st.markdown("---")
    st.markdown("**📐 Benchmark Leaders** — from vellum.ai/llm-leaderboard")
    st.caption("2026 benchmarks that differentiate frontier models — MMLU is saturated, these are not")

    BENCHMARK_DATA = {
        "GPQA Diamond (PhD Reasoning)": [
            ("Claude Opus 4.8", "93.6%"), ("Claude Opus 4.7", "94.2%"),
            ("GPT-5.5", "93.6%"), ("GPT 5.2", "92.4%"), ("Claude 3 Opus", "95.4%"),
        ],
        "SWE-bench (Agentic Coding)": [
            ("Claude Opus 4.8", "88.6%"), ("Claude Opus 4.7", "87.6%"),
            ("Claude Sonnet 4.5", "82%"), ("Claude Opus 4.5", "80.9%"), ("Claude Opus 4.6", "80.8%"),
        ],
        "AIME 2025 (Math Olympiad)": [
            ("Gemini 3 Pro", "100%"), ("GPT 5.2", "100%"),
            ("Claude Opus 4.6", "99.8%"), ("Kimi K2 Thinking", "99.1%"), ("GPT oss 20b", "98.7%"),
        ],
        "Humanity's Last Exam": [
            ("Claude Opus 4.8", "57.9%"), ("Gemini 3 Pro", "45.8%"),
            ("Kimi K2 Thinking", "44.9%"), ("GPT-5.5 Pro", "43.1%"), ("GPT-5.5", "41.4%"),
        ],
    }

    bench_cols = st.columns(len(BENCHMARK_DATA))
    for col, (bench_name, leaders) in zip(bench_cols, BENCHMARK_DATA.items()):
        with col:
            st.markdown(f"**{bench_name}**")
            for i, (model, score) in enumerate(leaders):
                medal = ["🥇","🥈","🥉","4️⃣","5️⃣"][i]
                st.caption(f"{medal} {model}: **{score}**")


# ── AUTO-WATCHER TAB ──────────────────────────────────────────────
with watch_tab:
    st.markdown("**Auto-watcher** — monitors sources for new content and re-ingests on change.")

    try:
        from db.connection import get_engine as _get_engine2
        from sqlalchemy import text as _text2
        _engine2 = _get_engine2()
        with _engine2.connect() as _conn2:
            watch_rows = _conn2.execute(_text2("""
                SELECT url, entity_name, check_frequency,
                       last_checked, last_hash IS NOT NULL as has_baseline
                FROM watch_sources
                ORDER BY entity_name
            """)).fetchall()

        if watch_rows:
            import pandas as pd
            wdf = pd.DataFrame(watch_rows, columns=["URL", "Entity", "Frequency", "Last Checked", "Baseline Set"])
            wdf["Last Checked"] = wdf["Last Checked"].apply(lambda x: str(x)[:16] if x else "Never")
            wdf["Baseline Set"] = wdf["Baseline Set"].map({True: "✅", False: "⏳"})
            st.dataframe(wdf, use_container_width=True)
        else:
            st.info("No watch sources configured.")

    except Exception as e:
        st.error(f"Could not load watch sources: {e}")

    st.markdown("---")
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        force_check = st.toggle("Force check all sources", value=False,
                                help="Check all sources now regardless of schedule")
    with col_w2:
        run_watcher_btn = st.button("▶️ Run Watcher Now", type="primary", use_container_width=True)

    if run_watcher_btn:
        import io, contextlib
        output = io.StringIO()
        with st.spinner("Checking watch sources for new content..."):
            try:
                from ingest.watcher import run as watcher_run
                with contextlib.redirect_stdout(output):
                    watcher_run(force=force_check)
                st.success("Watcher run complete.")
                st.code(output.getvalue())
            except Exception as e:
                st.error(f"Error: {e}")
                st.code(output.getvalue())

    st.caption("💡 Schedule with GitHub Actions cron to run daily automatically.")


# ── ADD CONTENT TAB ──────────────────────────────────────────────
with add_tab:
    st.markdown("**Add a URL to the corpus** — ingests immediately and optionally adds to the watch list.")

    url_input = st.text_input(
        "URL",
        placeholder="https://airisk.mit.edu/priorities",
        help="Any publicly accessible HTML page"
    )

    col_a, col_b = st.columns(2)
    with col_a:
        source_type = st.selectbox("Source type", [
            "safety_eval", "model_card", "blog",
            "regulatory", "benchmark", "zt_framework"
        ])
        entity_name = st.text_input("Organization", placeholder="MIT, CISA, Anthropic...")
    with col_b:
        entity_type = st.selectbox("Entity type", [
            "evaluation", "company", "regulation", "research"
        ])
        add_to_watch = st.toggle("Also add to Auto-Watcher", value=False,
                                 help="Re-check this URL daily/weekly for new content")

    ingest_btn = st.button("⚡ Ingest Now", type="primary", disabled=not url_input.strip())

    if ingest_btn and url_input.strip():
        if not entity_name.strip():
            st.warning("Enter an organization name.")
        else:
            import io, contextlib
            output = io.StringIO()
            with st.spinner(f"Ingesting {url_input[:60]}..."):
                try:
                    import sys, os
                    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                    from ingest.pipeline import ingest_url
                    with contextlib.redirect_stdout(output):
                        result = ingest_url(
                            url=url_input.strip(),
                            source_type=source_type,
                            entity_name=entity_name.strip(),
                            entity_type=entity_type,
                        )

                    if result["status"] == "success":
                        st.success(f"✅ Ingested: **{result.get('title', url_input)[:60]}** — {result.get('chunks', 0)} chunks")
                    elif result["status"] == "skipped":
                        st.info("Already in corpus. Use force re-ingest if content changed.")
                    else:
                        st.error(f"Failed: {result.get('error', 'unknown error')}")

                    if add_to_watch and result["status"] in ("success", "skipped"):
                        try:
                            from db.connection import get_engine
                            from sqlalchemy import text
                            engine = get_engine()
                            freq = st.radio("Check frequency", ["daily", "weekly"], horizontal=True, key="freq_radio")
                            with engine.connect() as conn:
                                conn.execute(text("""
                                    INSERT INTO watch_sources
                                        (url, entity_name, source_type, entity_type, check_frequency)
                                    VALUES (:url, :entity, :stype, :etype, :freq)
                                    ON CONFLICT (url) DO NOTHING
                                """), {
                                    "url": url_input.strip(),
                                    "entity": entity_name.strip(),
                                    "stype": source_type,
                                    "etype": entity_type,
                                    "freq": freq,
                                })
                                conn.commit()
                            st.success("✅ Added to Auto-Watcher")
                        except Exception as e:
                            st.warning(f"Ingested OK but watch list failed: {e}")

                    with st.expander("Ingestion log"):
                        st.code(output.getvalue())

                except Exception as e:
                    st.error(f"Error: {e}")
                    st.code(output.getvalue())

    st.markdown("---")
    st.markdown("**Quick add — paste these to ingest the MIT AI Risk Repository:**")
    st.code("https://airisk.mit.edu/priorities")
    st.code("https://arxiv.org/abs/2408.12622")
    st.caption("Entity: MIT · Type: safety_eval")


# ── HISTORY TAB ──────────────────────────────────────────────────
with history_tab:
    st.markdown("**Audit trail — every query logged with agent identity.**")
    st.caption("This is the claude-zt Foundation tier in action.")

    try:
        from db.connection import get_engine
        from sqlalchemy import text as sql_text
        engine = get_engine()
        with engine.connect() as conn:
            rows = conn.execute(sql_text("""
                SELECT agent_id, agent_role, query_text, mode,
                       chunks_retrieved, latency_ms, created_at
                FROM queries
                ORDER BY created_at DESC
                LIMIT 20
            """)).fetchall()

        if rows:
            for r in rows:
                with st.expander(
                    f"`{r[0][:8]}` [{r[2][:60]}]",
                    expanded=False
                ):
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Role", r[1])
                    col2.metric("Chunks", r[3] or 0)
                    col3.metric("Latency", f"{r[5]}ms" if r[5] else "—")
                    st.caption(f"Mode: {r[3]} · {r[6]}")
                    st.text(r[2])
        else:
            st.info("No queries logged yet. Run a search to see the audit trail.")
    except Exception as e:
        st.warning(f"Could not load history: {e}")
