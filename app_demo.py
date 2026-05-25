import streamlit as st
import anthropic
from datetime import datetime

st.set_page_config(
    page_title="AI Chief of Staff — Demo",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 AI Chief of Staff")
st.caption(f"Built by Usman Chaudhary | Field CISO → AI Builder | Demo Mode")

# Demo banner
st.info("📌 **Demo Mode** — This shows how the agent works with sample data. The full version connects to real Gmail and Google Calendar.")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "context_loaded" not in st.session_state:
    st.session_state.context_loaded = False

SYSTEM_PROMPT = """
You are an AI Chief of Staff for a senior security executive at a major tech company.
You help cut through overwhelm, prioritize ruthlessly, and make better decisions faster.

Your operating principles:
1. PRIORITIZE — identify what matters most today
2. SIMPLIFY — turn complexity into clear next actions
3. PROTECT — guard deep work time from shallow tasks
4. DECIDE — give a recommendation, not just options
5. DRAFT — write email replies when asked

Be direct, structured, and brief. No fluff.

Output format when given tasks:
🎯 TOP 3 TODAY
📅 THIS WEEK
🔄 BATCH THESE
🤖 DELEGATE/AUTOMATE
"""

# Realistic fake data for a senior security executive
DEMO_EMAILS = [
    {
        "from": "CISO Council <events@cisocouncil.org>",
        "subject": "Speaking slot available — AI Security Summit, June 12",
        "snippet": "We have a 30-minute slot available on AI security in enterprise environments. Given your recent work on agentic AI risk, we think you'd be a great fit..."
    },
    {
        "from": "Jerome Jackson <jerome.jackson@anthropic.com>",
        "subject": "Re: Field CISO motion at Anthropic",
        "snippet": "Great questions Usman. Let me connect you with our Head of Enterprise Security — I think there's a real conversation to be had here. Are you free next week?"
    },
    {
        "from": "Property Manager <mgmt@cedarproperties.com>",
        "subject": "Cedar lease renewal — HOA approval needed by June 1",
        "snippet": "Hi Usman, just a reminder that we need the signed lease renewal submitted to the HOA by June 1st or we'll need to start the process over. Please advise..."
    },
    {
        "from": "Sarah Chen <s.chen@fortunebank.com>",
        "subject": "AI security framework review — board presentation Friday",
        "snippet": "Usman, our board presentation on AI governance is Friday at 2pm. Can you review the security section by Thursday EOD? Specifically the agentic AI risk slides..."
    },
    {
        "from": "LinkedIn Job Alerts <jobalerts@linkedin.com>",
        "subject": "3 new jobs match: AI Security, Field CISO, Enterprise AI",
        "snippet": "New matches: Head of AI Security at Cohere (San Francisco), Field CISO at Scale AI (Remote), Director AI Risk at OpenAI (San Francisco)..."
    },
    {
        "from": "Team <noreply@notion.so>",
        "subject": "Weekly digest — AI Mastery project updates",
        "snippet": "3 pages updated this week in your AI Mastery workspace. Chief of Staff agent documentation, Month 2 planning notes, Content Engine research..."
    },
    {
        "from": "Dr. Amanda Torres <a.torres@georgetown.edu>",
        "subject": "Guest lecture inquiry — AI & Cybersecurity, MBA program",
        "snippet": "Dear Usman, I teach the Technology Strategy course in our MBA program. Would you be interested in a guest lecture on AI security in the enterprise? Spring semester..."
    },
    {
        "from": "Rocket Money <alerts@rocketmoney.com>",
        "subject": "New subscription detected — $92.98 Namecheap",
        "snippet": "We noticed a new recurring charge on your account: Namecheap $92.98. Is this intentional? Tap to confirm or dispute..."
    }
]

DEMO_EVENTS = [
    {"title": "1:1 with Director of Security", "start": "09:00 AM"},
    {"title": "AI Risk Working Group — Q3 Planning", "start": "11:00 AM"},
    {"title": "Customer Advisory Call — Fortune 500 CISO", "start": "02:00 PM"},
    {"title": "Deep work block — AI Mastery (blocked)", "start": "04:00 PM"},
]

def format_demo_context():
    context = f"Today is {datetime.now().strftime('%A, %B %d, %Y')}\n\n"
    context += "📧 UNREAD EMAILS:\n"
    for e in DEMO_EMAILS:
        context += f"• From: {e['from']}\n"
        context += f"  Subject: {e['subject']}\n"
        context += f"  Preview: {e['snippet'][:120]}\n\n"
    context += "📅 TODAY'S CALENDAR:\n"
    for e in DEMO_EVENTS:
        context += f"• {e['start']}: {e['title']}\n"
    return context

# Sidebar
with st.sidebar:
    st.header("📊 Sample Inbox")

    if st.button("🔄 Load Demo Data", type="primary", use_container_width=True):
        st.session_state.context_loaded = True
        st.success("Demo data loaded!")

    if st.session_state.context_loaded:
        st.subheader("📧 Sample Emails")
        for email in DEMO_EMAILS[:5]:
            with st.expander(email['subject'][:35]):
                st.caption(f"From: {email['from'][:40]}")
                st.caption(email['snippet'][:100])

        st.subheader("📅 Today's Calendar")
        for event in DEMO_EVENTS:
            st.caption(f"• {event['start']}: {event['title']}")

    st.markdown("---")
    st.header("About")
    st.markdown("""
    **Chief of Staff Agent** is Month 1 of a 7-month AI engineering journey.

    **What the full version does:**
    - Connects to real Gmail + Google Calendar
    - Reads your actual inbox
    - Prioritizes your real day

    **Built with:**
    - Anthropic Claude API
    - Gmail API + Google Calendar
    - Python + Streamlit

    [GitHub](https://github.com/usmanaminch/ai-mastery-2026) | [usmanc.com](https://usmanc.com)
    """)

# Chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if not st.session_state.messages:
    if not st.session_state.context_loaded:
        st.markdown("**Click 'Load Demo Data' in the sidebar to get started.**")
    else:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎯 Prioritize my day", use_container_width=True):
                prompt = "Help me prioritize my day"
                st.session_state.messages.append({"role": "user", "content": prompt})
                context = format_demo_context()
                client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
                response = client.messages.create(
                    model="claude-haiku-4-5",
                    max_tokens=800,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": f"{context}\n\n{prompt}"}]
                )
                reply = response.content[0].text
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.rerun()
        with col2:
            if st.button("📧 Triage my inbox", use_container_width=True):
                prompt = "Analyze my emails. Which need urgent replies? Which can I ignore?"
                st.session_state.messages.append({"role": "user", "content": prompt})
                context = format_demo_context()
                client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
                response = client.messages.create(
                    model="claude-haiku-4-5",
                    max_tokens=800,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": f"{context}\n\n{prompt}"}]
                )
                reply = response.content[0].text
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.rerun()

if prompt := st.chat_input("Ask the Chief of Staff anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    context = format_demo_context() if st.session_state.context_loaded else ""
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=600,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": f"{context}\n\n{prompt}" if context else prompt}]
            )
        reply = response.content[0].text
        st.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})
