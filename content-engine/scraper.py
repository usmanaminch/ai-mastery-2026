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
        from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

        # Extract video ID
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

        # Fetch transcript using new API style
        try:
            ytt_api = YouTubeTranscriptApi()
            fetched = ytt_api.fetch(video_id)
            full_text = ' '.join([t.text for t in fetched])
        except Exception:
            # Fallback for older API versions
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = transcript_list.find_transcript(['en'])
            fetched = transcript.fetch()
            full_text = ' '.join([t['text'] if isinstance(t, dict) else t.text for t in fetched])

        # Get video title via oEmbed
        title = ""
        author = ""
        try:
            oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
            r = requests.get(oembed_url, timeout=5)
            if r.ok:
                data = r.json()
                title = data.get('title', '')
                author = data.get('author_name', '')
        except:
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
    Synthesize article content.
    depth = "quick" → 4-sentence brief for daily scanning
    depth = "deep"  → full breakdown for writing
    """
    if not article["content"]:
        return {"success": False, "error": "No content to synthesize"}

    if depth == "quick":
        prompt = f"""You are analyzing an article for a Field CISO and AI Security Executive.
His focus: AI security, agentic AI risk, enterprise security strategy, SOC transformation.
He writes for CISO and board audiences. He coins memorable terms.

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
  "synthesis": "4 sentences: core argument, key evidence, main implication for enterprise security, why it matters now",
  "key_quotes": ["most notable quote if any", "second notable quote if any"],
  "content_angle": "1-2 sentences: how Usman could use this — what unique POV from his Google Cloud and CISO experience could he add. Suggest a coined term if applicable.",
  "tier": 1,
  "themes": ["theme1", "theme2"],
  "why_timely": "1 sentence on why this matters right now"
}}

Tier 1 = worth a full article (strong POV, data-rich, evergreen)
Tier 3 = worth a quick LinkedIn reaction (timely, straightforward)

Themes: agentic SOC, AI security, AI governance, post-quantum, cloud security,
zero trust, SecOps, threat intelligence, AI risk, enterprise AI, vibe coding, data strategy"""

    else:  # deep synthesis
        prompt = f"""You are doing a deep synthesis of an article for a Field CISO writing a detailed piece.
He needs everything to write a full article WITHOUT reading the source himself.
His background: Field CISO at Google Cloud, advisor to Fortune 500 boards, 17 years in security.
His audience: CISOs, boards, senior security leaders.

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
  "core_argument": "2-3 sentences: the central thesis of the article",
  "key_points": [
    "Point 1 with specific detail/stat/claim",
    "Point 2 with specific detail/stat/claim",
    "Point 3 with specific detail/stat/claim",
    "Point 4 with specific detail/stat/claim",
    "Point 5 with specific detail/stat/claim"
  ],
  "key_stats": ["stat 1 with attribution", "stat 2 with attribution"],
  "key_quotes": ["exact notable quote 1", "exact notable quote 2"],
  "frameworks_mentioned": ["framework or model mentioned in article"],
  "counterarguments": "any limitations or opposing views mentioned",
  "synthesis": "comprehensive 6-8 sentence synthesis covering the full argument",
  "content_angle": "3-4 sentences: Usman's unique POV opportunity. What can he add from his enterprise CISO experience? Suggest a coined term or framework name.",
  "draft_outline": {{
    "headline": "suggested article headline with coined term",
    "hook": "suggested opening line",
    "sections": ["section 1 title", "section 2 title", "section 3 title"],
    "call_to_action": "suggested closing CTA"
  }},
  "tier": 1,
  "themes": ["theme1", "theme2"],
  "why_timely": "2 sentences on urgency and timeliness"
}}"""

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        result = json.loads(response.content[0].text)
        result["success"] = True
        result["depth"] = depth
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
                return result
            except:
                pass
        return {"success": False, "error": "Failed to parse synthesis"}


def process_url(url: str, depth: str = "quick") -> dict:
    """Full pipeline: fetch → synthesize → return record data"""
    print(f"Fetching: {url}")

    # Route to appropriate fetcher
    if 'youtube.com' in url or 'youtu.be' in url:
        article = fetch_youtube_transcript(url)
    else:
        article = fetch_article(url)

    if not article["success"]:
        print(f"Failed to fetch: {article.get('error', 'Unknown error')}")
        return {"success": False, "error": article.get("error")}

    print(f"Synthesizing ({depth}): {article['title'][:60]}...")
    synthesis = synthesize_article(article, depth=depth)

    if not synthesis["success"]:
        print(f"Failed to synthesize: {synthesis.get('error')}")
        return {"success": False, "error": synthesis.get("error")}

    return {
        "success": True,
        "url": url,
        "source_name": article["source_name"],
        "raw_content": article["content"],
        **synthesis
    }


def process_pasted_text(text: str, url: str, source_name: str,
                        author: str, title: str, depth: str = "quick") -> dict:
    """Process manually pasted article text (for Medium, LinkedIn, paywalled)"""
    article = {
        "success": True,
        "url": url,
        "title": title,
        "author": author,
        "source_name": source_name,
        "content": text[:8000]
    }
    print(f"Synthesizing pasted content ({depth}): {title[:60]}...")
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
    print("=== QUICK SYNTHESIS TEST ===")
    result = process_url(
        'https://cloud.google.com/blog/topics/threat-intelligence/defending-enterprise-ai-vulnerabilities',
        depth="quick"
    )
    if result['success']:
        print(f"Title: {result['title']}")
        print(f"Tier: {result['tier']}")
        print(f"Synthesis: {result['synthesis']}")
        print(f"Angle: {result['content_angle']}")
    else:
        print(f"Failed: {result['error']}")

    print("\n=== DEEP SYNTHESIS TEST ===")
    result2 = process_url(
        'https://cloud.google.com/blog/topics/threat-intelligence/defending-enterprise-ai-vulnerabilities',
        depth="deep"
    )
    if result2['success']:
        print(f"Core Argument: {result2.get('core_argument', '')}")
        print(f"Key Points: {result2.get('key_points', [])}")
        print(f"Draft Headline: {result2.get('draft_outline', {}).get('headline', '')}")
    else:
        print(f"Failed: {result2['error']}")