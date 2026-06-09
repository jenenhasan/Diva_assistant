# src/audio/recorder.py
import pyaudio
import wave
import tempfile
import os
import time
import threading
import numpy as np

class MicrophoneRecorder:
    def __init__(self, device_index=4, rate=44100, channels=1, chunk=1024):
        self.rate = rate
        self.chunk = chunk
        self.channels = channels
        self.device_index = device_index
        self.p = pyaudio.PyAudio()
        self._lock = threading.Lock()
        
        # Detect device capabilities
        self._detect_device_capabilities()

    def _detect_device_capabilities(self):
        """Detect the correct number of channels for the device."""
        try:
            dev_info = self.p.get_device_info_by_index(self.device_index)
            max_channels = int(dev_info.get('maxInputChannels', 1))
            if max_channels < self.channels:
                print(f"[WARNING] Device supports only {max_channels} channels. Using {max_channels}.")
                self.channels = max_channels
        except Exception:
            pass

    def record(self, duration=5, silence_timeout=0.7):
        """Record audio, returns path to WAV file."""
        with self._lock:
            try:
                stream = self.p.open(
                    format=pyaudio.paInt16,
                    channels=self.channels,  # Use detected channel count
                    rate=self.rate,
                    input=True,
                    input_device_index=self.device_index,
                    frames_per_buffer=self.chunk
                )
            except Exception as e:
                # If device 4 fails, try default device
                print(f"[WARNING] Device {self.device_index} failed: {e}. Trying default device.")
                stream = self.p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=self.rate,
                    input=True,
                    frames_per_buffer=self.chunk
                )
            
            frames = []
            silent_chunks = 0
            max_silent = int(silence_timeout * self.rate / self.chunk)
            start = time.time()
            
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
            
            stream.stop_stream()
            stream.close()
            
            # Save to temp file
            fd, path = tempfile.mkstemp(suffix='.wav')
            with os.fdopen(fd, 'wb') as f:
                with wave.open(f, 'wb') as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
                    wf.setframerate(self.rate)
                    wf.writeframes(b''.join(frames))
            return path

    def __del__(self):
        try:
            self.p.terminate()
        except:
            pass