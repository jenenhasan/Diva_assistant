import threading
import pyttsx3
import platform

class TTSEngine:
    def __init__(self, rate: int = 180, volume: float = 1.0):
        self._lock = threading.Lock()
        self.engine = self._init_engine(rate, volume)
        self._is_speaking = False

    def _init_engine(self, rate: int, volume: float):
        if platform.system() == "Windows":
            engine = pyttsx3.init(driverName='sapi5')
        else:
            engine = pyttsx3.init()
        engine.setProperty('rate', rate)
        engine.setProperty('volume', volume)
        voices = engine.getProperty('voices')
        if len(voices) > 1:
            engine.setProperty('voice', voices[1].id)
        return engine

    def speak(self, text: str):
        if not text:
            return
        with self._lock:
            self._is_speaking = True
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            finally:
                self._is_speaking = False

    def stop(self):
        with self._lock:
            if self._is_speaking:
                self.engine.stop()
                self._is_speaking = False

    @property
    def is_speaking(self) -> bool:
        return self._is_speaking