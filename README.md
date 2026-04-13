# YouTube Live Stream Scheduler

Python script that runs nightly on the Video PC and ensures YouTube live broadcast events exist for all services in the next 7 days. Broadcasts that already exist are left untouched — only missing ones are created.

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

## How deployment works

Pushing to `main` triggers a GitHub Actions workflow that runs on the Video PC via a self-hosted runner. The workflow:

1. Installs Python 3.12 if not already present
2. Installs Python dependencies
3. Copies `scheduler.py` to `C:\git\vale-church-of-christ\youtube-stream-scheduler\`
4. Writes credentials from GitHub Secrets on first deploy to a new PC
5. Creates or updates a Windows scheduled task that runs the script nightly at 11:00 PM as SYSTEM

---

## Adding a new PC

Install the GitHub Actions self-hosted runner — that's it. Everything else is handled automatically on the next push to `main`.

1. Go to **Settings → Actions → Runners → New self-hosted runner**.
2. Select **Windows** and run the commands shown — they include a unique token, so copy them directly from that page.
3. Push any change to `main` to trigger deployment.

---

## Google authentication

> **This only needs to be done once ever.** Credentials are stored in GitHub Secrets and deployed automatically to every PC. Only repeat these steps if authentication is invalidated — e.g., if access is manually revoked or the Google account password changes.

### Why we use a dedicated generic Gmail account

The script authenticates as a **dedicated generic Gmail account** (not the Workspace account). Google Workspace admins can enforce session/token expiration policies (e.g., 14-day forced re-auth) that apply to all accounts in the org — including OAuth refresh tokens. A plain Gmail account is not subject to those policies, so the refresh token persists indefinitely (until manually revoked or inactive for 6+ months). The generic account is granted channel manager access on the brand channel.

### 0. Set up the generic Gmail account

1. Create (or designate) a generic Gmail account for streaming use — e.g. `valepark.streaming@gmail.com`.
2. In [YouTube Studio](https://studio.youtube.com), go to **Settings → Channel → Permissions** and invite the generic Gmail account as a **Manager**.
3. Accept the invite by signing in to YouTube as the generic Gmail account.

### 1. Google Cloud Console

> Create the Cloud project while signed in as the generic Gmail account to keep everything under one non-Workspace identity.

1. Go to [console.cloud.google.com](https://console.cloud.google.com) and create a new project.
2. Enable the YouTube Data API v3: **APIs & Services → Enable APIs → search "YouTube Data API v3" → Enable**.
3. Configure the OAuth consent screen: **APIs & Services → OAuth consent screen**.
   - User type: **External**
   - Publishing status: **Testing** (set during initial creation)
   - Under **Test users**, add the brand account: `vale-church-of-6243@pages.plusgoogle.com`
   - > **Important:** After saving, change the publishing status to **"In production"** (there is a "Publish app" button on the consent screen page). Testing mode causes refresh tokens to expire after 7 days. Switching to production removes that limit. Google will show an "unverified app" warning during the one-time auth flow — click **"Advanced → Go to [app] (unsafe)"** to proceed. No formal Google review is required for a Desktop app used by a small number of known accounts.
4. Create OAuth credentials: **APIs & Services → Credentials → Create Credentials → OAuth client ID**.
   - Application type: **Desktop app**
5. Download the credentials JSON file — you'll need its contents in the next step.

### 2. Authorize against the Brand Page channel

1. Install dependencies locally: `pip install -r requirements.txt`
2. Delete any existing `credentials.pkl` in `C:\git\vale-church-of-christ\youtube-stream-scheduler\` — the script will skip the auth flow if this file is present.
3. Place `client_secrets.json` in this folder and run:

   ```powershell
   python scheduler.py
   ```

4. A browser window will open. **Sign in as the generic Gmail account** (not the Workspace account). When prompted to choose a channel, select the **Vale Park Church of Christ** brand channel.

### 3. Store credentials in GitHub Secrets

In this repository go to **Settings → Secrets and variables → Actions → New repository secret** and add the following two secrets.

**`YOUTUBE_CLIENT_SECRETS`** — paste the full contents of `client_secrets.json`.

**`YOUTUBE_CREDENTIALS`** — base64-encoded OAuth token. Run the following and paste the output as the secret value:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\git\vale-church-of-christ\youtube-stream-scheduler\credentials.pkl")) | Set-Clipboard
```

---

## Running manually

```powershell
cd C:\git\vale-church-of-christ\youtube-stream-scheduler
python scheduler.py
```
