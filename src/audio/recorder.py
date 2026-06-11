import pyaudio
import wave
import tempfile
import os
import time
import threading
import numpy as np

class MicrophoneRecorder:
    def __init__(self, device_index=None, rate=16000, chunk=1024, channels=1, format=pyaudio.paInt16):
        self.rate = rate
        self.chunk = chunk
        self.channels = channels
        self.format = format
        self.device_index = device_index
        self.p = None
        self._lock = threading.Lock()
        self._init_pyaudio()

    def _init_pyaudio(self):
        try:
            self.p = pyaudio.PyAudio()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize PyAudio: {e}")

    def record(self, duration=5, silence_timeout=0.7):
        """Record audio, returns path to WAV file."""
        with self._lock:
            if self.p is None:
                self._init_pyaudio()
            
            # Try to open stream with given device
            stream = None
            try:
                stream = self.p.open(
                    format=self.format,
                    channels=self.channels,
                    rate=self.rate,
                    input=True,
                    input_device_index=self.device_index,
                    frames_per_buffer=self.chunk
                )
            except Exception as e:
                print(f"[WARNING] Device {self.device_index} failed: {e}. Trying default device.")
                try:
                    stream = self.p.open(
                        format=self.format,
                        channels=self.channels,
                        rate=self.rate,
                        input=True,
                        frames_per_buffer=self.chunk
                    )
                except Exception as e2:
                    raise RuntimeError(f"Could not open any audio device: {e2}")
            
            frames = []
            silent_chunks = 0
            max_silent = int(silence_timeout * self.rate / self.chunk)
            start = time.time()
            
            try:
                while time.time() - start < duration:
                    data = stream.read(self.chunk, exception_on_overflow=False)
                    
                    # Simple noise gate
                    samples = np.frombuffer(data, dtype=np.int16)
                    if np.max(np.abs(samples)) < 500:
                        silent_chunks += 1
                        if silent_chunks > max_silent and len(frames) > 10:
                            break
                    else:
                        silent_chunks = 0
                    
                    frames.append(data)
            finally:
                stream.stop_stream()
                stream.close()
            
            # Save to temp file
            fd, path = tempfile.mkstemp(suffix='.wav')
            with os.fdopen(fd, 'wb') as f:
                with wave.open(f, 'wb') as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(self.p.get_sample_size(self.format))
                    wf.setframerate(self.rate)
                    wf.writeframes(b''.join(frames))
            return path

    def __del__(self):
        if self.p:
            try:
                self.p.terminate()
            except:
                pass