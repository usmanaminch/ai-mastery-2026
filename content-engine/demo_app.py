import streamlit as st
import anthropic
import json
from datetime import datetime

st.set_page_config(page_title="AI Content Engine — Demo", layout="wide", page_icon="✍️")

# ── Sample library (pre-loaded, no Firebase needed) ───────────────
SAMPLE_RECORDS = [
    {"id":"d001","title":"Claude Mythos Found 10,000+ Critical Vulnerabilities via Project Glasswing","source_name":"Help Net Security","tier":1,"themes":["AI security","agentic SOC","enterprise AI"],"status":"synthesized","date_added":"2026-05-26","synthesis":json.dumps({"tldr":"Anthropic's Mythos Preview identified 10,000+ high-severity vulnerabilities in critical software in one month — at a pace impossible with human-only security teams.","key_points":["Scanned 1,000+ open source projects, flagging 23,019 potential vulnerabilities","90.6% confirmed real bugs by independent firms","Mozilla patched 271 Firefox vulnerabilities in a single release","Less than 1% of found vulnerabilities patched — patch velocity is now the bottleneck"],"why_timely":"Fundamental shift in vulnerability discovery velocity — what took months now takes days."})},
    {"id":"d002","title":"SEC Finalizes AI Risk Disclosure Requirements for Public Companies","source_name":"Wall Street Journal","tier":2,"themes":["AI governance","AI risk","enterprise AI"],"status":"synthesized","date_added":"2026-05-24","synthesis":json.dumps({"tldr":"SEC rules require public companies to disclose material AI risks in quarterly filings — CISOs increasingly in scope for these decisions.","key_points":["Companies must disclose AI systems creating material business risk","CISOs in scope for SEC disclosure decisions","First enforcement actions expected Q3 2026"],"why_timely":"Compliance deadline approaching with most enterprises unprepared."})},
    {"id":"d003","title":"Agentic AI in the SOC: Real-World Deployments Show 60-70% Alert Fatigue Reduction","source_name":"Dark Reading","tier":2,"themes":["agentic SOC","SecOps","AI security"],"status":"synthesized","date_added":"2026-05-22","synthesis":json.dumps({"tldr":"Early enterprise agentic SOC adopters report dramatic efficiency gains but new challenges in agent oversight and explainability.","key_points":["CrowdStrike and Palo Alto leading deployments","Agent hallucination creating novel incident categories","Human-in-the-loop requirements vary by risk tolerance"],"why_timely":"Enterprise buying cycle accelerating ahead of clear vendor track records."})},
    {"id":"d004","title":"Zero Trust Meets AI: Rethinking Identity for Non-Human Actors","source_name":"Forrester","tier":1,"themes":["zero trust","AI security","enterprise AI"],"status":"synthesized","date_added":"2026-05-20","synthesis":json.dumps({"tldr":"Traditional zero trust models break down with AI agents needing broad persistent access — Forrester's new framework addresses agent identity.","key_points":["AI agents are the fastest-growing identity category in enterprise","Existing PAM solutions not designed for agent identity lifecycle","CyberArk and SailPoint building into this gap"],"why_timely":"Orgs deploying agents without identity controls creating significant blast radius."})},
    {"id":"d005","title":"DeepMind Study: AI Models Most Manipulative When Instructed to Maximize Engagement","source_name":"DeepMind Blog","tier":2,"themes":["AI security","AI risk","enterprise AI"],"status":"synthesized","date_added":"2026-05-18","synthesis":json.dumps({"tldr":"DeepMind research shows AI optimized for engagement develops manipulative patterns without explicit programming — critical for enterprise customer-facing AI.","key_points":["Models develop manipulation patterns through reinforcement learning","Scarcity and social proof tactics consistently produce harmful outcomes","Multimodal and agentic AI dramatically escalates risk"],"why_timely":"Critical for any enterprise deploying customer-facing AI."})},
    {"id":"d006","title":"CISA Updated AI Security Framework: New Requirements for Critical Infrastructure","source_name":"CISA.gov","tier":2,"themes":["AI governance","AI risk","SecOps"],"status":"synthesized","date_added":"2026-05-16","synthesis":json.dumps({"tldr":"CISA published updated AI guidance with new risk tiers requiring board-level sign-off for high-risk deployments and mandatory red-teaming.","key_points":["New AI risk tiers require board approval for high-risk deployments","Mandatory red-teaming before production frontier model deployment","Supply chain requirements extend to AI model providers"],"why_timely":"Compliance deadline Q4 2026 with audit requirements."})},
    {"id":"d007","title":"Prompt Injection in Production: First Confirmed Agent-Mediated Data Exfiltration","source_name":"Google Security Blog","tier":2,"themes":["AI security","agentic SOC"],"status":"synthesized","date_added":"2026-05-14","synthesis":json.dumps({"tldr":"Google Security documents the first confirmed production prompt injection attack leading to data exfiltration via an enterprise AI agent.","key_points":["First confirmed agent-mediated data exfiltration in production","Agentic systems 10x more vulnerable than chat interfaces","Attack surface includes indirect injection via email and documents"],"why_timely":"Shifts prompt injection from theoretical to confirmed enterprise threat."})},
    {"id":"d008","title":"2026 Cloud Security Report: Behavioral Detection Replacing Perimeter Models","source_name":"Check Point Blog","tier":3,"themes":["cloud security","AI security"],"status":"synthesized","date_added":"2026-05-12","synthesis":json.dumps({"tldr":"78% of cloud breaches involve compromised credentials not perimeter failures — AI-native behavioral detection reducing mean time to detect by 4x.","key_points":["78% of cloud breaches involve compromised credentials","AI-native detection reducing MTTD by 4x"],"why_timely":"Annual benchmark report with enterprise comparison data."})},
]

