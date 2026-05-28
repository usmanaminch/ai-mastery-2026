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

# ── Reusable prompt blocks ───────────────────────────────────────────
TIER_CRITERIA = """
TIER CLASSIFICATION — evaluate THIS ARTICLE carefully before answering:

Tier 3 (DEFAULT — most articles, ~60%):
  Quick LinkedIn reaction (150-300 words).
  The article is interesting and worth sharing, but a single source.
  Best as: a few lines of commentary, top 3 takeaways, link to original.
  Use for: news items, podcast episodes, single-point blog posts,
  LinkedIn posts from others, quick reads, opinion pieces.
  When in doubt, this is the right tier.

Tier 2 (~35% of articles):
  Standalone blog post (300-800 words).
  The article has enough depth, original insight, or unique data to justify
  its own dedicated write-up — the source alone can support a full post.
  Usman can add a clear CISO perspective that changes the reader's view.
  Use for: detailed technical breakdowns, articles with original research or
  real stats, frameworks with genuine application to enterprise security.

Tier 1 (RARE — ~5%, only for landmark single sources):
  Full long-form article (800-1200 words) for usmanc.com.
  A single article qualifies ONLY if it is a landmark primary source — a major
  original report, industry study, or primary document with enough data,
  frameworks, and depth to anchor a comprehensive piece entirely on its own.
  Think: Verizon DBIR, Google Threat Horizons, a major government regulation.

  IMPORTANT: Most Tier 1 content is NOT produced from individual articles.
  It comes from cross-article synthesis — multiple T2/T3 articles on the same
  theme synthesized together into one definitive piece. Do NOT force Tier 1
  on a single article that would work better as part of a cluster.

DEFAULT RULE: Classify T3 unless the article clearly has standalone substance
for a full blog post (T2) or is a landmark primary source document (T1, rare).
"""

ALLOWED_THEMES = """
THEMES — use ONLY values from this list, never invent new ones:
agentic SOC, AI security, AI governance, post-quantum, cloud security,
zero trust, SecOps, threat intelligence, AI risk, enterprise AI,
vibe coding, data strategy
"""


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

    Tier model:
    - T3 (default): single article → quick LinkedIn reaction
    - T2: single article with depth → standalone blog post
    - T1 (rare): landmark primary source only, OR a theme cluster synthesized separately
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

{TIER_CRITERIA}

{ALLOWED_THEMES}

Evaluate this specific article against the tier criteria above, then respond
ONLY with valid JSON in the structure below. Replace every <placeholder> with
real content based on YOUR evaluation — do not copy placeholders literally.

{{
  "title": "<clean article title>",
  "author": "<author name or Unknown>",
  "tldr": "<ONE sentence — the single most important point>",
  "key_points": [
    "<Point 1 — specific claim, stat, or argument from the article>",
    "<Point 2 — specific claim, stat, or argument from the article>",
    "<Point 3 — specific claim, stat, or argument from the article>",
    "<Point 4 — specific claim, stat, or argument from the article>"
  ],
  "why_timely": "<One sentence on why this matters right now for CISOs>",
  "key_quotes": ["<most notable quote if any>"],
  "suggested_piece": {{
    "what_to_write": "<specific article or post concept — not vague>",
    "why_now": "<what makes this urgent or timely today>",
    "audience": "<who specifically — e.g. Fortune 500 CISOs, security boards, SOC leaders>",
    "value_to_audience": "<what they get from reading — specific benefit>",
    "usman_angle": "<what Usman adds from his Google Cloud CISO experience>",
    "coined_term": "<a memorable term Usman could coin for the core concept>",
    "recommended_tier": <EVALUATE — integer 1, 2, or 3. Default to 3. Only upgrade to 2 if this single article supports a full standalone blog post. Only 1 if it is a landmark primary source document.>
  }},
  "tier": <SAME integer as recommended_tier above>,
  "themes": ["<select 1-3 from ALLOWED_THEMES list only>"]
}}

