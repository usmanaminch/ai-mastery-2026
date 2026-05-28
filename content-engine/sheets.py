import pickle
import json
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import warnings
warnings.filterwarnings('ignore')

SPREADSHEET_ID = "1obT1Fu4kEOvgSvd1el2ErTw_F3YKGtGvhzwp-7t6tOU"
SHEET_NAME = "Sheet1"
TOKEN_PATH = "../chief-of-staff/token.pickle"

def get_creds():
    """
    Load credentials — works both locally and on Streamlit Cloud.
    Local: reads token.pickle
    Cloud: reads GOOGLE_TOKEN from Streamlit secrets
    """
    try:
        # Try Streamlit secrets first (cloud deployment)
        import streamlit as st
        token_data = json.loads(st.secrets["GOOGLE_TOKEN"])
        creds = Credentials(
            token=token_data.get('token'),
            refresh_token=token_data.get('refresh_token'),
            token_uri=token_data.get('token_uri'),
            client_id=token_data.get('client_id'),
            client_secret=token_data.get('client_secret'),
            scopes=token_data.get('scopes')
        )
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        return creds
    except Exception:
        # Fall back to local token.pickle
        with open(TOKEN_PATH, 'rb') as f:
            creds = pickle.load(f)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        return creds

def get_unprocessed_links() -> list:
    """
    Return URLs where column G (Content Engine Synthesis) is blank.
    Column A = URL
    Column F = Usman Viewed
    Column G = Content Engine Synthesis (blank = not processed, Done = synthesized)
    """
    try:
        creds = get_creds()
        service = build('sheets', 'v4', credentials=creds)

        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A:G"
        ).execute()

        rows = result.get('values', [])
        unprocessed = []

        for i, row in enumerate(rows):
            if not row:
                continue
            url = row[0].strip() if len(row) > 0 else ""
            if not url.startswith('http'):
                continue
            synthesis_status = row[6].strip().lower() if len(row) > 6 else ""
            if synthesis_status not in ['done', 'yes']:
                unprocessed.append({
                    "url": url,
                    "row": i + 1,
                    "usman_viewed": row[5].strip().lower() if len(row) > 5 else "",
                    "synthesis_status": synthesis_status
                })

        return unprocessed

    except Exception as e:
        print(f"Sheets error: {e}")
        return []

def get_all_links() -> list:
    """Get all links with status for overview"""
    try:
        creds = get_creds()
        service = build('sheets', 'v4', credentials=creds)

        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A:G"
        ).execute()

        rows = result.get('values', [])
        all_links = []

        for i, row in enumerate(rows):
            if not row:
                continue
            url = row[0].strip() if len(row) > 0 else ""
            if not url.startswith('http'):
                continue
            synthesis_status = row[6].strip().lower() if len(row) > 6 else ""
            usman_viewed = row[5].strip().lower() if len(row) > 5 else ""
            all_links.append({
                "url": url,
                "row": i + 1,
                "usman_viewed": usman_viewed in ['yes', 'y'],
                "synthesized": synthesis_status in ['done', 'yes']
            })

        return all_links

    except Exception as e:
        print(f"Sheets error: {e}")
        return []

def mark_as_synthesized(row_number: int):
    """Write 'Done' to column G after successful synthesis"""
    try:
        creds = get_creds()
        service = build('sheets', 'v4', credentials=creds)
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!G{row_number}",
            valueInputOption="RAW",
            body={"values": [["Done"]]}
        ).execute()
        return True
    except Exception as e:
        print(f"Error marking row: {e}")
        return False

if __name__ == "__main__":
    print("=== Sheets Connection Test ===\n")
    all_links = get_all_links()
    synthesized = [l for l in all_links if l['synthesized']]
    unprocessed = get_unprocessed_links()
    print(f"Total links: {len(all_links)}")
    print(f"Synthesized (col G): {len(synthesized)}")
    print(f"Ready to process: {len(unprocessed)}")
    for item in unprocessed[:5]:
        viewed = "👁" if item['usman_viewed'] in ['yes','y'] else "○"
        print(f"  {viewed} Row {item['row']}: {item['url'][:65]}")