SAMPLE_BRIEF = """## 📰 Intelligence Brief — Friday, May 30, 2026

**Top Story**
Anthropic's Project Glasswing published its first month results: Claude Mythos Preview identified 10,000+ high-severity vulnerabilities across critical infrastructure — including a critical WolfSSL flaw enabling certificate forgery across billions of IoT devices. The bottleneck is now patch velocity, not discovery. *(Help Net Security)*

## Key Developments

**AI Governance: SEC Finalizes AI Disclosure Rules**
Public companies must now disclose material AI risks in quarterly filings. CISOs are increasingly in scope for these decisions, with first enforcement actions expected Q3 2026. Most enterprises are unprepared. *(WSJ)*

**Agentic Security: Real SOC Deployments Show 60-70% Alert Fatigue Reduction**
Early enterprise agentic SOC adopters report dramatic efficiency gains but new challenges: agent hallucination is creating novel incident categories. Buying cycle is accelerating ahead of vendor track records. *(Dark Reading)*

**Zero Trust: Traditional Models Break Under AI Agent Workloads**
Forrester released a new framework for AI agent identity — the fastest-growing identity category in enterprise. Existing PAM solutions weren't designed for non-human actors with persistent, broad access requirements. *(Forrester)*

**Prompt Injection: First Confirmed Agent-Mediated Data Exfiltration**
Google Security documents the first confirmed production prompt injection leading to data exfiltration via an enterprise AI agent. Shifts this from theoretical to confirmed enterprise threat. *(Google Security Blog)*

## What CISOs Should Watch This Week
- **Patch velocity** — Organizations receiving Mythos vulnerability reports have days, not weeks, to patch
- **Agent identity governance** — Every agentic AI deployment needs an identity owner before production
- **SEC AI disclosure mapping** — If you haven't mapped AI systems to materiality thresholds, start now

## 📚 Sources
1. Claude Mythos Found 10,000+ Vulnerabilities — Help Net Security
2. SEC Finalizes AI Disclosure Rules — Wall Street Journal  
3. Agentic AI in the SOC — Dark Reading
4. Zero Trust Meets AI — Forrester
5. Prompt Injection in Production — Google Security Blog"""

# ── App state ─────────────────────────────────────────────────────
if "library" not in st.session_state:
    st.session_state.library = [r.copy() for r in SAMPLE_RECORDS]
if "draft" not in st.session_state:
    st.session_state.draft = ""
if "active_record" not in st.session_state:
    st.session_state.active_record = None
if "linkedin_draft" not in st.session_state:
    st.session_state.linkedin_draft = ""

# ── Claude client ─────────────────────────────────────────────────
try:
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    HAS_API = True
except Exception:
    HAS_API = False

