import anthropic
from dotenv import load_dotenv
from datetime import datetime
from google_tools import get_recent_emails, get_todays_calendar, format_context_for_agent
import warnings
warnings.filterwarnings('ignore')

load_dotenv()

client = anthropic.Anthropic()

LIFE_CONTEXT = """
IDENTITY:
- Senior professional at Google, Field CISO
- Target: AI Engineer role at top AI company by end of 2026
- Building AI mastery through daily projects
- Content creator (blogs, articles on AI/security)

ACTIVE PRIORITIES THIS WEEK:
1. Cedar property: send lease to HOA (urgent)
2. Eldorado property: update lease and send to tenants (urgent)
3. Identify Anthropic/AI company contacts on LinkedIn
4. Follow up with Jerome at Anthropic
5. AI Mastery learning (daily)
"""

SYSTEM_PROMPT = """
You are Usman's Chief of Staff. You have access to his real Gmail and Calendar.
Be direct, strategic, ruthlessly prioritize.

Your job:
1. PRIORITIZE - cut through overwhelm, identify what matters most TODAY
2. ACTION - turn emails into specific next actions
3. IGNORE - identify what can be deleted/ignored
4. PROTECT - guard his deep work time

LIFE CONTEXT:
{context}

RULES:
- Be brutally honest, not reassuring
- Always output structured plan, never vague advice
- Flag anything career-critical immediately
- Keep responses tight — no fluff

OUTPUT FORMAT:
🎯 TOP 3 ACTIONS TODAY
📧 EMAILS THAT NEED RESPONSE (with suggested reply)
🗑️ IGNORE THESE (explain why)
📅 CALENDAR GAPS (suggest how to use free time)
👀 ONE VISIBILITY MOVE
""".format(context=LIFE_CONTEXT)

def morning_briefing():
    print("=" * 50)
    print("CHIEF OF STAFF — MORNING BRIEFING")
    print(datetime.now().strftime("%A, %B %d, %Y %I:%M %p"))
    print("=" * 50)
    print("Reading your Gmail and Calendar...\n")
    
    # Get real data
    emails = get_recent_emails(15)
    events = get_todays_calendar()
    real_world_context = format_context_for_agent(emails, events)
    
    # Send to Claude
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"{real_world_context}\n\nGive me my morning briefing. What should I focus on today?"
        }]
    )
    
    print(response.content[0].text)
    print("\n" + "=" * 50)
    
    # Interactive follow-up
    print("\nAsk me anything about your day (or 'quit' to exit):\n")
    conversation = []
    
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == 'quit':
            break
        if not user_input:
            continue
            
        conversation.append({
            "role": "user",
            "content": f"Context: {real_world_context}\n\nQuestion: {user_input}"
        })
        
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=conversation
        )
        
        reply = response.content[0].text
        conversation.append({
            "role": "assistant",
            "content": reply
        })
        
        print(f"\nCoS: {reply}\n")

if __name__ == "__main__":
    morning_briefing()