#!/usr/bin/env python3
"""
Checks the BYOD & Paper Test Supervision Shifts page for available shifts
and emails you when new shifts appear.

Designed to be run on a schedule by GitHub Actions (see
.github/workflows/check-shifts.yml), but also runs fine locally.

State is kept in state.json so we only email when something actually
changes (not on every single run).
"""

import json
import os
import re
import smtplib
import sys
from email.mime.text import MIMEText
from pathlib import Path

from playwright.sync_api import sync_playwright

STATE_FILE = Path(__file__).parent / "state.json"

# --- Config from environment / GitHub Secrets ---------------------------
SHIFT_URL = os.environ["SHIFT_URL"]  # your personalised link from the email
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ["SMTP_USER"]
SMTP_PASS = os.environ["SMTP_PASS"]
NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", SMTP_USER)

PAPER_LABEL = "Number of Available PAPER Shifts"
BYOD_LABEL = "Number of Available BYOD Shifts"


def fetch_counts() -> dict:
    """Load the page with a real browser (it's a JS-rendered Airtable
    interface) and pull out the two shift counts."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(SHIFT_URL, wait_until="networkidle", timeout=60_000)

        # The interface loads its data asynchronously even after
        # networkidle, so wait for one of the known labels to actually
        # show up, then give it a moment to settle.
        page.wait_for_selector(f"text={PAPER_LABEL}", timeout=30_000)
        page.wait_for_timeout(3000)

        body_text = page.inner_text("body")
        browser.close()

    def extract(label: str) -> int:
        match = re.search(rf"{re.escape(label)}\s*\n?\s*(\d+)", body_text)
        if not match:
            raise RuntimeError(
                f"Could not find '{label}' on the page — the page layout "
                "may have changed. Check the raw text below:\n\n" + body_text[:2000]
            )
        return int(match.group(1))

    return {
        "paper": extract(PAPER_LABEL),
        "byod": extract(BYOD_LABEL),
    }


def load_last_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"paper": 0, "byod": 0}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state))


def send_email(subject: str, body: str) -> None:
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = NOTIFY_EMAIL

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)


def main() -> None:
    current = fetch_counts()
    previous = load_last_state()

    print(f"Previous: {previous}  |  Current: {current}")

    changed = current != previous
    has_shifts = current["paper"] > 0 or current["byod"] > 0

    if changed and has_shifts:
        subject = "🔔 New supervision shifts available!"
        body = (
            f"Paper shifts available: {current['paper']}\n"
            f"BYOD shifts available: {current['byod']}\n\n"
            f"Book here: {SHIFT_URL}"
        )
        send_email(subject, body)
        print("Change detected with shifts available — email sent.")
    elif changed:
        print("Counts changed but nothing available right now — no email.")
    else:
        print("No change since last check — no email.")

    save_state(current)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