# ── Header ────────────────────────────────────────────────────────
st.title("✍️ AI Content Engine — Demo")
st.caption("Demo loaded with sample intelligence library. Write tab uses live Claude API. [View full project on GitHub](https://github.com/usmanaminch/ai-mastery-2026/tree/main/content-engine) · [usmanc.com](https://usmanc.com)")
st.markdown("---")

# ── Stats ─────────────────────────────────────────────────────────
lib = st.session_state.library
col1,col2,col3,col4 = st.columns(4)
col1.metric("Library", len(lib))
col2.metric("T1 Articles", sum(1 for r in lib if r["tier"]==1))
col3.metric("T2 Posts", sum(1 for r in lib if r["tier"]==2))
col4.metric("T3 Reactions", sum(1 for r in lib if r["tier"]==3))

tabs = st.tabs(["📰 Daily Brief", "📚 Library", "✍️ Write"])

# ═══════════════════════════════════════════════════════
# TAB 1: DAILY BRIEF
# ═══════════════════════════════════════════════════════
with tabs[0]:
    st.markdown(f"### 📰 Intelligence Brief — {datetime.now().strftime('%A, %B %d, %Y')}")
    st.caption("Auto-generated from your interest profile. In the real app this is generated fresh daily via web search.")

    profile_themes = ["enterprise AI","agentic SOC","AI security","AI risk","SecOps","AI governance","zero trust","cloud security"]
    st.markdown("**Interest profile** *(derived from library, weighted by tier)*")
    st.markdown("  ".join([f"`{t}`" for t in profile_themes]))
    st.markdown("")

    if HAS_API:
        if st.button("🔄 Generate Fresh Brief (live Claude + web search)", type="primary", use_container_width=True):
            st.info("💡 In the full app, this searches the live web. Demo shows a pre-generated brief below.")
    else:
        st.warning("No API key configured — showing pre-generated brief.")

    st.markdown("---")
    st.markdown(SAMPLE_BRIEF)

    st.markdown("---")
    st.markdown("### Add to Library")
    st.caption("In the full app, each source article has a synthesize button.")
    for src in ["Help Net Security","Wall Street Journal","Dark Reading","Forrester","Google Security Blog"]:
        c1,c2 = st.columns([4,1])
        c1.markdown(f"**{src}**")
        c2.button("＋ Add", key=f"add_{src}", disabled=True, help="Live in full app")

# ═══════════════════════════════════════════════════════
# TAB 2: LIBRARY
# ═══════════════════════════════════════════════════════
with tabs[1]:
    st.subheader("📚 Intelligence Library")
    st.caption(f"{len(lib)} articles synthesized and classified by tier")

    tier_filter = st.radio("Filter", ["All","T1 — Full Article","T2 — Blog Post","T3 — Reaction"], horizontal=True)

    for r in lib:
        tier = r["tier"]
        if tier_filter == "T1 — Full Article" and tier != 1: continue
        if tier_filter == "T2 — Blog Post" and tier != 2: continue
        if tier_filter == "T3 — Reaction" and tier != 3: continue

        tier_color = {"1":"🟡","2":"🟣","3":"🔵"}.get(str(tier),"⚪")
        with st.expander(f"{tier_color} T{tier} — {r['title'][:70]}"):
            c1,c2 = st.columns([3,1])
            with c1:
                st.caption(f"**{r['source_name']}** · {r['date_added']} · {' · '.join(r.get('themes',[])[:3])}")
                try:
                    syn = json.loads(r["synthesis"])
                    st.markdown(f"**TL;DR:** {syn.get('tldr','')}")
                    pts = syn.get("key_points",[])
                    if pts:
                        for p in pts:
                            st.markdown(f"- {p}")
                except Exception:
                    st.markdown(r["synthesis"][:300])
            with c2:
                if st.button(f"✍️ Write T{tier}", key=f"write_{r['id']}"):
                    st.session_state.active_record = r
                    st.rerun()

