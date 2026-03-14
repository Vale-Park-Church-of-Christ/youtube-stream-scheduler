# YouTube Live Stream Scheduler

Python script that runs nightly on a church PC and ensures YouTube live broadcast events exist for all services in the next 7 days. Broadcasts that already exist are left untouched — only missing ones are created.

## Events

| Event | Day | Time (CT) |
| --- | --- | --- |
| Sunday Morning Adult Bible Class | Sunday | 9:00 AM |
| Sunday Morning Worship Service | Sunday | 10:00 AM |
| Sunday Evening Worship Service | Sunday | 5:00 PM |
| Wednesday Evening Adult Bible Class | Wednesday | 6:00 PM |

Each broadcast title is prefixed with the event date in `MM/DD/YYYY -` format (e.g., `03/15/2026 - Sunday Morning Worship Service`).

## Stream Settings

- **Resolution:** 1080p
- **Frame rate:** 30fps
- **Ingest type:** RTMP (auto-generated stream key per event)
- **Privacy:** Public

## Prerequisites

- Python 3.8 or later
- A Google Cloud project with the YouTube Data API v3 enabled

## Setup

### 1. Google Cloud Console

1. Go to [console.cloud.google.com](https://console.cloud.google.com) and create a new project.
2. Enable the YouTube Data API v3: **APIs & Services → Enable APIs → search "YouTube Data API v3" → Enable**.
3. Create OAuth credentials: **APIs & Services → Credentials → Create Credentials → OAuth client ID**.
   - Application type: **Desktop app**
4. Download the credentials JSON file and save it as `client_secrets.json` in this folder.

### 2. Install dependencies

```bat
pip install -r requirements.txt
```

### 3. Authorize against the Brand Page channel

Run the script once manually from the folder:

```bat
python scheduler.py
```

A browser window will open. **Sign in with the Google account that manages the church's YouTube channel and select the Vale Park Church of Christ channel when prompted.** Credentials are saved to `credentials.pkl` — subsequent runs (including scheduled ones) will use this file and refresh it automatically.

### 4. Windows Task Scheduler

1. Open **Task Scheduler** and click **Create Task**.
2. **General tab:** give it a name (e.g., `YouTube Stream Scheduler`).
3. **Triggers tab:** New trigger → Daily → set a time (e.g., 11:00 PM).
4. **Actions tab:** New action:
   - Program: full path to `python.exe` (e.g., `C:\Python312\python.exe`)
   - Arguments: `scheduler.py`
   - Start in: full path to this folder
5. **Conditions tab:** uncheck "Start only if the computer is on AC power" if the PC may be on battery.
6. Click OK. The script will run automatically every night.

> **Note:** The church PC must be on when the task runs. If it misses a night, the next time it runs it will catch up — the script always checks the full 7-day window and creates anything missing.

## Running manually

```bat
python scheduler.py
```
