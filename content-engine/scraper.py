import requests
from bs4 import BeautifulSoup
import anthropic
from dotenv import load_dotenv
import warnings
import json
import re
from urllib.parse import urlparse, parse_qs

warnings.filterwarnings('ignore')
load_dotenv()

client = anthropic.Anthropic()

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

def fetch_article(url: str) -> dict:
    """Fetch and extract article content from a URL"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        for tag in soup(['script', 'style', 'nav', 'footer',
                        'header', 'aside', 'iframe', 'form']):
            tag.decompose()

        title = ""
        if soup.find('h1'):
            title = soup.find('h1').get_text(strip=True)
        elif soup.find('title'):
            title = soup.find('title').get_text(strip=True)

        author = ""
        for selector in ['[rel="author"]', '.author', '[class*="author"]',
                        '[class*="byline"]', 'meta[name="author"]']:
            el = soup.select_one(selector)
            if el:
                author = el.get('content', el.get_text(strip=True))
                break

        content = ""
        for selector in ['article', 'main', '[class*="content"]',
                        '[class*="post"]', '[class*="article"]']:
            el = soup.select_one(selector)
            if el:
                content = el.get_text(separator=' ', strip=True)
                break

        if not content:
            content = soup.get_text(separator=' ', strip=True)

        content = ' '.join(content.split())[:8000]

        domain = urlparse(url).netloc
        source_name = domain.replace('www.', '').replace('cloud.', 'Google Cloud ')

        return {
            "success": True,
            "url": url,
            "title": title,
            "author": author,
            "source_name": source_name,
            "content": content
        }

    except Exception as e:
        return {
            "success": False,
            "url": url,
            "error": str(e),
            "title": "", "author": "",
            "source_name": "", "content": ""
        }


def fetch_youtube_transcript(url: str) -> dict:
    """Fetch transcript from YouTube video or podcast"""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        video_id = None
        if 'youtu.be/' in url:
            video_id = url.split('youtu.be/')[1].split('?')[0]
        elif 'youtube.com/watch' in url:
            parsed = urlparse(url)
            video_id = parse_qs(parsed.query).get('v', [None])[0]
        elif 'youtube.com' in url:
            match = re.search(r'[?&]v=([^&]+)', url)
            if match:
                video_id = match.group(1)

        if not video_id:
            return {"success": False, "error": "Could not extract video ID"}

        full_text = ""
        try:
            ytt_api = YouTubeTranscriptApi()
            fetched = ytt_api.fetch(video_id)
            full_text = ' '.join([t.text for t in fetched])
        except Exception:
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                transcript = transcript_list.find_transcript(['en'])
                fetched = transcript.fetch()
                full_text = ' '.join([
                    t['text'] if isinstance(t, dict) else t.text
                    for t in fetched
                ])
            except Exception as e2:
                return {"success": False, "error": f"Transcript error: {str(e2)}"}

        title = ""
        author = ""
        try:
            oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
            r = requests.get(oembed_url, timeout=5)
            if r.ok:
                data = r.json()
                title = data.get('title', '')
                author = data.get('author_name', '')
        except Exception:
            pass

        return {
            "success": True,
            "url": url,
            "title": title,
            "author": author,
            "source_name": "YouTube",
            "content": full_text[:8000]
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def synthesize_article(article: dict, depth: str = "quick") -> dict:
    """
    Synthesize article content into intelligence record.

    depth = "quick"  -> Haiku, TLDR + bullets for daily scanning
    depth = "deep"   -> Sonnet, full breakdown for writing

    Model routing:
    - Quick: Haiku — fast and cheap, good enough for scanning
    - Deep: Sonnet — quality matters when this feeds your writing
    """
    if not article["content"]:
        return {"success": False, "error": "No content to synthesize"}

    model = "claude-sonnet-4-5" if depth == "deep" else "claude-haiku-4-5"

    if depth == "quick":
        prompt = f"""You are analyzing an article for a Field CISO and AI Security Executive.
