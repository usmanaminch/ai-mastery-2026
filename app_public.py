import streamlit as st
import anthropic
from datetime import datetime

st.set_page_config(
    page_title="Chief of Staff Agent",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 AI Chief of Staff")
st.caption(f"Built by Usman Chaudhary | Field CISO → AI Engineer | {datetime.now().strftime('%B %d, %Y')}")

if "messages" not in st.session_state:
    st.session_state.messages = []

SYSTEM_PROMPT = """
You are an AI Chief of Staff. You help busy professionals cut through overwhelm, prioritize ruthlessly, and make better decisions faster.

Your operating principles:
1. PRIORITIZE — identify what matters most today
2. SIMPLIFY — turn complexity into clear next actions  
3. PROTECT — guard deep work time from shallow tasks
4. DECIDE — give a recommendation, not just options

Be direct, structured, and brief. No fluff.

Output format when given a list of tasks:
🎯 TOP 3 TODAY
📅 THIS WEEK
🔄 BATCH THESE
🤖 DELEGATE/AUTOMATE
"""

with st.sidebar:
    st.header("About This Project")
    st.markdown("""
    **Chief of Staff Agent** is Week 1 of my 7-month AI Engineering journey.
    
    **What it does:**
    - Connects to Gmail + Google Calendar
    - Uses Claude to prioritize your day
    - Acts as an intelligent personal assistant
    
    **Built with:**
    - Anthropic Claude API
    - Gmail API + Google Calendar API  
    - Python + Streamlit
    
    **The Journey:**
    - 🔨 May: Agent Development
    - 📊 June: Content Engine
    - 💰 July: Quant Finance AI
    - 🤖 Aug: Local Models
    - 📈 Sep: Trading Signals
    - 🌐 Oct: Portfolio Site
    """)
    st.markdown("---")
    st.markdown("**Connect:**")
    st.markdown("[GitHub](https://github.com/usmanaminch) | [LinkedIn](https://linkedin.com/in/usmanaminch)")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if not st.session_state.messages:
    st.info("Ask anything about productivity, priorities, or decision-making.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎯 Help me prioritize my day", use_container_width=True):
            prompt = "Help me prioritize my day"
            st.session_state.messages.append({"role": "user", "content": prompt})
            client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
            response = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=500,
                system=SYSTEM_PROMPT,
                messages=st.session_state.messages
            )
            reply = response.content[0].text
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()
    with col2:
        if st.button("😰 I'm overwhelmed, where do I start?", use_container_width=True):
            prompt = "I'm overwhelmed, where do I start?"
            st.session_state.messages.append({"role": "user", "content": prompt})
            client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
            response = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=500,
                system=SYSTEM_PROMPT,
                messages=st.session_state.messages
            )
            reply = response.content[0].text
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()

if prompt := st.chat_input("Ask your Chief of Staff anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=500,
                system=SYSTEM_PROMPT,
                messages=[{"role": m["role"], "content": m["content"]}
                          for m in st.session_state.messages]
            )
        reply = response.content[0].text
        st.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})
