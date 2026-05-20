import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import base64

# Permissions we need
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar.readonly'
]

def get_google_credentials():
    """Login to Google and save credentials"""
    creds = None
    
    # Load saved credentials if they exist
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next time
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def get_recent_emails(max_results=10):
    """Get recent unread emails"""
    creds = get_google_credentials()
    service = build('gmail', 'v1', credentials=creds)
    
    # Get unread emails
    results = service.users().messages().list(
        userId='me',
        labelIds=['INBOX', 'UNREAD'],
        maxResults=max_results
    ).execute()
    
    messages = results.get('messages', [])
    emails = []
    
    for msg in messages:
        # Get email details
        message = service.users().messages().get(
            userId='me',
            id=msg['id'],
            format='metadata',
            metadataHeaders=['From', 'Subject', 'Date']
        ).execute()
        
        headers = message['payload']['headers']
        email_data = {}
        
        for header in headers:
            if header['name'] == 'From':
                email_data['from'] = header['value']
            elif header['name'] == 'Subject':
                email_data['subject'] = header['value']
            elif header['name'] == 'Date':
                email_data['date'] = header['value']
        
        # Get snippet
        email_data['snippet'] = message.get('snippet', '')
        emails.append(email_data)
    
    return emails

def get_todays_calendar():
    """Get today's calendar events"""
    creds = get_google_credentials()
    service = build('calendar', 'v3', credentials=creds)
    
    # Today's time range
    now = datetime.utcnow()
    start_of_day = now.replace(hour=0, minute=0, second=0).isoformat() + 'Z'
    end_of_day = now.replace(hour=23, minute=59, second=59).isoformat() + 'Z'
    
    events_result = service.events().list(
        calendarId='primary',
        timeMin=start_of_day,
        timeMax=end_of_day,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])
    calendar_data = []
    
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        calendar_data.append({
            'title': event.get('summary', 'No title'),
            'start': start,
            'description': event.get('description', '')[:100]
        })
    
    return calendar_data

def format_context_for_agent(emails, events):
    """Format Gmail + Calendar data for the CoS agent"""
    context = "=== YOUR WORLD RIGHT NOW ===\n\n"
    
    context += "📧 UNREAD EMAILS:\n"
    if emails:
        for e in emails:
            context += f"• From: {e.get('from', 'Unknown')}\n"
            context += f"  Subject: {e.get('subject', 'No subject')}\n"
            context += f"  Preview: {e.get('snippet', '')[:100]}\n\n"
    else:
        context += "No unread emails.\n\n"
    
    context += "📅 TODAY'S CALENDAR:\n"
    if events:
        for e in events:
            context += f"• {e['start']}: {e['title']}\n"
    else:
        context += "No events today.\n\n"
    
    return context

if __name__ == "__main__":
    print("Connecting to Gmail and Calendar...")
    emails = get_recent_emails(10)
    events = get_todays_calendar()
    print(format_context_for_agent(emails, events))