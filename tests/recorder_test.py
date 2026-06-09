import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.audio.recorder import MicrophoneRecorder
import subprocess

def test():
    print("Recording 3 seconds... Speak now.")
    recorder = MicrophoneRecorder(device_index=4, rate=44100)
    audio_file = recorder.record(duration=3, silence_timeout=0.7)
    print(f"Saved: {audio_file}")
    subprocess.run(["aplay", audio_file])

if __name__ == "__main__":
    test()