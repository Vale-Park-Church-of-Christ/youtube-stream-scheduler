# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

A Python script that automatically creates YouTube live broadcast events for Vale Park Church of Christ. It runs nightly at 11:00 PM via Windows Task Scheduler and creates any missing broadcasts for the next 7 days based on the recurring service schedule. It is idempotent — safe to run multiple times; it never modifies existing broadcasts.

## Running the Script

```powershell
pip install -r requirements.txt
python scheduler.py
```

To inspect an existing broadcast's API resource details (debugging):
```powershell
python scheduler.py inspect <broadcast_id>
```

There are no automated tests. Manual execution is the validation method.

## Architecture

All logic lives in `scheduler.py`. The execution flow:

1. **Auth** — `get_credentials()` loads `credentials.pkl`; refreshes the OAuth token automatically; launches browser for interactive auth if credentials are missing entirely.
2. **Fetch existing** — `get_upcoming_broadcast_titles()` calls YouTube API to list existing broadcasts in the next 7 days.
3. **Compute expected** — `get_expected_events()` generates required events from the `EVENTS` config dict.
4. **Diff & create** — For each expected event not matched by title, `create_broadcast_with_stream()` calls the YouTube API to: create a liveBroadcast, create a liveStream (1080p/30fps/RTMP), bind them, update video metadata, and optionally add to a playlist.
5. **Log** — Rotating logs written to `logs/` (last 10 files retained).

## Event Configuration

The `EVENTS` list in `scheduler.py` drives what gets scheduled. Each entry has day-of-week, time (CT), title, and optional playlist name. Current services: Sunday Bible Class (9 AM), Sunday Morning Worship (10 AM), Sunday Evening Worship (5 PM), Wednesday Bible Class (6 PM).

Broadcast titles follow the pattern: `MM/DD/YYYY - [Event Title]`. Matching is done by exact title, so title format changes require care.

## Credentials & Deployment

- `client_secrets.json` — OAuth app credentials (not committed; safe to include in repo per Google's design, but excluded anyway).
- `credentials.pkl` — OAuth refresh token (sensitive; excluded from git; stored base64-encoded in GitHub Secret `YOUTUBE_CREDENTIALS`).

The GitHub Actions workflow (`.github/workflows/deploy.yml`) runs on a self-hosted runner on the Video PC. It writes credentials, installs dependencies, and creates/updates the Windows scheduled task. Pushing to `main` triggers deployment.

**Why a generic Gmail account (`valepark.streaming@gmail.com`):** Google Workspace enforces refresh token expiration (e.g., 14-day forced re-auth). Plain Gmail accounts are exempt, so the refresh token persists indefinitely. This account holds Manager access on the Vale Park brand channel.

**Re-authenticating** (if `credentials.pkl` is ever lost): run the script manually on the Video PC — a browser window opens, sign in as `valepark.streaming@gmail.com`, and the new `credentials.pkl` must be base64-encoded and updated in GitHub Secrets.

## Key Constants (hardcoded in `scheduler.py`)

| Setting | Value |
|---|---|
| Timezone | America/Chicago |
| Stream quality | 1080p, 30fps, RTMP |
| Video category | 29 (Nonprofits & Activism) |
| Location tag | "Vale Church of Christ" |
| Scan window | Next 7 days |
| Log retention | 10 most recent files |