His focus: AI security, agentic AI risk, enterprise security strategy, SOC transformation.
He writes for CISO and board audiences and coins memorable terms.

ARTICLE TITLE: {article['title']}
AUTHOR: {article['author']}
SOURCE: {article['source_name']}
URL: {article['url']}

CONTENT:
{article['content'][:6000]}

Respond ONLY with valid JSON, no markdown:

{{
  "title": "clean article title",
  "author": "author name or Unknown",
  "tldr": "ONE sentence — the single most important point from this article",
  "key_points": [
    "Point 1 — specific claim, stat, or argument from the article",
    "Point 2 — specific claim, stat, or argument from the article",
    "Point 3 — specific claim, stat, or argument from the article",
    "Point 4 — specific claim, stat, or argument from the article"
  ],
  "why_timely": "One sentence on why this matters right now for CISOs",
  "key_quotes": ["most notable quote if any"],
  "suggested_piece": {{
    "what_to_write": "Specific article or post concept — not vague",
    "why_now": "What makes this urgent or timely today",
    "audience": "Who specifically — e.g. Fortune 500 CISOs, security boards, SOC leaders",
    "value_to_audience": "What they get from reading it — specific benefit",
    "usman_angle": "What Usman adds from his Google Cloud CISO experience that others cannot",
    "coined_term": "A memorable term Usman could coin for the core concept",
    "recommended_tier": 1
  }},
  "tier": 1,
  "themes": ["theme1", "theme2"]
}}

Tier 1 = worth a full article on usmanc.com (strong original POV, data-rich, evergreen)
Tier 2 = substantive LinkedIn post 300-500 words (good POV but not full article)
Tier 3 = quick LinkedIn reaction 150-300 words (timely, top 3 takeaways, link to source)

Themes: agentic SOC, AI security, AI governance, post-quantum, cloud security,
zero trust, SecOps, threat intelligence, AI risk, enterprise AI, vibe coding, data strategy"""

    else:  # deep — Sonnet for quality
        prompt = f"""You are doing a deep synthesis of an article for a Field CISO writing a detailed piece.
He needs everything to write without reading the source himself.
Background: Field CISO at Google Cloud, Fortune 500 board advisor, 17 years in security.
Audience: CISOs, boards, senior security leaders.

ARTICLE TITLE: {article['title']}
AUTHOR: {article['author']}
SOURCE: {article['source_name']}
URL: {article['url']}

CONTENT:
{article['content'][:8000]}

Respond ONLY with valid JSON, no markdown:

{{
  "title": "clean article title",
  "author": "author name or Unknown",
  "tldr": "ONE sentence — the single most important point",
  "core_argument": "2-3 sentences: the central thesis",
  "key_points": [
    "Point 1 with specific detail, stat, or claim and its source",
    "Point 2 with specific detail, stat, or claim and its source",
    "Point 3 with specific detail, stat, or claim and its source",
    "Point 4 with specific detail, stat, or claim and its source",
    "Point 5 with specific detail, stat, or claim and its source"
  ],
  "key_stats": ["stat with attribution", "stat with attribution"],
  "key_quotes": ["exact notable quote 1", "exact notable quote 2"],
  "frameworks_mentioned": ["framework or model name"],
  "counterarguments": "limitations or opposing views mentioned",
  "why_timely": "2 sentences on urgency for CISOs",
  "suggested_piece": {{
    "what_to_write": "Specific article concept with working title",
    "why_now": "What makes this urgent or timely today",
    "audience": "Who specifically — e.g. Fortune 500 CISOs, security boards, SOC leaders",
    "value_to_audience": "What they get from reading — specific benefit",
    "usman_angle": "What Usman adds from Google Cloud CISO experience that others cannot",
    "coined_term": "A memorable term Usman could coin for the core concept",
    "recommended_tier": 1
  }},
  "draft_outline": {{
    "headline": "suggested article headline using the coined term",
    "hook": "suggested opening line that creates urgency",
    "sections": ["section 1 title", "section 2 title", "section 3 title"],
    "call_to_action": "suggested closing CTA"
  }},
  "tier": 1,
  "themes": ["theme1", "theme2"]
}}

