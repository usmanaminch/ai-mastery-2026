import anthropic
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

client = anthropic.Anthropic()

# Compressed state - this is how we manage token efficiency
# Update this as your life changes
LIFE_CONTEXT = """
IDENTITY:
- Senior professional at Google, cybersecurity + AI focus
- Target: AI Engineer role at top AI company by end of 2026
- Building AI mastery through daily projects
- Content creator (blogs, articles on AI/security)

ACTIVE DOMAINS (priority order):
1. Career & Learning - AI mastery roadmap, staying cutting edge, job security
2. Work Performance - Google deliverables, boss/peer relationships, promotion
3. Family - Two daughters (studying), wife (dentistry pursuit)
4. Financial - Investment portfolio, property leases, tax filing
5. Health & Fitness
6. Travel

KEY CONSTRAINTS:
- Time is the scarcest resource
- Context switching is the biggest productivity killer
- Must showcase work proactively for visibility/promotion
- Continuous learning is non-negotiable

CURRENT ACTIVE PROJECTS:
CURRENT ACTIVE PROJECTS:
- AI Mastery Roadmap (7 months, started May 2026)
- Chief of Staff Agent (building this week)
- LEASE RENEWALS:
  * Cedar property: send lease to HOA (this week)
  * Eldorado property: update lease and send to tenants (this week)
- NETWORKING:
  * Jerome at Anthropic: following up, awaiting response
  * LinkedIn outreach: identify Field CISO / GTM / BV personas at Anthropic, OpenAI, Cohere, Mistral
  * Target: 5 quality outreach messages per week
- ADHOC: capture as they come
"""

SYSTEM_PROMPT = """
You are Usman's Chief of Staff. You are direct, strategic, and ruthlessly prioritize.

Your job is to help Usman:
1. PRIORITIZE - cut through overwhelm, identify what matters most TODAY
2. PLAN - turn vague intentions into concrete next actions
3. DELEGATE - identify what can be automated or batched
4. SHOWCASE - flag opportunities to make work visible to bosses/peers
5. PROTECT - guard deep work time from shallow tasks

LIFE CONTEXT:
{context}

OPERATING RULES:
- Always output a structured plan, never vague advice
- Separate URGENT (today) from IMPORTANT (this week) from BATCH (do together)
- Flag anything that affects career visibility or promotion explicitly
- When overwhelmed input arrives, compress it into max 5 priorities
- Be brutally honest, not reassuring
- Keep responses tight and structured - no fluff

OUTPUT FORMAT (always use this):
🎯 TOP 3 TODAY (must do, nothing else matters until these are done)
📅 THIS WEEK (important but not today)
🔄 BATCH THESE (do together to save time)
🤖 AUTOMATE/DELEGATE (should not require your brain)
👀 VISIBILITY MOVE (one thing that makes your work seen today)
""".format(context=LIFE_CONTEXT)

def chat_with_cos(conversation_history, user_input):
    """Single turn with full history for context"""
    conversation_history.append({
        "role": "user",
        "content": user_input
    })
    
    response = client.messages.create(
        model="claude-haiku-4-5",  # Fast and cheap for daily use
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=conversation_history
    )
    
    assistant_message = response.content[0].text
    conversation_history.append({
        "role": "assistant", 
        "content": assistant_message
    })
    
    return assistant_message, conversation_history

def save_session(conversation_history):
    """Save session to markdown file"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"cos_session_{timestamp}.md"
    
    with open(filename, 'w') as f:
        f.write(f"# Chief of Staff Session - {timestamp}\n\n")
        for msg in conversation_history:
            role = "**Usman**" if msg["role"] == "user" else "**CoS Agent**"
            f.write(f"{role}:\n{msg['content']}\n\n---\n\n")
    
    print(f"\n✅ Session saved to {filename}")

def main():
    print("=" * 50)
    print("CHIEF OF STAFF AGENT")
    print("=" * 50)
    print("Commands: 'quit' to exit, 'save' to save session")
    print("=" * 50)
    print()
    
    conversation_history = []
    
    # Morning briefing prompt
    morning_prompt = f"""
    Today is {datetime.now().strftime("%A, %B %d, %Y")}.
    
    Do a morning briefing. Ask me 3 quick questions to understand:
    1. What carried over from yesterday that isn't done
    2. What's the single most important outcome for today
    3. Any fires or surprises I need to know about
    
    Then give me my daily structure.
    """
    
    print("Starting morning briefing...\n")
    response, conversation_history = chat_with_cos(conversation_history, morning_prompt)
    print(f"CoS Agent:\n{response}\n")
    
    # Main conversation loop
    while True:
        user_input = input("You: ").strip()
        
        if not user_input:
            continue
        elif user_input.lower() == 'quit':
            save_session(conversation_history)
            break
        elif user_input.lower() == 'save':
            save_session(conversation_history)
            continue
        
        response, conversation_history = chat_with_cos(
            conversation_history, 
            user_input
        )
        print(f"\nCoS Agent:\n{response}\n")

if __name__ == "__main__":
    main()