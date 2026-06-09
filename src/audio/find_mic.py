import pyaudio

def find_microphone():
    """Find all available microphone devices."""
    p = pyaudio.PyAudio()
    print("Available input devices:")
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if dev['maxInputChannels'] > 0:
            print(f"  Index {i}: {dev['name']} (channels: {dev['maxInputChannels']}, rate: {int(dev['defaultSampleRate'])})")
    p.terminate()

if __name__ == "__main__":
    find_microphone()