CRITICAL OUTPUT RULES:
- Default tier is 3. Justify any upgrade to 2 or 1 against the criteria.
- themes MUST only contain strings from the ALLOWED_THEMES list — do not invent new themes
- Output valid JSON only, no markdown fences, no commentary"""

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

{TIER_CRITERIA}

{ALLOWED_THEMES}

Evaluate this specific article against the tier criteria above, then respond
ONLY with valid JSON in the structure below. Replace every <placeholder> with
real content based on YOUR evaluation — do not copy placeholders literally.

{{
  "title": "<clean article title>",
  "author": "<author name or Unknown>",
  "tldr": "<ONE sentence — the single most important point>",
  "core_argument": "<2-3 sentences: the central thesis>",
  "key_points": [
    "<Point 1 with specific detail, stat, or claim and its source>",
    "<Point 2 with specific detail, stat, or claim and its source>",
    "<Point 3 with specific detail, stat, or claim and its source>",
    "<Point 4 with specific detail, stat, or claim and its source>",
    "<Point 5 with specific detail, stat, or claim and its source>"
  ],
  "key_stats": ["<stat with attribution>", "<stat with attribution>"],
  "key_quotes": ["<exact notable quote 1>", "<exact notable quote 2>"],
  "frameworks_mentioned": ["<framework or model name>"],
  "counterarguments": "<limitations or opposing views mentioned>",
  "why_timely": "<2 sentences on urgency for CISOs>",
  "suggested_piece": {{
    "what_to_write": "<specific article concept with working title>",
    "why_now": "<what makes this urgent or timely today>",
    "audience": "<who specifically — e.g. Fortune 500 CISOs, security boards, SOC leaders>",
    "value_to_audience": "<what they get from reading — specific benefit>",
    "usman_angle": "<what Usman adds from Google Cloud CISO experience>",
    "coined_term": "<a memorable term Usman could coin for the core concept>",
    "recommended_tier": <EVALUATE — integer 1, 2, or 3. Default to 3. Only upgrade to 2 if this single article supports a full standalone blog post. Only 1 if it is a landmark primary source document.>
  }},
  "draft_outline": {{
    "headline": "<suggested article headline using the coined term>",
    "hook": "<suggested opening line that creates urgency>",
    "sections": ["<section 1 title>", "<section 2 title>", "<section 3 title>"],
    "call_to_action": "<suggested closing CTA>"
  }},
  "tier": <SAME integer as recommended_tier above>,
  "themes": ["<select 1-3 from ALLOWED_THEMES list only>"]
}}

CRITICAL OUTPUT RULES:
- Default tier is 3. Justify any upgrade to 2 or 1 against the criteria.
- themes MUST only contain strings from the ALLOWED_THEMES list — do not invent new themes
- Output valid JSON only, no markdown fences, no commentary"""

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
        return {"success": synthesis.get("error")}
    return {
        "success": True,
        "url": url,
        "source_name": source_name,
        "raw_content": text[:2000],
        **synthesis
    }


if __name__ == "__main__":
    # Test — podcast episode should come back T3, not T1
    test_url = 'https://cloud.withgoogle.com/cloudsecurity/podcast/ep264-measuring-your-agentic-soc-two-security-leaders-walk-into-a-podcast/'

    print("=== QUICK SYNTHESIS (Haiku) ===")
    result = process_url(test_url, depth="quick")
    if result['success']:
        print(f"Title: {result.get('title')}")
        print(f"TLDR: {result.get('tldr')}")
        sp = result.get('suggested_piece', {})
        print(f"Recommended tier: {sp.get('recommended_tier')}  ← should be 3 for a podcast episode")
        print(f"Top-level tier:   {result.get('tier')}")
        print(f"Themes: {result.get('themes')}")
    else:
        print(f"Failed: {result['error']}")
