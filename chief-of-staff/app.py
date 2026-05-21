import streamlit as st
import anthropic
from dotenv import load_dotenv
from datetime import datetime
from google_tools import get_recent_emails, get_todays_calendar, format_context_for_agent
import warnings
warnings.filterwarnings('ignore')

load_dotenv()

# Page config
st.set_page_config(
    page_title="Chief of Staff",
    page_icon="🎯",
    layout="wide"
)

# Styling
st.markdown("""
<style>
    .main { background-color: #0f0f0f; }
    .stTextInput > div > div > input { background-color: #1e1e1e; color: white; }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🎯 Chief of Staff")
st.caption(f"Good {'morning' if datetime.now().hour < 12 else 'evening'}, Usman. {datetime.now().strftime('%A, %B %d, %Y')}")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "context_loaded" not in st.session_state:
    st.session_state.context_loaded = False
if "email_data" not in st.session_state:
    st.session_state.email_data = []
if "calendar_data" not in st.session_state:
    st.session_state.calendar_data = []

LIFE_CONTEXT = """
IDENTITY:
- Senior professional at Google, Field CISO
- Target: AI Engineer role at top AI company by end of 2026
- Building AI mastery through daily projects

ACTIVE PRIORITIES THIS WEEK:
1. Cedar property: send lease to HOA (urgent)
2. Eldorado property: update lease and send to tenants (urgent)
3. Identify Anthropic/AI company contacts on LinkedIn
4. Follow up with Jerome at Anthropic
5. AI Mastery learning (daily)
"""

SYSTEM_PROMPT = f"""
You are Usman's Chief of Staff. You have access to his real Gmail and Calendar.
Be direct, strategic, ruthlessly prioritize.

LIFE CONTEXT:
{LIFE_CONTEXT}

RULES:
- Be brutally honest, not reassuring
- Always output structured plan, never vague advice
- Flag anything career-critical immediately
- Keep responses tight — no fluff
"""

# Sidebar — Gmail and Calendar
with st.sidebar:
    st.header("📊 Your World")
    
    if st.button("🔄 Load Gmail & Calendar", type="primary"):
        with st.spinner("Reading your inbox..."):
            try:
                st.session_state.email_data = get_recent_emails(10)
                st.session_state.calendar_data = get_todays_calendar()
                st.session_state.context_loaded = True
                st.success("Loaded!")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    if st.session_state.context_loaded:
        st.subheader("📧 Unread Emails")
        for email in st.session_state.email_data[:5]:
            with st.expander(email.get('subject', 'No subject')[:40]):
                st.caption(f"From: {email.get('from', '')[:40]}")
                st.caption(email.get('snippet', '')[:100])
        
        st.subheader("📅 Today's Calendar")
        if st.session_state.calendar_data:
            for event in st.session_state.calendar_data:
                st.caption(f"• {event['title']}")
        else:
            st.caption("No events today")

# Main chat area
st.subheader("💬 Chat with your Chief of Staff")

# Display messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Morning briefing button
if not st.session_state.messages:
    if st.button("🌅 Get Morning Briefing"):
        if not st.session_state.context_loaded:
            st.warning("Click 'Load Gmail & Calendar' in the sidebar first.")
        else:
            context = format_context_for_agent(
                st.session_state.email_data,
                st.session_state.calendar_data
            )
            
            client = anthropic.Anthropic()
            with st.spinner("Preparing your briefing..."):
                response = client.messages.create(
                    model="claude-haiku-4-5",
                    max_tokens=1000,
                    system=SYSTEM_PROMPT,
                    messages=[{
                        "role": "user",
                        "content": f"{context}\n\nGive me my morning briefing."
                    }]
                )
            
            briefing = response.content[0].text
            st.session_state.messages.append({
                "role": "assistant",
                "content": briefing
            })
            st.rerun()

# Chat input
if prompt := st.chat_input("Ask your Chief of Staff anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    context = ""
    if st.session_state.context_loaded:
        context = format_context_for_agent(
            st.session_state.email_data,
            st.session_state.calendar_data
        )
    
    client = anthropic.Anthropic()
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=500,
                system=SYSTEM_PROMPT,
                messages=[
                    *[{"role": m["role"], "content": m["content"]} 
                      for m in st.session_state.messages[:-1]],
                    {"role": "user", "content": f"{context}\n\n{prompt}"}
                ]
            )
        reply = response.content[0].text
        st.markdown(reply)
    
    st.session_state.messages.append({
        "role": "assistant",
        "content": reply
    })