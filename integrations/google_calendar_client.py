import os
from datetime import datetime, timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pathlib

cred_path = pathlib.Path(__file__).parent / "googlecal.json"

SCOPES = ["https://www.googleapis.com/auth/calendar"]

class GoogleCalendarClient:
    def __init__(self, creds_file: str = "googlecal.json", token_file: str = "token.json"):
        self.creds_file = creds_file
        self.token_file = token_file
        self.service = self._authenticate()

    def _authenticate(self):
        creds = None
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.creds_file, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(self.token_file, "w") as token:
                token.write(creds.to_json())
        return build("calendar", "v3", credentials=creds)

    def insert_event(self, event_dict: dict) -> dict:
        try:
            result = self.service.events().insert(calendarId="primary", body=event_dict).execute()
            return result
        except HttpError as e:
            raise Exception(f"Google Calendar API error: {e}")

    def list_events(self, time_min: datetime = None, max_results: int = 10) -> list:
        time_min = time_min or datetime.now(timezone.utc).isoformat()
        events_result = self.service.events().list(
            calendarId="primary",
            timeMin=time_min,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        return events_result.get("items", [])
    
if __name__ == '__main__' : 
    client = GoogleCalendarClient(creds_file=cred_path)
    events = client.list_events(max_results=5)
    print(f"Found {len(events)} upcoming events")
    for e in events:
        print(f"- {e.get('summary', 'No title')}")