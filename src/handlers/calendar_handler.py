


class Calendarhandler:
    def __init__(self , dialog , calendar_service , gemini_answer): 
        self.dialog = dialog
        self.calendar_service = calendar_service
        self.gemini_answer = gemini_answer
    def handle_create_event(self):
        self.dialog.speak("Let's schedule an event. Tell me the name and time.")
        command = self.dialog.listen_with_retry("For example, 'Team meeting tomorrow at 2pm'",
            "I didn't catch that. Please say the event name and time.")
        if not command : 
            return 
        parsed= self.calendar.parse_time_expressiona(command)
        if not parsed["valid"]:
            self.dialog.speak(f"sorry, I didnt understand: {parsed['error']}")
            return 
        time_str = parsed["start_time"].strftime('%A at %I:%M %p')
        if not self.dialog.confirm(f"Create '{parsed['summary']}' for {time_str}?"):
            self.dialog.speak("cancelled")
            return 
        self.dialog.show_thinking()
        result = self.calendar.create_event(parsed["summary"], parsed["start_time"] , parsed.get('duration' , 60))
        self.dialog.hide_thinking()
        self.dialog.speak(result["message"])
        
        


    