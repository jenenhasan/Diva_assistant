import threading
import time
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)

WAKE_WORDS = ["diva", "hey diva", "hello diva", "wake up"]


class WakeWordDetector:
    """
    Lightweight wake-word detector that uses the existing STT engine.
    It continuously records short audio clips and checks for a wake word.
    When triggered it calls the provided callback.
    """

    def __init__(self, recorder, stt_engine, callback: Callable, wake_words: list = None):
        self.recorder = recorder
        self.stt = stt_engine
        self.callback = callback
        self.wake_words = [w.lower() for w in (wake_words or WAKE_WORDS)]
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def _contains_wake_word(self, text: str) -> bool:
        text_lower = text.lower()
        return any(word in text_lower for word in self.wake_words)

    def _listen_loop(self):
        logger.info("Wake-word detector started")
        while self._running:
            try:
                audio_path = self.recorder.record(duration=2.5, silence_timeout=1.5)
                if not audio_path:
                    continue
                result = self.stt.recognize(audio_path)
                if result and self._contains_wake_word(result.text):
                    logger.info(f"Wake word detected: '{result.text}'")
                    self.callback()
                    time.sleep(1.0)  # brief cooldown after trigger
            except Exception as e:
                logger.error(f"Wake-word loop error: {e}")
                time.sleep(0.5)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
            self._thread = None
        logger.info("Wake-word detector stopped")