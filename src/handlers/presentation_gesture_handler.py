class PresentationGestureHandler:
    def __init__(self, dialog, gesture_service):
        self.dialog = dialog
        self.gesture = gesture_service

    def register(self, router):
        """Register all presentation gesture intents with the router."""
        router.register(r"start presentation gesture|presentation mode on|start gesture presentation", self.handle_start_gesture)
        router.register(r"stop presentation gesture|presentation mode off|stop gesture presentation", self.handle_stop_gesture)
        router.register(r"toggle presentation gesture|presentation mode|gesture presentation", self.handle_toggle_gesture)
        return self

    def handle_start_gesture(self):
        """Start presentation gesture tracking."""
        if self.gesture.is_running():
            self.dialog.speak("Presentation gesture tracking is already running.")
            return

        self.dialog.show_thinking()
        result = self.gesture.start()
        self.dialog.hide_thinking()

        if result["success"]:
            self.dialog.speak("Presentation gesture tracking started. Swipe right for next slide, left for previous slide.")
            self.dialog.speak("Say 'stop presentation gesture' to turn it off.")
        else:
            self.dialog.speak(f"Failed to start gesture tracking: {result['error']}")

    def handle_stop_gesture(self):
        """Stop presentation gesture tracking."""
        if not self.gesture.is_running():
            self.dialog.speak("Presentation gesture tracking is not running.")
            return

        self.dialog.show_thinking()
        result = self.gesture.stop()
        self.dialog.hide_thinking()

        if result["success"]:
            self.dialog.speak("Presentation gesture tracking stopped.")
        else:
            self.dialog.speak(f"Failed to stop gesture tracking: {result['error']}")

    def handle_toggle_gesture(self):
        """Toggle presentation gesture tracking on/off."""
        if self.gesture.is_running():
            self.handle_stop_gesture()
        else:
            self.handle_start_gesture()


if __name__ == "__main__":
    from unittest.mock import MagicMock
    
    class MockDialog:
        def speak(self, text):
            print(f"[ASSISTANT] {text}")
        
        def show_thinking(self):
            print("[THINKING...]")
        
        def hide_thinking(self):
            print("[DONE]")
    
    class MockGestureService:
        def __init__(self):
            self._running = False
        
        def is_running(self):
            return self._running
        
        def start(self):
            self._running = True
            return {"success": True, "message": "Started"}
        
        def stop(self):
            self._running = False
            return {"success": True, "message": "Stopped"}
    
    print("\n🧪 TESTING PresentationGestureHandler\n")
    mock_dialog = MockDialog()
    mock_gesture = MockGestureService()
    handler = PresentationGestureHandler(mock_dialog, mock_gesture)
    
    print("Testing start...")
    handler.handle_start_gesture()
    print("\nTesting stop...")
    handler.handle_stop_gesture()