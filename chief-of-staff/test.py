import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-haiku-4-5",
    max_tokens=50,
    messages=[
        {"role": "user", "content": "Say 'Hour 1 complete' and nothing else."}
    ]
)

print(response.content[0].text)