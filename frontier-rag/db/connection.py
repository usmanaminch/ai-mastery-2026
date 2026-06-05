"""
db/connection.py — Cloud SQL connection

Reads config from st.secrets (Streamlit Cloud) with fallback to os.getenv (local dev).
Streamlit Cloud does NOT expose secrets as os.environ — must use st.secrets directly.
"""
import os, json, sqlalchemy
from google.cloud.sql.connector import Connector
from dotenv import load_dotenv
load_dotenv()

def _cfg(key, default=None):
    """Read from st.secrets first, then .env / os.environ."""
    try:
        import streamlit as st
        v = st.secrets.get(key)
        if v is not None:
            return v
    except Exception:
        pass
    return os.getenv(key, default)

INSTANCE_CONNECTION_NAME = _cfg("INSTANCE_CONNECTION_NAME", "frontier-rag:us-east4:frontier-rag-db")
DB_USER = _cfg("DB_USER", "raguser")
DB_PASS = _cfg("DB_PASS")
DB_NAME = _cfg("DB_NAME", "frontier_rag")

_connector   = None
_credentials = None

def _get_credentials():
    global _credentials
    if _credentials is not None:
        return _credentials
    sa_json = _cfg("GOOGLE_SERVICE_ACCOUNT_JSON")
    if sa_json:
        try:
            from google.oauth2 import service_account
            info = json.loads(sa_json) if isinstance(sa_json, str) else sa_json
            _credentials = service_account.Credentials.from_service_account_info(
                info, scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            return _credentials
        except Exception as e:
            print(f"[connection] SA creds failed: {e} — using ADC")
    return None

def get_connector():
    global _connector
    if _connector is None:
        creds = _get_credentials()
        _connector = Connector(credentials=creds) if creds else Connector()
    return _connector

def get_connection():
    return get_connector().connect(
        INSTANCE_CONNECTION_NAME, "pg8000",
        user=DB_USER, password=DB_PASS, db=DB_NAME,
    )

def get_engine():
    return sqlalchemy.create_engine("postgresql+pg8000://", creator=get_connection)

def close_connector():
    global _connector
    if _connector:
        _connector.close()
        _connector = None
