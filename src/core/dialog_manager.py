import time
import json
import sys

class DialogManager:
    def __init__(self, tts_engine, stt_engine, audio_recorder=None):
        self.tts = tts_engine
        self.stt = stt_engine
        self.recorder = audio_recorder  # optional: handles mic recording
        self.max_retries = 2
        self.short_timeout = 5
        self.long_timeout = 30

    def speak(self, text: str):
        self.tts.speak(text)
        # Also emit JSON for frontend if needed
        print(json.dumps({"event": "speak", "text": text}) + "\n", flush=True)

    def listen(self, prompt: str = None, timeout: int = 5) -> str:
        if prompt:
            self.speak(prompt)
        # Here you would record audio to a temp file using self.recorder
        # For simplicity, assume self.recorder.record(timeout) returns file path
        if self.recorder:
            audio_file = self.recorder.record(timeout)
            if audio_file:
                result = self.stt.recognize(audio_file)
                if result:
                    return result.text
        return ""

    def listen_with_retry(self, prompt: str, retry_prompt: str = None) -> str:
        for attempt in range(self.max_retries):
            text = self.listen(prompt if attempt == 0 else retry_prompt, timeout=self.long_timeout)
            if text:
                return text
            if attempt == 0 and retry_prompt is None:
                retry_prompt = "I didn't catch that. Please repeat."
        return ""

    def confirm(self, question: str) -> bool:
        answer = self.listen_with_retry(question + " Say yes to confirm, no to cancel.")
        return answer and "yes" in answer.lower()

    def choose(self, prompt: str, options: list) -> str:
        self.speak(prompt)
        for i, opt in enumerate(options, 1):
            self.speak(f"{i}. {opt}")
        response = self.listen_with_retry("Please say the number or name.")
        try:
            idx = int(response) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except:
            pass
        for opt in options:
            if opt.lower() in response.lower():
                return opt
        return ""

    def show_thinking(self):
        print(json.dumps({"event": "thinking"}) + "\n", flush=True)

    def hide_thinking(self):
        print(json.dumps({"event": "thinking_end"}) + "\n", flush=True)