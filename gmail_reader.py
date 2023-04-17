import os
import base64
import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']


# Authenticate with Gmail API
def authenticate_gmail():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


# Mark all unread emails as read with limit of 20
def mark_emails_as_read():
    creds = authenticate_gmail()
    service = create_gmail_service()

    # Get all unread emails
    results = service.users().messages().list(
        userId='me', q='is:unread').execute()
    messages = results.get('messages', [])

    if not messages:
        print('No unread messages found.')
        return

    # Mark all unread emails as read
    for message in messages:
        service.users().messages().modify(
            userId='me',
            id=message['id'],
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        print(f'Marked email with ID {message["id"]} as read.')

# Mark all unread emails as read
def mark_all_emails_as_read():
    while (get_unread_emails_count() > 0):
        mark_emails_as_read()

# Create Gmail service
def create_gmail_service():
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)
    return service

# Get the total number of unread emails
def get_unread_emails_count():
    creds = authenticate_gmail()
    service = create_gmail_service()

    # Get total number of unread emails
    results = service.users().labels().get(userId='me', id='INBOX').execute()
    unread_count = results['messagesUnread']
    return unread_count

# Archive all emails older than 3 months
def archive_old_messages():
    # Set up the Gmail API client
    creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/gmail.modify'])
    service = build('gmail', 'v1', credentials=creds)

    # Get the timestamp for 3 months ago
    now = datetime.datetime.utcnow()
    three_months_ago = now - datetime.timedelta(days=90)
    timestamp = int(three_months_ago.timestamp())

    # Get the IDs of all messages in the inbox older than 3 months
    query = f'category:primary before:{timestamp} label:inbox'
    response = service.users().messages().list(userId='me', q=query).execute()
    message_ids = [msg['id'] for msg in response.get('messages', [])]

    # Archive the old messages
    if message_ids:
        batch = service.new_batch_http_request()
        for message_id in message_ids:
            batch.add(service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['INBOX']}
            ))
        batch.execute()
