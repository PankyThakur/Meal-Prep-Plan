from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta

SCOPES = ["https://www.googleapis.com/auth/calendar"]
ROOT = Path(__file__).resolve().parent.parent  # meal-prep-project/
CALENDAR_ID = "40124dd3644c9e450ad2afe1d714d52697917f80c740eb159fb10ed71aca21d9@group.calendar.google.com"

def get_calendar_service():
    creds = None
    token_path = ROOT / "token.json"
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(ROOT / "credentials.json"), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())
    return build("calendar", "v3", credentials=creds)

def get_calendar(start_date: str, end_date: str) -> list[dict]:
    """Returns the busy blocks on the user's calendar between start_date and end_date, inclusive. Dates are ISO strings like "2026-11-07". Use this after the user names the days they want to meal prep (for example, "Saturday or Sunday") to find which times are already taken. Each busy block has a start and an end time. Call get_current_date first if the user says a relative day like "this Saturday". It does not return free slots; the model must work out the gaps between busy blocks."""
    service = get_calendar_service()
    time_min = f"{start_date}T00:00:00-05:00"
    time_max = f"{end_date}T23:59:59-05:00"
    result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy="startTime",
    ).execute()
    return [
        {"start": e["start"].get("dateTime", e["start"].get("date")),
         "end": e["end"].get("dateTime", e["end"].get("date")),
         "title": e.get("summary", "(no title)")}
        for e in result.get("items", [])
    ]

def book_slot(date: str, start: str, end: str, title: str, description: str, reminder_minutes: int = 15) -> dict:
    """Creates one event on the user's calendar and returns its "status", "event_id", "link", "start", and "end". date is an ISO string like "2026-11-09"; start and end are 24-hour times like "07:00" and "07:30" in America/New_York. Put the recipe name in title, and the short description plus the numbered recipe steps in description. reminder_minutes sets a popup reminder that many minutes before the start. This is the only tool that changes anything: call it only after the user has approved the plan in a separate message, once per approved slot. It does not check for clashes, so check get_calendar first, and it cannot edit or delete events."""
    try:
        start_dt = datetime.fromisoformat(f"{date}T{start}")
        end_dt = datetime.fromisoformat(f"{date}T{end}")
    except ValueError:
        return {"status": "error", "message": "Use date YYYY-MM-DD and times HH:MM (24-hour)."}
    if end_dt <= start_dt:
        return {"status": "error", "message": "end must be after start."}

    event = {
        "summary": title,
        "description": description,
        "start": {"dateTime": start_dt.isoformat(), "timeZone": "America/New_York"},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": "America/New_York"},
        "reminders": {"useDefault": False, "overrides": [{"method": "popup", "minutes": reminder_minutes}]},
    }
    created = get_calendar_service().events().insert(calendarId=CALENDAR_ID, body=event).execute()
    return {
        "status": "booked",
        "event_id": created["id"],
        "link": created.get("htmlLink"),
        "start": created["start"]["dateTime"],
        "end": created["end"]["dateTime"],
    }
