"""
Cloud SQL connection using the Python Connector.

Why the Connector vs raw psycopg2?
- Handles IAM authentication automatically using gcloud credentials
- Manages SSL certificates without manual configuration
- Reconnects on failure automatically
- No need to whitelist your IP address in Cloud SQL
"""
import os
from google.cloud.sql.connector import Connector
import sqlalchemy
from dotenv import load_dotenv

load_dotenv()

INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME", "frontier-rag:us-east4:frontier-rag-db")
DB_USER = os.getenv("DB_USER", "raguser")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME", "frontier_rag")

_connector = None

def get_connector():
    global _connector
    if _connector is None:
        _connector = Connector()
    return _connector

def get_connection():
    """Return a pg8000 connection via the Cloud SQL Connector."""
    return get_connector().connect(
        INSTANCE_CONNECTION_NAME,
        "pg8000",
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME,
    )

def get_engine():
    """Return a SQLAlchemy engine connected to Cloud SQL."""
    return sqlalchemy.create_engine(
        "postgresql+pg8000://",
        creator=get_connection,
    )

def close_connector():
    global _connector
    if _connector:
        _connector.close()
        _connector = None
