from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os

# All three scopes — Gmail + Calendar + Sheets
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/spreadsheets'
]

creds = None

# Delete old token to force re-auth
token_path = '../chief-of-staff/token.pickle'
if os.path.exists(token_path):
    os.remove(token_path)
    print("Old token removed")

# Run OAuth flow
flow = InstalledAppFlow.from_client_secrets_file(
    '../chief-of-staff/credentials.json',
    SCOPES
)
creds = flow.run_local_server(port=0)

# Save new token
with open(token_path, 'wb') as f:
    pickle.dump(creds, f)

print("New token saved with scopes:")
for scope in creds.scopes:
    print(f"  - {scope}")
