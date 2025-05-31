import os
import datetime
import pytz
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the existing tokens/token.pickle
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

TOKEN_PATH = 'tokens/token.pickle'
CREDENTIALS_PATH = 'client_secret.json'
TIMEZONE = 'America/Chicago'

def get_authenticated_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SCOPES
            )
            creds = flow.run_local_server(port=8080, prompt='consent')
        os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
        with open(TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)
    return build('youtube', 'v3', credentials=creds)

def get_next_sunday_10am():
    tz = pytz.timezone(TIMEZONE)
    now = datetime.datetime.now(tz)
    days_until_sunday = (6 - now.weekday()) % 7
    if days_until_sunday == 0 and now.hour >= 10:
        days_until_sunday = 7
    next_sunday = now + datetime.timedelta(days=days_until_sunday)
    next_sunday_10am = tz.localize(datetime.datetime.combine(next_sunday.date(), datetime.time(10, 0)))
    return next_sunday_10am.isoformat()

def create_stream():
    youtube = get_authenticated_service()
    
    start_time = get_next_sunday_10am()
    end_time = (datetime.datetime.fromisoformat(start_time) + datetime.timedelta(hours=1)).isoformat()

    # Create liveBroadcast
    broadcast_body = {
        "snippet": {
            "title": "Sunday 10AM Worship",
            "scheduledStartTime": start_time,
            "scheduledEndTime": end_time
        },
        "status": {
            "privacyStatus": "public"
        }
    }

    broadcast_response = youtube.liveBroadcasts().insert(
        part="snippet,status",
        body=broadcast_body
    ).execute()

    # Create liveStream
    stream_body = {
        "snippet": {
            "title": "Sunday 10AM Stream"
        },
        "cdn": {
            "frameRate": "30fps",
            "ingestionType": "rtmp",
            "resolution": "720p"
        }
    }

    stream_response = youtube.liveStreams().insert(
        part="snippet,cdn",
        body=stream_body
    ).execute()

    # Bind the broadcast to the stream
    youtube.liveBroadcasts().bind(
        part="id,contentDetails",
        id=broadcast_response['id'],
        streamId=stream_response['id']
    ).execute()

    print(f"✅ Stream created successfully: https://www.youtube.com/watch?v={broadcast_response['id']}")

if __name__ == "__main__":
    create_stream()

