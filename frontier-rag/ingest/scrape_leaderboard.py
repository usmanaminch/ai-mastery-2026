"""
ingest/scrape_leaderboard.py — Scrape llm-stats.com leaderboard
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests
from sqlalchemy import text
from db.connection import get_engine
from dotenv import load_dotenv
load_dotenv()

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS leaderboard (
    id SERIAL PRIMARY KEY, rank INTEGER, model_name TEXT NOT NULL,
    creator TEXT, llm_score FLOAT, reasoning FLOAT, coding FLOAT,
    agent FLOAT, arena FLOAT, context_win TEXT, speed TEXT,
    price_input FLOAT, license TEXT, scraped_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS leaderboard_rank_idx ON leaderboard (rank);
"""

KNOWN_CREATORS = [
    "Moonshot AI","Alibaba Cloud / Qwen","Alibaba Cloud /","Alibaba Cloud",
    "Google DeepMind","Mistral AI","InceptionLabs","Together AI",
    "OpenAI","Anthropic","DeepSeek","Microsoft","Google","Qwen","Meta",
    "Amazon","ByteDance","MiniMax","Perplexity","Cohere","NVIDIA","Apple","xAI","01.AI","Yi",
]

def split_model_creator(raw):
    name = raw.strip().rstrip("/").strip()
    for creator in KNOWN_CREATORS:
        if name.endswith(creator):
            return name[:-len(creator)].strip(), creator
    return name, ""

def parse_float(val):
    if not val or str(val).strip() in ("—","-","","N/A","None"):
        return None
    v = str(val).strip().replace("$","").replace(",","").replace("c/s","").replace("M tok","").replace("K tok","").replace("/M","")
    try:
        return float(v)
    except ValueError:
        return None

def ensure_schema():
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text(SCHEMA_SQL))
        conn.commit()

def scrape_leaderboard():
    print("Fetching llm-stats.com...")
    try:
        resp = requests.get("https://llm-stats.com", headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print(f"  Failed: {e}")
        return []

    table_match = re.search(r"\| Rank \|.*?\n((?:\|.*\n?)+)", resp.text, re.DOTALL)
    if not table_match:
        print("  No table found")
        return []

    models = []
    for row in table_match.group(1).strip().split("\n"):
        if not row.strip() or "---" in row:
            continue
        cols = [c.strip() for c in row.split("|") if c.strip()]
        if len(cols) < 6:
            continue
        try:
            rank_raw = re.sub(r"[^0-9]", "", cols[0])
            if not rank_raw:
                continue
            rank = int(rank_raw)
            cell = cols[1]
            cell = re.sub(r"!\[[^\]]*\]\([^\)]*\)", "", cell)
            cell = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", cell)
            cell = re.sub(r"\b(NEW|UNRELEASED|Preview)\b", "", cell).strip()
            model_name, creator = split_model_creator(cell)
            models.append({
                "rank": rank,
                "model_name": model_name[:120],
                "creator": creator[:80],
                "llm_score":   parse_float(cols[2]) if len(cols) > 2 else None,
                "reasoning":   parse_float(cols[3]) if len(cols) > 3 else None,
                "coding":      parse_float(cols[4]) if len(cols) > 4 else None,
                "agent":       parse_float(cols[5]) if len(cols) > 5 else None,
                "arena":       parse_float(cols[6]) if len(cols) > 6 else None,
                "context_win": cols[7].strip() if len(cols) > 7 else None,
                "speed":       cols[8].strip() if len(cols) > 8 else None,
                "price_input": parse_float(cols[9]) if len(cols) > 9 else None,
                "license":     cols[10].strip() if len(cols) > 10 else None,
            })
        except Exception:
            continue
    print(f"  Parsed {len(models)} models")
    return models

def store_leaderboard(models):
    if not models:
        return
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM leaderboard"))
        for m in models:
            conn.execute(text("""
                INSERT INTO leaderboard (rank,model_name,creator,llm_score,reasoning,
                coding,agent,arena,context_win,speed,price_input,license)
                VALUES (:rank,:model_name,:creator,:llm_score,:reasoning,
                :coding,:agent,:arena,:context_win,:speed,:price_input,:license)
            """), m)
        conn.commit()
    print(f"Stored {len(models)} models")

def run():
    ensure_schema()
    models = scrape_leaderboard()
    if models:
        store_leaderboard(models)
        print("\nTop 5:")
        for m in models[:5]:
            price = f"${m['price_input']:.2f}" if m.get("price_input") else "—"
            print(f"  #{m['rank']:>2}  {m['model_name']:<30} {m['creator']:<15}  {m.get('llm_score')}  {price}/M")
    return models

if __name__ == "__main__":
    run()
