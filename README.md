# Shift Notifier

Checks your "BYOD & Paper Test Supervision Shifts" page every 15 minutes and
emails you the moment new shifts become available.

## How it works
- GitHub Actions spins up a runner on a schedule, opens your personalised
  shift link in a headless browser (the page is a JS-rendered Airtable
  interface, so a plain HTTP request wouldn't see the data), and reads the
  two "Number of Available ... Shifts" counters.
- It compares the counts to the last check (stored in `state.json`, committed
  back to the repo each run).
- If the counts changed **and** at least one is greater than 0, it emails you.

## One-time setup (10 minutes)

### 1. Create a private GitHub repo
Create a new **private** repository and upload these files
(`checker.py`, `requirements.txt`, `.github/workflows/check-shifts.yml`).
Private matters because your personal shift link is sensitive.

### 2. Get a Gmail "app password" (or use another SMTP provider)
If you'll send from a Gmail account:
1. Turn on 2-Step Verification on that Google account, if not already on.
2. Go to https://myaccount.google.com/apppasswords and create an app
   password (choose "Mail" / "Other").
3. Copy the 16-character password — you'll paste it into a secret below.

(Any SMTP provider works — Outlook, iCloud, SendGrid, etc. Just adjust
`SMTP_SERVER` / `SMTP_PORT` accordingly.)

### 3. Add repository secrets
In your repo: **Settings → Secrets and variables → Actions → New repository
secret**. Add each of these:

| Secret name | Value |
|---|---|
| `SHIFT_URL` | Your personalised link from the shift email (the one that pre-fills your Staff ID) |
| `SMTP_SERVER` | `smtp.gmail.com` (or your provider's SMTP host) |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | The email address you're sending *from* |
| `SMTP_PASS` | The app password from step 2 |
| `NOTIFY_EMAIL` | The email address you want notified (can be the same as `SMTP_USER`) |

### 4. Turn it on
That's it — the workflow (`.github/workflows/check-shifts.yml`) is already
scheduled to run every 15 minutes. You can also trigger it manually any time
from the **Actions** tab → "Check for available shifts" → **Run workflow**,
which is the fastest way to confirm everything's wired up correctly.

## If it doesn't find the shift counts
Airtable interface pages can change their layout. If the workflow run fails
with "Could not find ... on the page", open the failed run's log — the
script prints the raw page text it saw, which makes it easy to spot what
changed and adjust the two label strings at the top of `checker.py`
(`PAPER_LABEL` / `BYOD_LABEL`).

## Adjusting the schedule
Edit the `cron` line in `.github/workflows/check-shifts.yml`. GitHub Actions
schedules aren't perfectly precise under load, so anything below 5 minutes
isn't worth setting — 15 minutes is a solid balance of promptness and being
a good citizen of GitHub's free scheduler.

## Notes on privacy
Your `SHIFT_URL` and email credentials only ever live as encrypted GitHub
secrets — they're not printed in logs and aren't visible to anyone without
admin access to the repo.
