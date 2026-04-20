import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _get_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w", encoding="utf-8") as f:
            f.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)


def create_event(title, date_str, time_str, description):
    service = _get_service()
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    start_day = date_obj.isoformat() + "Z"
    end_day = (date_obj + timedelta(days=1)).isoformat() + "Z"

    existing = (
        service.events()
        .list(calendarId="primary", timeMin=start_day, timeMax=end_day, singleEvents=True)
        .execute()
    )
    for item in existing.get("items", []):
        if item.get("summary", "").strip().lower() == str(title).strip().lower():
            print(f"[calendar] skipped duplicate: {title}")
            return

    if time_str:
        start_iso = f"{date_str}T{time_str}:00"
        end_dt = datetime.strptime(start_iso, "%Y-%m-%dT%H:%M:%S") + timedelta(hours=1)
        body = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start_iso},
            "end": {"dateTime": end_dt.strftime("%Y-%m-%dT%H:%M:%S")},
        }
    else:
        body = {
            "summary": title,
            "description": description,
            "start": {"date": date_str},
            "end": {"date": (date_obj + timedelta(days=1)).strftime("%Y-%m-%d")},
        }

    service.events().insert(calendarId="primary", body=body).execute()
    print(f"[calendar] created: {title}")
