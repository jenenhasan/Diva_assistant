class TerminalHandler:
    def __init__(self, dialog, terminal_service, geminiservice=None):
        self.dialog = dialog
        self.gemini = geminiservice
        self.terminal = terminal_service
    

    def register(self, router):
        router.register(r"run (the )?command|execute", self.handle_execute_command)
        router.register(r"run and log", self.handle_run_and_log)
        router.register(r"explain last error|what was the last error", self.handle_explain_last_error)
        return self

    

    def handle_execute_command(self):
        """Execute a terminal command and report result."""
        command = self.dialog.listen_with_retry("What command would you like to run?")
        if not command:
            return

        self.dialog.show_thinking()
        result = self.terminal.run_command(command)
        self.dialog.hide_thinking()

        if result["success"]:
            self.dialog.speak("Command executed successfully.")
            if result.get("output") and len(result["output"]) < 200:
                self.dialog.speak(f"Output: {result['output']}")
        else:
            self.dialog.speak(f"Command failed: {result['error'][:200]}")
            
            # Ask for explanation if Gemini is available
            if self.gemini and self.dialog.confirm("Would you like me to explain the error?"):
                self._explain_error(result["error"], command)

    def handle_run_and_log(self):
        """Run a command and log any error to Notion."""
        command = self.dialog.listen_with_retry("What command would you like to run and log?")
        if not command:
            return

        self.dialog.show_thinking()
        result = self.terminal.run_command_with_logging(command, self.gemini)
        self.dialog.hide_thinking()

        if result["success"]:
            self.dialog.speak("Command executed successfully. No error to log.")
        else:
            self.dialog.speak(f"Command failed. Error has been logged to Notion.")
            if result.get("explanation"):
                self.dialog.speak(f"Explanation: {result['explanation'][:200]}")

    def handle_explain_last_error(self):
        """Explain the most recent terminal error."""
        result = self.terminal.get_last_error()
        
        if not result or not result.get("error"):
            self.dialog.speak("No recent terminal errors found.")
            return

        self.dialog.speak(f"Last error: {result['error'][:150]}")
        self._explain_error(result["error"], result.get("command", "unknown"))

    def _explain_error(self, error_message: str, command: str):
        """Use Gemini to explain an error."""
        if not self.gemini:
            self.dialog.speak("Gemini service not available.")
            return

        self.dialog.show_thinking()
        prompt = f"""
        A user ran this command: "{command}"
        And got this error: "{error_message[:1000]}"
        
        Please explain what went wrong and suggest a fix in 2-3 sentences.
        """
        explanation = self.gemini.get_answer(prompt)
        self.dialog.hide_thinking()
        self.dialog.speak(f"Explanation: {explanation[:300]}")


if __name__ == "__main__":
    from unittest.mock import MagicMock

    # Mock DialogManager
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
            print(f"[CONFIRM] {question} (y/n)")
            return input().strip().lower() in ("y", "yes")

    # Mock TerminalService
    class MockTerminalService:
        def run_command(self, command):
            if "invalid" in command:
                return {"success": False, "error": "Command not found", "output": ""}
            return {"success": True, "output": "Command output here", "error": ""}

        def run_command_with_logging(self, command, gemini=None):
            if "invalid" in command:
                return {"success": False, "error": "Command not found", "explanation": "Try installing the package"}
            return {"success": True, "output": "OK", "error": ""}

        def get_last_error(self):
            return {"error": "Previous command failed: file not found", "command": "cat missing.txt"}

    # Mock Gemini
    class MockGemini:
        def get_answer(self, prompt):
            return "This error means the command was not found. Try installing the required package."

    # Test
    print("\n🧪 TESTING TerminalHandler\n")
    method = input("Which method? (execute / runlog / explain): ").strip().lower()

    mock_dialog = MockDialog()
    mock_terminal = MockTerminalService()
    mock_gemini = MockGemini()

    handler = TerminalHandler(mock_dialog, mock_terminal, geminiservice=mock_gemini)

    if method == "execute":
        mock_dialog.responses = ["ls -la"]
        handler.handle_execute_command()
    elif method == "runlog":
        mock_dialog.responses = ["invalid_command"]
        handler.handle_run_and_log()
    elif method == "explain":
        handler.handle_explain_last_error()
    else:
        print("Unknown method. Use 'execute', 'runlog', or 'explain'.")