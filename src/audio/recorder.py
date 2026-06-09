import pyaudio
import wave
import tempfile
import os
import time
import threading
import numpy as np

class MicrophoneRecorder:
    def __init__(self, device_index=4, rate=44100):
        self.rate = rate
        self.device_index = device_index
        self.p = pyaudio.PyAudio()
        self._lock = threading.Lock()

    def record(self, duration=5, silence_timeout=0.7):
        """Record audio, returns path to WAV file."""
        with self._lock:
            stream = self.p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=1024
            )
            
            frames = []
            silent_chunks = 0
            max_silent = int(silence_timeout * self.rate / 1024)
            start = time.time()
            
            while time.time() - start < duration:
                data = stream.read(1024, exception_on_overflow=False)
                
                # Simple noise gate
                samples = np.frombuffer(data, dtype=np.int16)
                if np.max(np.abs(samples)) < 500:  # silence threshold
                    silent_chunks += 1
                    if silent_chunks > max_silent and len(frames) > 10:
                        break
                else:
                    silent_chunks = 0
                    # Keep audio as-is (no hiss filtering needed)
                
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            
            # Save to temp file
            fd, path = tempfile.mkstemp(suffix='.wav')
            with os.fdopen(fd, 'wb') as f:
                with wave.open(f, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
                    wf.setframerate(self.rate)
                    wf.writeframes(b''.join(frames))
            return path

    def __del__(self):
        self.p.terminate()