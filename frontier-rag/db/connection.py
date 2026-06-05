"""
db/connection.py — Cloud SQL connection

Handles two auth modes automatically:
- Local dev: Application Default Credentials (gcloud auth application-default login)
- Streamlit Cloud: Service account JSON stored in st.secrets or GOOGLE_SERVICE_ACCOUNT_JSON env var

No code changes needed between environments — it detects which to use.
"""
import os
import json
import sqlalchemy
from google.cloud.sql.connector import Connector
from dotenv import load_dotenv

load_dotenv()

INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME", "frontier-rag:us-east4:frontier-rag-db")
DB_USER = os.getenv("DB_USER", "raguser")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME", "frontier_rag")
GCP_PROJECT  = os.getenv("GCP_PROJECT", "frontier-rag")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-east4")

_connector = None
_credentials = None


def _get_credentials():
    """
    Return GCP credentials.
    Priority: Streamlit secrets → env var → ADC (local gcloud login).
    """
    global _credentials
    if _credentials is not None:
        return _credentials

    sa_json = None

    # Try Streamlit secrets first (cloud deployment)
    try:
        import streamlit as st
        sa_json = st.secrets.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    except Exception:
        pass

    # Fall back to env var
    if not sa_json:
        sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")

    if sa_json:
        try:
            from google.oauth2 import service_account
            sa_info = json.loads(sa_json) if isinstance(sa_json, str) else sa_json
            _credentials = service_account.Credentials.from_service_account_info(
                sa_info,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
            return _credentials
        except Exception as e:
            print(f"[connection] Service account load failed: {e} — falling back to ADC")

    # ADC (local development)
    return None


def get_connector() -> Connector:
    global _connector
    if _connector is None:
        creds = _get_credentials()
        _connector = Connector(credentials=creds) if creds else Connector()
    return _connector


def get_connection():
    return get_connector().connect(
        INSTANCE_CONNECTION_NAME,
        "pg8000",
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME,
    )


def get_engine():
    return sqlalchemy.create_engine(
        "postgresql+pg8000://",
        creator=get_connection,
    )


def close_connector():
    global _connector
    if _connector:
        _connector.close()
        _connector = None
