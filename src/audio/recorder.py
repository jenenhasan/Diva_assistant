import pyaudio
import wave
import tempfile
import os
import time
import threading

class MicrophoneRecorder:
    """Simple recorder that writes WAV files from microphone."""
    def __init__(self, rate=16000, chunk=1024, channels=1, format=pyaudio.paInt16):
        self.rate = rate
        self.chunk = chunk
        self.channels = channels
        self.format = format
        self.p = pyaudio.PyAudio()
        self.stream = None
        self._lock = threading.Lock()

    def record(self, duration: float, silence_timeout: float = 0.7) -> str:
        """
        Record until either duration or silence_timeout seconds of silence.
        Returns path to temporary WAV file.
        """
        with self._lock:
            self.stream = self.p.open(format=self.format,
                                       channels=self.channels,
                                       rate=self.rate,
                                       input=True,
                                       frames_per_buffer=self.chunk)
            frames = []
            silent_chunks = 0
            max_silent_chunks = int(silence_timeout * self.rate / self.chunk)
            start_time = time.time()
            while time.time() - start_time < duration:
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                frames.append(data)
                # simple energy detection
                energy = max(abs(int.from_bytes(data[i:i+2], 'little', signed=True))
                             for i in range(0, len(data), 2))
                if energy < 500:  # silence threshold
                    silent_chunks += 1
                else:
                    silent_chunks = 0
                if silent_chunks > max_silent_chunks and len(frames) > 10:
                    break
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

            # write to temp file
            fd, path = tempfile.mkstemp(suffix='.wav')
            with os.fdopen(fd, 'wb') as f:
                wf = wave.open(f, 'wb')
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.p.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(b''.join(frames))
                wf.close()
            return path
    

    def __del__(self):
        self.p.terminate()