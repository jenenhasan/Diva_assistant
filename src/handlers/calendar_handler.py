class Calendarhandler:
    def __init__(self, dialog, calendar_service, gemini_service=None):
        self.dialog = dialog
        self.calendar = calendar_service
        self.gemini = gemini_service

    def register(self, router):
        """Register all calendar intents with the router."""
        router.register(r"create (an? )?event|schedule (a )?meeting", self.handle_create_event)
        router.register(r"create (a )?task|add (a )?task", self.handle_create_task)
        router.register(r"show (upcoming )?events", self.handle_show_upcoming_events)
        router.register(r"what( do I have|'s on my calendar| events)", self.handle_show_upcoming_events)
        router.register(r"done so far|completed tasks|what have I done", self.handle_done_so_far)
        return self

    def handle_create_event(self):
        """Create a new calendar event via voice dialog."""
        self.dialog.speak("Let's schedule an event. Tell me the name and time.")
        
        command = self.dialog.listen_with_retry(
            "For example, 'Team meeting tomorrow at 2pm'",
            "I didn't catch that. Please say the event name and time."
        )
        if not command:
            self.dialog.speak("Event creation cancelled.")
            return

        parsed = self.calendar.parse_time_expression(command)
        if not parsed["valid"]:
            self.dialog.speak(f"Sorry, I didn't understand: {parsed['error']}")
            return

        time_str = parsed["start_time"].strftime('%A at %I:%M %p')
        
        if not self.dialog.confirm(f"Create '{parsed['summary']}' for {time_str} for {parsed.get('duration', 60)} minutes?"):
            self.dialog.speak("Event creation cancelled.")
            return

        self.dialog.show_thinking()
        result = self.calendar.create_event(
            parsed["summary"], 
            parsed["start_time"], 
            parsed.get("duration", 60)
        )
        self.dialog.hide_thinking()

        if result["success"]:
            self.dialog.speak(f"All set! {result['message']}")
        else:
            self.dialog.speak(f"Sorry, I couldn't create the event: {result['message']}")

    def handle_create_task(self):
        """Create a new task via voice dialog."""
        self.dialog.speak("Let's add a task. Tell me the task and due date.")
        
        command = self.dialog.listen_with_retry(
            "For example, 'Finish report by Friday' or 'Call client tomorrow at 3pm'",
            "Please repeat the task and due date."
        )
        if not command:
            self.dialog.speak("Task creation cancelled.")
            return

        parsed = self.calendar.parse_time_expression(command)
        if not parsed["valid"]:
            self.dialog.speak(f"Sorry, I didn't understand: {parsed['error']}")
            return

        time_str = parsed["start_time"].strftime('%A at %I:%M %p')
        
        if not self.dialog.confirm(f"Create task '{parsed['summary']}' due {time_str}?"):
            self.dialog.speak("Task creation cancelled.")
            return

        self.dialog.show_thinking()
        result = self.calendar.create_task(parsed["summary"], parsed["start_time"])
        self.dialog.hide_thinking()

        if result["success"]:
            self.dialog.speak(f"Task added. {result['message']}")
        else:
            self.dialog.speak(f"Sorry, I couldn't create the task: {result['message']}")

    def handle_show_upcoming_events(self):
        """Show upcoming calendar events."""
        self.dialog.show_thinking()
        events = self.calendar.get_upcoming_events(max_results=5)
        self.dialog.hide_thinking()

        if not events:
            self.dialog.speak("You have no upcoming events.")
            return

        self.dialog.speak(f"You have {len(events)} upcoming events:")
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            # Format the date/time for speech
            if 'T' in start:
                date_part = start.split('T')[0]
                time_part = start.split('T')[1][:5]
                self.dialog.speak(f"{date_part} at {time_part}: {event['summary']}")
            else:
                self.dialog.speak(f"{start}: {event['summary']}")

    def handle_done_so_far(self):
        """Show completed events and tasks."""
        self.dialog.show_thinking()
        events = self.calendar.done_so_far()
        self.dialog.hide_thinking()

        if not events:
            self.dialog.speak("No completed events or tasks found.")
            return

        self.dialog.speak(f"Here's what you've completed:")
        for event in events[:5]:
            start = event['start'].get('dateTime', event['start'].get('date'))
            if 'T' in start:
                date_part = start.split('T')[0]
                self.dialog.speak(f"{date_part}: {event['summary']}")
            else:
                self.dialog.speak(f"{start}: {event['summary']}")


if __name__ == "__main__":
    from unittest.mock import MagicMock

    class MockDialog:
        def __init__(self):
            self.responses = []
            self.response_index = 0

        def speak(self, text):
            print(f"[ASSISTANT] {text}")

        def listen_with_retry(self, prompt=None, retry_prompt=None):
            if self.response_index < len(self.responses):
                ans = self.responses[self.response_index]
                self.response_index += 1
                return ans
            return ""

        def show_thinking(self):
            print("[THINKING...]")

        def hide_thinking(self):
            print("[DONE]")

        def confirm(self, question):
            print(f"[CONFIRM] {question}")
            return True

    class MockCalendarService:
        def parse_time_expression(self, command):
            from datetime import datetime, timedelta
            return {
                "valid": True,
                "summary": "Test Meeting",
                "start_time": datetime.now() + timedelta(days=1),
                "duration": 60
            }

        def create_event(self, summary, start_time, duration):
            return {"success": True, "message": f"Event '{summary}' created"}

        def create_task(self, summary, start_time):
            return {"success": True, "message": f"Task '{summary}' created"}

        def get_upcoming_events(self, max_results=5):
            return [
                {"summary": "Team meeting", "start": {"dateTime": "2025-06-15T14:00:00"}},
                {"summary": "Client call", "start": {"dateTime": "2025-06-16T10:00:00"}}
            ]

        def done_so_far(self):
            return [
                {"summary": "Finished report", "start": {"dateTime": "2025-06-10T17:00:00"}},
                {"summary": "Fixed bug", "start": {"dateTime": "2025-06-09T15:30:00"}}
            ]

    print("\n🧪 TESTING CalendarHandler\n")
    method = input("Which method? (event / task / upcoming / done): ").strip().lower()

    mock_dialog = MockDialog()
    mock_calendar = MockCalendarService()
    handler = Calendarhandler(mock_dialog, mock_calendar)

    if method == "event":
        mock_dialog.responses = ["Test meeting tomorrow at 2pm"]
        handler.handle_create_event()
    elif method == "task":
        mock_dialog.responses = ["Finish report by Friday"]
        handler.handle_create_task()
    elif method == "upcoming":
        handler.handle_show_upcoming_events()
    elif method == "done":
        handler.handle_done_so_far()
    else:
        print("Unknown method. Use 'event', 'task', 'upcoming', or 'done'.")