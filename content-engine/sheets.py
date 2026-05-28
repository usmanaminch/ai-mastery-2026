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

# Any of these in column G means "stop showing in ready-to-process queue"
TERMINAL_STATUSES = {
    'done', 'yes',                    # historical / successfully synthesized
    'skipped',                        # platforms we can't auto-scrape
    'pending paste',                  # failed scrape, in manual queue
    'duplicate',                      # URL already in library
    'dismissed',                      # user manually skipped
    'error',                          # manual error mark
}

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
    Return URLs where column G is blank or not a terminal status.
    Column A = URL
    Column F = Usman Viewed
    Column G = Content Engine Synthesis
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
            if synthesis_status not in TERMINAL_STATUSES:
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
                "synthesized": synthesis_status in ['done', 'yes'],
                "status": synthesis_status,  # full status string for richer UI
            })

        return all_links

    except Exception as e:
        print(f"Sheets error: {e}")
        return []

def mark_row_status(row_number: int, status: str) -> bool:
    """Generic function — writes any status string to column G of given row"""
    try:
        creds = get_creds()
        service = build('sheets', 'v4', credentials=creds)
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!G{row_number}",
            valueInputOption="RAW",
            body={"values": [[status]]}
        ).execute()
        return True
    except Exception as e:
        print(f"Error marking row {row_number} as '{status}': {e}")
        return False

# ── Convenience wrappers ──────────────────────────────────────────
def mark_as_synthesized(row_number: int) -> bool:
    """Write 'Done' to column G after successful synthesis"""
    return mark_row_status(row_number, "Done")

def mark_as_skipped(row_number: int) -> bool:
    """Write 'Skipped' for platforms that can't be auto-scraped (IG, TikTok, etc.)"""
    return mark_row_status(row_number, "Skipped")

def mark_as_pending_paste(row_number: int) -> bool:
    """Write 'Pending Paste' when URL is queued for manual paste"""
    return mark_row_status(row_number, "Pending Paste")

def mark_as_duplicate(row_number: int) -> bool:
    """Write 'Duplicate' when URL is already in library"""
    return mark_row_status(row_number, "Duplicate")

def mark_as_dismissed(row_number: int) -> bool:
    """Write 'Dismissed' when user manually skipped the URL via Skip button"""
    return mark_row_status(row_number, "Dismissed")

if __name__ == "__main__":
    print("=== Sheets Connection Test ===\n")
    all_links = get_all_links()
    synthesized = [l for l in all_links if l['synthesized']]
    unprocessed = get_unprocessed_links()

    # Status breakdown
    from collections import Counter
    status_counts = Counter(l['status'] or 'empty' for l in all_links)

    print(f"Total links: {len(all_links)}")
    print(f"Synthesized (Done/Yes): {len(synthesized)}")
    print(f"Ready to process: {len(unprocessed)}")
    print(f"\nStatus breakdown:")
    for status, count in sorted(status_counts.items(), key=lambda x: -x[1]):
        print(f"  {status:20s} {count}")
    print(f"\nReady-to-process samples:")
    for item in unprocessed[:5]:
        viewed = "👁" if item['usman_viewed'] in ['yes','y'] else "○"
        print(f"  {viewed} Row {item['row']}: {item['url'][:65]}")