Tier 1 = full article on usmanc.com
Tier 2 = substantive LinkedIn post 300-500 words
Tier 3 = quick LinkedIn reaction 150-300 words, top 3 takeaways, link to source

Themes: agentic SOC, AI security, AI governance, post-quantum, cloud security,
zero trust, SecOps, threat intelligence, AI risk, enterprise AI, vibe coding, data strategy"""

    response = client.messages.create(
        model=model,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        result = json.loads(response.content[0].text)
        result["success"] = True
        result["depth"] = depth
        result["model_used"] = model
        return result
    except json.JSONDecodeError:
        text = response.content[0].text
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > 0:
            try:
                result = json.loads(text[start:end])
                result["success"] = True
                result["depth"] = depth
                result["model_used"] = model
                return result
            except Exception:
                pass
        return {"success": False, "error": "Failed to parse synthesis response"}


def process_url(url: str, depth: str = "quick") -> dict:
    """Full pipeline: fetch → synthesize → return record data"""
    print(f"Fetching: {url}")

    if 'youtube.com' in url or 'youtu.be' in url:
        article = fetch_youtube_transcript(url)
    else:
        article = fetch_article(url)

    if not article["success"]:
        print(f"Failed to fetch: {article.get('error', 'Unknown error')}")
        return {"success": False, "error": article.get("error")}

    model_name = 'Sonnet' if depth == 'deep' else 'Haiku'
    print(f"Synthesizing ({depth}) with {model_name}: {article['title'][:60]}...")
    synthesis = synthesize_article(article, depth=depth)

    if not synthesis["success"]:
        return {"success": False, "error": synthesis.get("error")}

    return {
        "success": True,
        "url": url,
        "source_name": article["source_name"],
        "raw_content": article["content"],
        **synthesis
    }


def process_pasted_text(
    text: str,
    url: str,
    source_name: str,
    author: str,
    title: str,
    depth: str = "quick"
) -> dict:
    """Process manually pasted article text for Medium, LinkedIn, paywalled content"""
    article = {
        "success": True,
        "url": url,
        "title": title,
        "author": author,
        "source_name": source_name,
        "content": text[:8000]
    }
    model_name = 'Sonnet' if depth == 'deep' else 'Haiku'
    print(f"Synthesizing pasted content ({depth}) with {model_name}: {title[:60]}...")
    synthesis = synthesize_article(article, depth=depth)
    if not synthesis["success"]:
        return {"success": False, "error": synthesis.get("error")}
    return {
        "success": True,
        "url": url,
        "source_name": source_name,
        "raw_content": text[:2000],
        **synthesis
    }


if __name__ == "__main__":
    test_url = 'https://cloud.google.com/blog/topics/threat-intelligence/defending-enterprise-ai-vulnerabilities'

    print("=== QUICK SYNTHESIS (Haiku) ===")
    result = process_url(test_url, depth="quick")
    if result['success']:
        print(f"TLDR: {result.get('tldr')}")
        print(f"Key Points:")
        for p in result.get('key_points', []):
            print(f"  • {p}")
        sp = result.get('suggested_piece', {})
        print(f"\nSuggested Piece:")
        print(f"  What: {sp.get('what_to_write')}")
        print(f"  Audience: {sp.get('audience')}")
        print(f"  Usman's angle: {sp.get('usman_angle')}")
        print(f"  Coined term: {sp.get('coined_term')}")
        print(f"  Tier: {sp.get('recommended_tier')}")
    else:
        print(f"Failed: {result['error']}")
