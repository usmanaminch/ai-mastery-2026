import anthropic
from dotenv import load_dotenv
from datetime import datetime
from google_tools import get_recent_emails, get_todays_calendar, format_context_for_agent
import warnings
import json
warnings.filterwarnings('ignore')

load_dotenv()

client = anthropic.Anthropic()

LIFE_CONTEXT = """
IDENTITY:
- Senior professional at Google, Field CISO
- Target: AI Engineer role at top AI company by end of 2026
- Building AI mastery through daily projects
- Content creator (blogs, articles on AI/security)
- Tone: Professional, direct, warm. Never sycophantic.

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

CAPABILITIES:
1. PRIORITIZE — cut through overwhelm, identify what matters most TODAY
2. DRAFT — write email replies in Usman's voice when asked
3. ACTION — turn emails into specific next actions
4. IGNORE — identify what can be deleted/ignored
5. PROTECT — guard deep work time from shallow tasks

USMAN'S EMAIL VOICE:
- Direct and confident
- Warm but not excessive
- Professional, senior executive tone
- Short paragraphs
- Never uses "hope this finds you well" or similar filler
- Signs off as "Usman"

RULES:
- Be brutally honest, not reassuring
- Always output structured plan, never vague advice
- Flag anything career-critical immediately
- Keep responses tight — no fluff
"""

def analyze_emails(emails):
    """Analyze emails and categorize them"""
    email_summary = []
    for i, email in enumerate(emails):
        email_summary.append(
            f"Email {i+1}:\n"
            f"From: {email.get('from', 'Unknown')}\n"
            f"Subject: {email.get('subject', 'No subject')}\n"
            f"Preview: {email.get('snippet', '')[:150]}\n"
        )
    
    prompt = f"""
    Analyze these {len(emails)} emails and categorize each one:
    
    {chr(10).join(email_summary)}
    
    For each email output:
    - Category: URGENT_REPLY / REPLY_NEEDED / READ_ONLY / IGNORE
    - Why: one line reason
    - Suggested action: specific next step
    
    Format as a clean numbered list.
    """
    
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=800,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

def draft_reply(email, context=""):
    """Draft a reply to a specific email"""
    prompt = f"""
    Draft a reply to this email in Usman's voice:
    
    FROM: {email.get('from', '')}
    SUBJECT: {email.get('subject', '')}
    CONTENT: {email.get('snippet', '')}
    
    Additional context from Usman: {context if context else 'None provided'}
    
    Write ONLY the email body. No subject line. No "Here's a draft" preamble.
    Keep it concise and professional.
    """
    
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

def morning_briefing():
    print("=" * 60)
    print("CHIEF OF STAFF V3 — MORNING BRIEFING")
    print(datetime.now().strftime("%A, %B %d, %Y %I:%M %p"))
    print("=" * 60)
    print("Reading your Gmail and Calendar...\n")
    
    emails = get_recent_emails(10)
    events = get_todays_calendar()
    context = format_context_for_agent(emails, events)
    
    # Morning briefing
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=600,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"{context}\n\nGive me my morning briefing in your standard format."
        }]
    )
    print(response.content[0].text)
    print("\n" + "=" * 60)
    
    # Email analysis
    print("\n📧 ANALYZING YOUR EMAILS...\n")
    analysis = analyze_emails(emails)
    print(analysis)
    print("\n" + "=" * 60)
    
    # Interactive mode
    print("\nCOMMANDS:")
    print("  'draft [1-10]' — draft reply for email number")
    print("  'quit' — exit")
    print("  Or just chat naturally\n")
    
    conversation = []
    
    while True:
        user_input = input("You: ").strip()
        
        if not user_input:
            continue
        elif user_input.lower() == 'quit':
            break
        elif user_input.lower().startswith('draft '):
            try:
                email_num = int(user_input.split(' ')[1]) - 1
                if 0 <= email_num < len(emails):
                    print(f"\n📝 Drafting reply to: {emails[email_num].get('subject', 'No subject')}")
                    additional = input("Any context to add? (press Enter to skip): ").strip()
                    draft = draft_reply(emails[email_num], additional)
                    print(f"\n--- DRAFT REPLY ---\n{draft}\n-------------------\n")
                else:
                    print("Invalid email number")
            except (ValueError, IndexError):
                print("Usage: draft [number] e.g. 'draft 3'")
        else:
            conversation.append({
                "role": "user",
                "content": f"Context: {context}\n\nQuestion: {user_input}"
            })
            
            response = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=500,
                system=SYSTEM_PROMPT,
                messages=conversation
            )
            
            reply = response.content[0].text
            conversation.append({"role": "assistant", "content": reply})
            print(f"\nCoS: {reply}\n")

if __name__ == "__main__":
    morning_briefing()