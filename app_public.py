import streamlit as st
import anthropic
from datetime import datetime
import json
import pickle
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Chief of Staff Agent",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 AI Chief of Staff")
st.caption(f"Built by Usman Chaudhary | Field CISO → AI Builder | {datetime.now().strftime('%B %d, %Y')}")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "emails" not in st.session_state:
    st.session_state.emails = []
if "events" not in st.session_state:
    st.session_state.events = []
if "context_loaded" not in st.session_state:
    st.session_state.context_loaded = False

SYSTEM_PROMPT = """
You are an AI Chief of Staff. You help busy professionals cut through overwhelm, prioritize ruthlessly, and make better decisions faster.

Your operating principles:
1. PRIORITIZE — identify what matters most today
2. SIMPLIFY — turn complexity into clear next actions
3. PROTECT — guard deep work time from shallow tasks
4. DECIDE — give a recommendation, not just options
5. DRAFT — write email replies when asked

Be direct, structured, and brief. No fluff.

Output format when given a list of tasks:
🎯 TOP 3 TODAY
📅 THIS WEEK
🔄 BATCH THESE
🤖 DELEGATE/AUTOMATE
"""

def get_google_creds():
    """Load credentials from Streamlit secrets"""
    try:
        token_data = json.loads(st.secrets["GOOGLE_TOKEN"])
        creds = Credentials(
            token=token_data.get('token'),
            refresh_token=token_data.get('refresh_token'),
            token_uri=token_data.get('token_uri'),
            client_id=token_data.get('client_id'),
            client_secret=token_data.get('client_secret'),
            scopes=token_data.get('scopes')
        )
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        return creds
    except Exception as e:
        st.error(f"Gmail auth error: {str(e)}")
        return None

def get_emails(max_results=10):
    """Fetch unread emails"""
    try:
        creds = get_google_creds()
        if not creds:
            return []
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().messages().list(
            userId='me',
            labelIds=['INBOX', 'UNREAD'],
            maxResults=max_results
        ).execute()
        messages = results.get('messages', [])
        emails = []
        for msg in messages:
            message = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()
            headers = message['payload']['headers']
            email_data = {'snippet': message.get('snippet', '')}
            for h in headers:
                if h['name'] == 'From':
                    email_data['from'] = h['value']
                elif h['name'] == 'Subject':
                    email_data['subject'] = h['value']
            emails.append(email_data)
        return emails
    except Exception as e:
        st.error(f"Gmail error: {str(e)}")
        return []

def get_calendar():
    """Fetch today's events"""
    try:
        creds = get_google_creds()
        if not creds:
            return []
        service = build('calendar', 'v3', credentials=creds)
        now = datetime.utcnow()
        start = now.replace(hour=0, minute=0, second=0).isoformat() + 'Z'
        end = now.replace(hour=23, minute=59, second=59).isoformat() + 'Z'
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start,
            timeMax=end,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        return [{'title': e.get('summary', 'No title'),
                 'start': e['start'].get('dateTime', e['start'].get('date'))}
                for e in events]
    except Exception as e:
        st.error(f"Calendar error: {str(e)}")
        return []

def format_context(emails, events):
    context = f"Today is {datetime.now().strftime('%A, %B %d, %Y')}\n\n"
    context += "📧 UNREAD EMAILS:\n"
    if emails:
        for e in emails:
            context += f"• From: {e.get('from','')[:50]}\n"
            context += f"  Subject: {e.get('subject','')}\n"
            context += f"  Preview: {e.get('snippet','')[:100]}\n\n"
    else:
        context += "No unread emails.\n\n"
    context += "📅 TODAY'S CALENDAR:\n"
    if events:
        for e in events:
            context += f"• {e['start']}: {e['title']}\n"
    else:
        context += "No events today.\n"
    return context

# Sidebar
with st.sidebar:
    st.header("📊 Your World")
    if st.button("🔄 Load Gmail & Calendar", type="primary", use_container_width=True):
        with st.spinner("Reading your inbox..."):
            st.session_state.emails = get_emails(10)
            st.session_state.events = get_calendar()
            st.session_state.context_loaded = True
            if st.session_state.emails or st.session_state.events:
                st.success("Loaded!")
            else:
                st.warning("No data — check Gmail connection")

    if st.session_state.context_loaded:
        st.subheader("📧 Unread Emails")
        if st.session_state.emails:
            for email in st.session_state.emails[:5]:
                with st.expander(email.get('subject','No subject')[:40]):
                    st.caption(f"From: {email.get('from','')[:40]}")
                    st.caption(email.get('snippet','')[:100])
        else:
            st.caption("No unread emails")

        st.subheader("📅 Today's Calendar")
        if st.session_state.events:
            for event in st.session_state.events:
                st.caption(f"• {event['title']}")
        else:
            st.caption("No events today")

    st.markdown("---")
    st.header("About")
    st.markdown("""
    **Chief of Staff Agent** — Month 1 of a 7-month AI journey.
    
    **Built with:**
    - Anthropic Claude API
    - Gmail API + Google Calendar
    - Python + Streamlit
    
    [GitHub](https://github.com/usmanaminch) | [usmanc.com](https://usmanc.com)
    """)

# Chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if not st.session_state.messages:
    st.info("Load your Gmail and Calendar from the sidebar, then ask me anything.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎯 Prioritize my day", use_container_width=True):
            prompt = "Help me prioritize my day"
            st.session_state.messages.append({"role": "user", "content": prompt})
            context = format_context(st.session_state.emails, st.session_state.events) if st.session_state.context_loaded else ""
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
            if not st.session_state.context_loaded:
                st.warning("Load Gmail first from the sidebar.")
            else:
                prompt = "Analyze my emails. Which need urgent replies? Which can I ignore?"
                st.session_state.messages.append({"role": "user", "content": prompt})
                context = format_context(st.session_state.emails, st.session_state.events)
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

if prompt := st.chat_input("Ask your Chief of Staff anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    context = format_context(st.session_state.emails, st.session_state.events) if st.session_state.context_loaded else ""
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
