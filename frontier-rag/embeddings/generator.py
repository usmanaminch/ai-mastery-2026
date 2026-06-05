"""
embeddings/generator.py — Vertex AI text-embedding-004
Reads credentials from st.secrets (cloud) or ADC (local).
"""
import os, json, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv()

def _cfg(key, default=None):
    try:
        import streamlit as st
        v = st.secrets.get(key)
        if v is not None:
            return v
    except Exception:
        pass
    return os.getenv(key, default)

GCP_PROJECT  = _cfg("GCP_PROJECT",  "frontier-rag")
GCP_LOCATION = _cfg("GCP_LOCATION", "us-east4")
EMBEDDING_MODEL = "text-embedding-004"
EMBEDDING_DIMS  = 768

_client = None

def _get_credentials():
    sa_json = _cfg("GOOGLE_SERVICE_ACCOUNT_JSON")
    if sa_json:
        try:
            from google.oauth2 import service_account
            info = json.loads(sa_json) if isinstance(sa_json, str) else sa_json
            return service_account.Credentials.from_service_account_info(
                info, scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
        except Exception as e:
            print(f"[generator] SA creds failed: {e}")
    return None

def get_client():
    global _client
    if _client is None:
        creds = _get_credentials()
        kwargs = dict(vertexai=True, project=GCP_PROJECT, location=GCP_LOCATION)
        if creds:
            kwargs["credentials"] = creds
        _client = genai.Client(**kwargs)
    return _client

def embed_texts(texts: list, task_type: str = "RETRIEVAL_DOCUMENT", batch_size: int = 20) -> list:
    client = get_client()
    all_vectors = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        result = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=batch,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=EMBEDDING_DIMS,
            ),
        )
        all_vectors.extend([e.values for e in result.embeddings])
    return all_vectors

def embed_query(query: str) -> list:
    return embed_texts([query], task_type="RETRIEVAL_QUERY")[0]

def embed_document(text: str) -> list:
    return embed_texts([text], task_type="RETRIEVAL_DOCUMENT")[0]
