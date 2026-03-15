"""
Vale Park Church of Christ — YouTube Live Stream Scheduler

Runs nightly via Windows Task Scheduler. Looks at the next 7 days and
creates any missing YouTube live broadcast events for Sunday and Wednesday
services. Broadcasts that already exist are left untouched.

On first run a browser window will open for OAuth authorization.
Select the Vale Park Church of Christ Brand Page channel when prompted.
Credentials are saved to credentials.pkl and refreshed automatically
on subsequent runs.
"""

import datetime
import glob
import logging
import os
import pickle

import pytz
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ── Configuration ──────────────────────────────────────────────────────────────

TIMEZONE         = pytz.timezone('America/Chicago')
CREDENTIALS_FILE = 'credentials.pkl'
SCOPES           = ['https://www.googleapis.com/auth/youtube']
LOGS_DIR         = 'logs'
LOGS_TO_KEEP     = 10


def find_client_secrets():
    """Locates the OAuth client secrets file.

    Accepts either the standard deployed name (client_secrets.json) or
    Google's default download name (client_secret_*.apps.googleusercontent.com.json).
    """
    if os.path.exists('client_secrets.json'):
        return 'client_secrets.json'
    matches = glob.glob('client_secret_*.apps.googleusercontent.com.json')
    if matches:
        return matches[0]
    raise FileNotFoundError(
        'No client secrets file found. Expected client_secrets.json or '
        'client_secret_*.apps.googleusercontent.com.json'
    )


STREAM_CDN = {
    'frameRate':     '30fps',
    'ingestionType': 'rtmp',
    'resolution':    '1080p',
}

# weekday() values: 0=Monday, 1=Tuesday, 2=Wednesday, ..., 6=Sunday
EVENTS = [
    {'title': 'Sunday Morning Adult Bible Class',    'weekday': 6, 'hour': 9,  'minute': 0},
    {'title': 'Sunday Morning Worship Service',      'weekday': 6, 'hour': 10, 'minute': 0},
    {'title': 'Sunday Evening Worship Service',      'weekday': 6, 'hour': 17, 'minute': 0},
    {'title': 'Wednesday Evening Adult Bible Class', 'weekday': 2, 'hour': 18, 'minute': 0},
]

# ── Logging ────────────────────────────────────────────────────────────────────

def setup_logging():
    os.makedirs(LOGS_DIR, exist_ok=True)

    timestamp = datetime.datetime.now(TIMEZONE).strftime('%Y-%m-%d_%H%M%S')
    log_file  = os.path.join(LOGS_DIR, f'{timestamp}.log')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s  %(levelname)-8s  %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(),
        ],
    )

    prune_logs()
    return log_file


def prune_logs():
    logs = sorted(glob.glob(os.path.join(LOGS_DIR, '*.log')))
    for old in logs[:-LOGS_TO_KEEP]:
        os.remove(old)


# ── Auth ───────────────────────────────────────────────────────────────────────

def get_credentials():
    creds = None

    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, 'rb') as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow  = InstalledAppFlow.from_client_secrets_file(find_client_secrets(), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(CREDENTIALS_FILE, 'wb') as f:
            pickle.dump(creds, f)

    return creds

# ── YouTube ────────────────────────────────────────────────────────────────────

def get_upcoming_broadcast_titles(youtube):
    """Returns the set of titles for all upcoming scheduled broadcasts."""
    titles  = set()
    request = youtube.liveBroadcasts().list(
        part='snippet',
        broadcastStatus='upcoming',
        maxResults=50,
    )
    while request:
        response = request.execute()
        for item in response.get('items', []):
            titles.add(item['snippet']['title'])
        request = youtube.liveBroadcasts().list_next(request, response)
    return titles

def create_broadcast_with_stream(youtube, title, start_time):
    broadcast = youtube.liveBroadcasts().insert(
        part='snippet,status',
        body={
            'snippet': {
                'title': title,
                'scheduledStartTime': start_time.isoformat(),
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': False,
            },
        }
    ).execute()

    stream = youtube.liveStreams().insert(
        part='snippet,cdn',
        body={
            'snippet': {'title': title},
            'cdn': STREAM_CDN,
        }
    ).execute()

    youtube.liveBroadcasts().bind(
        part='id,contentDetails',
        id=broadcast['id'],
        streamId=stream['id'],
    ).execute()

# ── Schedule ───────────────────────────────────────────────────────────────────

def get_expected_events():
    """Returns (date, event) pairs for every event occurrence in the next 7 days."""
    today  = datetime.datetime.now(TIMEZONE).date()
    result = []

    for offset in range(1, 8):
        date = today + datetime.timedelta(days=offset)
        for event in EVENTS:
            if date.weekday() == event['weekday']:
                result.append((date, event))

    return result

def build_start_time(date, hour, minute):
    naive = datetime.datetime(date.year, date.month, date.day, hour, minute)
    return TIMEZONE.localize(naive)

def build_title(date, event_title):
    return f"{date.strftime('%m/%d/%Y')} - {event_title}"

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    setup_logging()
    logging.info('Scheduler started')

    creds   = get_credentials()
    youtube = build('youtube', 'v3', credentials=creds)

    existing_titles = get_upcoming_broadcast_titles(youtube)

    for date, event in get_expected_events():
        title = build_title(date, event['title'])

        if title in existing_titles:
            logging.info(f'Already exists: {title}')
            continue

        start_time = build_start_time(date, event['hour'], event['minute'])

        try:
            create_broadcast_with_stream(youtube, title, start_time)
            logging.info(f'Created: {title}')
        except Exception as e:
            logging.error(f'Failed to create "{title}": {e}')

    logging.info('Scheduler finished')

if __name__ == '__main__':
    main()
