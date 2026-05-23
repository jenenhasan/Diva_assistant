class Orchestrator:
    def __init__(self, dialog, router, handlers, gemini_service=None):
        self.dialog = dialog
        self.router = router
        self.handlers = handlers
        self.gemini = gemini_service
        self.running = True

    def run(self):
        self.dialog.speak("Voice assistant ready.")
        while self.running:
            text = self.dialog.listen(timeout=3)
            if not text:
                continue
            text_lower = text.lower()
            # Wake word check (simple)
            if any(w in text_lower for w in ["hello", "hey", "wake up", "diva"]):
                self.dialog.speak("Yes? How can I help?")
                continue
            if "goodbye" in text_lower or "exit" in text_lower:
                self.dialog.speak("Goodbye!")
                self.running = False
                break
            handler = self.router.route(text)
            if handler:
                handler()
            elif self.gemini:
                self.dialog.show_thinking()
                answer = self.gemini.get_answer(text)
                self.dialog.speak(answer)
                self.dialog.hide_thinking()
            else:
                self.dialog.speak("Sorry, I didn't understand that command.")