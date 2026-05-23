import torch
import torchaudio
import whisper
import logging
import time
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RecognitionResult:
    text: str
    confidence: float
    engine: str   # 'silero' or 'whisper'
    processing_time: float

class STTEngine:
    """Hybrid STT: Silero (fast) + Whisper (accurate fallback)."""
    SAMPLE_RATE = 16000
    SILERO_CONF_THRESHOLD = 0.5

    def __init__(self, use_gpu: bool = True, silero_lang: str = 'en'):
        self.device = torch.device('cuda' if use_gpu and torch.cuda.is_available() else 'cpu')
        logger.info(f"STT using device: {self.device}")
        
        # Load Silero
        self.silero_model = None
        self.silero_decoder = None
        try:
            self.silero_model, self.silero_decoder, _ = torch.hub.load(
                'snakers4/silero-models',
                'silero_stt',
                language=silero_lang,
                device=self.device
            )
            self.silero_model.eval()
            logger.info("Silero loaded")
        except Exception as e:
            logger.warning(f"Silero failed: {e}")
        
        # Load Whisper
        self.whisper_model = None
        try:
            self.whisper_model = whisper.load_model("base", device=self.device)
            logger.info("Whisper loaded")
        except Exception as e:
            logger.warning(f"Whisper failed: {e}")

    def _load_audio(self, audio_path: str) -> Tuple[Optional[torch.Tensor], Optional[int]]:
        try:
            waveform, sr = torchaudio.load(audio_path)
            if sr != self.SAMPLE_RATE:
                resampler = torchaudio.transforms.Resample(sr, self.SAMPLE_RATE)
                waveform = resampler(waveform)
            if waveform.shape[0] > 1:
                waveform = waveform.mean(dim=0, keepdim=True)
            return waveform.squeeze(0), self.SAMPLE_RATE
        except Exception as e:
            logger.error(f"Audio load error: {e}")
            return None, None

    def recognize_silero(self, audio_path: str) -> Optional[RecognitionResult]:
        if not self.silero_model:
            return None
        start = time.time()
        try:
            waveform, _ = self._load_audio(audio_path)
            if waveform is None:
                return None
            waveform = waveform.to(self.device)
            with torch.no_grad():
                output = self.silero_model(waveform)
            text = self.silero_decoder(output[0].cpu()).strip()
            if not text:
                return None
            # Heuristic confidence
            conf = min(1.0, len(text.split()) / 8.0)
            return RecognitionResult(text=text, confidence=conf, engine='silero', processing_time=time.time()-start)
        except Exception as e:
            logger.error(f"Silero error: {e}")
            return None

    def recognize_whisper(self, audio_path: str) -> Optional[RecognitionResult]:
        if not self.whisper_model:
            return None
        start = time.time()
        try:
            result = self.whisper_model.transcribe(audio_path, language='en', fp16=False)
            text = result['text'].strip()
            if not text:
                return None
            conf = 1.0 - result.get('no_speech_prob', 0.0)
            return RecognitionResult(text=text, confidence=conf, engine='whisper', processing_time=time.time()-start)
        except Exception as e:
            logger.error(f"Whisper error: {e}")
            return None

    def recognize(self, audio_path: str, force_whisper: bool = False) -> Optional[RecognitionResult]:
        """Main entry point: try Silero then fallback to Whisper."""
        if not force_whisper and self.silero_model:
            res = self.recognize_silero(audio_path)
            if res and res.confidence >= self.SILERO_CONF_THRESHOLD:
                return res
        if self.whisper_model:
            return self.recognize_whisper(audio_path)
        return None