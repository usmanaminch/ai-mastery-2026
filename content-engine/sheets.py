import pickle
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import warnings
warnings.filterwarnings('ignore')

SPREADSHEET_ID = "1obT1Fu4kEOvgSvd1el2ErTw_F3YKGtGvhzwp-7t6tOU"
SHEET_NAME = "Sheet1"
TOKEN_PATH = "../chief-of-staff/token.pickle"

def get_creds():
    """Load and refresh Google credentials"""
    with open(TOKEN_PATH, 'rb') as f:
        creds = pickle.load(f)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds

def get_unprocessed_links() -> list:
    """
    Read the Google Sheet and return URLs where column G is blank.
    Column A = URL
    Column F = Usman Viewed (ignored for processing decisions)
    Column G = Content Engine Synthesis — blank = not yet processed, Done = synthesized
    """
    try:
        creds = get_creds()
        service = build('sheets', 'v4', credentials=creds)

        # Read columns A through G
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A:G"
        ).execute()

        rows = result.get('values', [])
        unprocessed = []

        for i, row in enumerate(rows):
            if not row:
                continue

            # Column A = URL
            url = row[0].strip() if len(row) > 0 else ""

            # Skip if not a valid URL
            if not url.startswith('http'):
                continue

            # Column G = Content Engine Synthesis status (index 6)
            synthesis_status = row[6].strip().lower() if len(row) > 6 else ""

            # Only process if column G is blank
            if synthesis_status not in ['done', 'yes']:
                unprocessed.append({
                    "url": url,
                    "row": i + 1,  # 1-indexed for Sheets API
                    "usman_viewed": row[5].strip().lower() if len(row) > 5 else "",
                    "synthesis_status": synthesis_status
                })

        return unprocessed

    except Exception as e:
        print(f"Sheets error: {e}")
        return []

def get_all_links() -> list:
    """Get all links with their status — for overview and consolidation"""
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
    """
    Mark a row as synthesized by writing 'Done' to column G.
    Called automatically after successful synthesis.
    """
    try:
        creds = get_creds()
        service = build('sheets', 'v4', credentials=creds)

        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!G{row_number}",
            valueInputOption="RAW",
            body={"values": [["Done"]]}
        ).execute()

        print(f"Marked row {row_number} as Done in column G")
        return True

    except Exception as e:
        print(f"Error marking row: {e}")
        return False

if __name__ == "__main__":
    print("=== Sheets Connection Test ===\n")

    all_links = get_all_links()
    synthesized = [l for l in all_links if l['synthesized']]
    viewed = [l for l in all_links if l['usman_viewed']]
    unprocessed = get_unprocessed_links()

    print(f"Total links in sheet: {len(all_links)}")
    print(f"Usman viewed (col F): {len(viewed)}")
    print(f"Content Engine synthesized (col G): {len(synthesized)}")
    print(f"Ready to synthesize (col G blank): {len(unprocessed)}")
    print(f"\nFirst 5 unprocessed:")
    for item in unprocessed[:5]:
        viewed_label = "👁 viewed" if item['usman_viewed'] in ['yes','y'] else "unseen"
        print(f"  Row {item['row']} [{viewed_label}]: {item['url'][:65]}")