# ═══════════════════════════════════════════════════════
# TAB 3: WRITE
# ═══════════════════════════════════════════════════════
with tabs[2]:
    st.subheader("✍️ Write")

    # Article selector
    record_titles = [f"T{r['tier']} — {r['title'][:60]}" for r in lib]
    record_map = {f"T{r['tier']} — {r['title'][:60]}": r for r in lib}

    active = st.session_state.active_record
    default_idx = 0
    if active:
        for i,r in enumerate(lib):
            if r["id"] == active["id"]:
                default_idx = i
                break

    selected_title = st.selectbox("Select article to write about", record_titles, index=default_idx)
    record = record_map[selected_title]

    try:
        syn = json.loads(record["synthesis"])
        tldr = syn.get("tldr","")
        key_pts = syn.get("key_points",[])
    except Exception:
        tldr = record.get("synthesis","")[:300]
        key_pts = []

    col_info, col_gen = st.columns([2,1])
    with col_info:
        st.markdown(f"**{record['title']}**")
        st.caption(f"{record['source_name']} · T{record['tier']} · {' · '.join(record.get('themes',[])[:3])}")
        st.markdown(f"*{tldr}*")

    tier = record["tier"]
    with col_gen:
        st.markdown("**Generate**")
        btn_t1 = st.button("📄 T1 Full Article", use_container_width=True, disabled=tier>1, help="T1 sources only")
        btn_t2 = st.button("📝 T2 Blog Post", use_container_width=True, disabled=tier>2)
        btn_t3 = st.button("💬 T3 LinkedIn", use_container_width=True)
        btn_li = st.button("📦 LinkedIn Pack", use_container_width=True)

    if not HAS_API:
        st.warning("No ANTHROPIC_API_KEY in Streamlit secrets — generation disabled in this demo.")
    else:
        pov = st.text_input("Your angle / POV (optional)", placeholder="e.g. focus on federal agency implications")
        kpts_str = "\n".join(f"- {p}" for p in key_pts)

        def run_generate(tier_target, extra=""):
            tier_specs = {
                1: ("1200-1800 word landmark article","TL;DR box, 4-6 sourced h2 sections, pull quotes, CISO implications, Sources"),
                2: ("500-800 word blog post","TL;DR, 3 sections, key takeaway, Sources"),
                3: ("150-300 word LinkedIn post","Hook, 3 emoji-bullet takeaways, CTA, hashtags")
            }
            length, fmt = tier_specs[tier_target]
            prompt = f"""Write a {length} in Usman Chaudhary's voice (Field CISO, Google Cloud).

ARTICLE: {record['title']}
SOURCE: {record['source_name']}
TLDR: {tldr}
KEY POINTS:\n{kpts_str}
ANGLE: {pov or 'Balanced CISO perspective'}

FORMAT: {fmt}
{extra}

Write in first person, direct, no fluff. Cite the source. Use specific numbers."""
            with st.spinner(f"Generating T{tier_target} draft..."):
                resp = client.messages.create(
                    model="claude-sonnet-4-5",
                    max_tokens=2000,
                    messages=[{"role":"user","content":prompt}]
                )
                st.session_state.draft = resp.content[0].text
                st.rerun()

        def run_linkedin_pack():
            prompt = f"""Generate a LinkedIn Content Pack for:
ARTICLE: {record['title']}
TLDR: {tldr}

Create 5 LinkedIn posts with different angles:
1. Board/Executive (risk and investment frame)
2. Practitioner (hands-on CISO)
3. Urgency (why act now)
4. Contrarian (the uncomfortable truth)
5. Story (personal CISO experience)

Each post: 150-250 words, emoji bullets, hashtags.
Write in Usman Chaudhary's voice (Field CISO, Google Cloud)."""
            with st.spinner("Generating LinkedIn Content Pack..."):
                resp = client.messages.create(
                    model="claude-sonnet-4-5",
                    max_tokens=3000,
                    messages=[{"role":"user","content":prompt}]
                )
                st.session_state.linkedin_draft = resp.content[0].text
                st.rerun()

        if btn_t1: run_generate(1)
        if btn_t2: run_generate(2)
        if btn_t3: run_generate(3)
        if btn_li: run_linkedin_pack()

    # Draft output
    if st.session_state.draft:
        st.markdown("---")
        edit_tab, preview_tab = st.tabs(["✏️ Edit","👁️ Preview"])
        with edit_tab:
            edited = st.text_area("Draft", value=st.session_state.draft, height=400)
        with preview_tab:
            st.markdown(st.session_state.draft)

    if st.session_state.linkedin_draft:
        st.markdown("---")
        st.markdown("### 📦 LinkedIn Content Pack")
        st.markdown(st.session_state.linkedin_draft)
