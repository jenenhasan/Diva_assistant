
from datetime import datetime, timedelta, timezone
import re
import dateparser

class CalendarService:
    def __init__(self, calendar_client):
        self.client = calendar_client

    # ---------- pure business logic ----------
    def create_event(self, summary: str, start_time: datetime, duration: int = 60, participants: list = None) -> dict:
        end_time = start_time + timedelta(minutes=duration)
        event = {
            "summary": summary,
            "start": {"dateTime": start_time.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end_time.isoformat(), "timeZone": "UTC"},
            "attendees": [{"email": email} for email in participants] if participants else [],
        }
        try:
            result = self.client.insert_event(event)
            return {
                "success": True,
                "message": f"Meeting '{summary}' scheduled for {start_time.strftime('%Y-%m-%d %H:%M')}",
                "event_id": result["id"]
            }
        except Exception as e:
            return {"success": False, "message": f"Failed to create event: {e}"}

    def create_task(self, summary: str, start_time: datetime, duration: int = 30, reminder_minutes: int = 30) -> dict:
        end_time = start_time + timedelta(minutes=duration)
        task = {
            "summary": f"TASK: {summary}",
            "start": {"dateTime": start_time.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end_time.isoformat(), "timeZone": "UTC"},
            "reminders": {
                "useDefault": False,
                "overrides": [{"method": "popup", "minutes": reminder_minutes}]
            },
            "transparency": "transparent",
            "visibility": "private"
        }
        try:
            result = self.client.insert_event(task)
            return {
                "success": True,
                "message": f"Task '{summary}' created for {start_time.strftime('%Y-%m-%d %H:%M')}",
                "event_id": result["id"]
            }
        except Exception as e:
            return {"success": False, "message": f"Task creation failed: {e}"}

    def parse_time_expression(self, command: str) -> dict:
        """Parse natural language time expression. Returns dict with 'valid', 'summary', 'start_time', 'duration', 'error'."""
        text = command.lower().strip()
        result = {
            "summary": "Untitled Event",
            "start_time": None,
            "local_time": None,
            "valid": False,
            "error": "",
            "duration": 60
        }
        try:
            # extract summary before time keyword
            summary_match = re.search(r'^(.*?)\s+(?:at|on|by|for)\s+', text)
            if summary_match:
                result["summary"] = summary_match.group(1).strip()
            time_setting = {
                'RELATIVE_BASE': datetime.now(),
                'PREFER_DATES_FROM': 'future',
                'PREFER_DAY_OF_MONTH': 'first',
                'DATE_ORDER': 'MDY'
            }
            time_match = re.search(r'\b(at|on|by|for)\s+(.*?)(?:\s+(?:to|till|until)\s+|\s*$)', text)
            if time_match:
                time_str = time_match.group(2)
                parsed_time = dateparser.parse(time_str, settings=time_setting)
                if parsed_time:
                    result["start_time"] = parsed_time
                    result["local_time"] = parsed_time
                    result["valid"] = True
                else:
                    result["error"] = "Couldn't understand time format"
            else:
                result["error"] = "No time information found"
            duration_match = re.search(r'for\s+(\d+)\s*(hours?|hrs?|minutes?|mins?)', text)
            if duration_match:
                dur = int(duration_match.group(1))
                unit = duration_match.group(2)[0]
                result["duration"] = dur * (60 if unit in ['h', 'hr', 'hour'] else dur)
        except Exception as e:
            result["error"] = f"Error parsing command: {str(e)}"
        return result

    def get_upcoming_events(self, max_results=10):
        return self.client.list_events(max_results=max_results)

    def done_so_far(self):
        """Return events that ended before now (completed)."""
        now = datetime.now(timezone.utc).isoformat()
        events_result = self.client.service.events().list(
            calendarId="primary",
            timeMax=now,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        return events_result.get("items", [])