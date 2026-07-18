"""
STT Manager using OpenAI Whisper for offline speech-to-text.

Bypasses Whisper's built-in load_audio (which requires ffmpeg) by
reading WAV files with Python's built-in `wave` module and resampling
with numpy. This makes STT work on any system without ffmpeg installed.
"""
import os
import io
import wave
import struct
import tempfile
import numpy as np
from pathlib import Path
from backend.model_config import STT_WHISPER_MODEL_SIZE

# Whisper's expected sample rate
WHISPER_SR = 16000


class WhisperSTTManager:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.model_size = STT_WHISPER_MODEL_SIZE  # Options: tiny, base, small, medium, large

    def load_model(self):
        """Load Whisper model (lazy loading)"""
        if self._model is None:
            import whisper
            print(f"🎤 Loading Whisper {self.model_size} model...")
            self._model = whisper.load_model(self.model_size)
            print(f"✅ Whisper model loaded successfully")
        return self._model

    @staticmethod
    def _read_wav_to_float32(wav_bytes: bytes) -> tuple:
        """
        Read WAV bytes into a float32 numpy array using only the
        built-in `wave` module (no ffmpeg needed).

        Returns:
            (samples: np.ndarray[float32], sample_rate: int)
        """
        with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
            n_channels = wf.getnchannels()
            sample_width = wf.getsampwidth()  # bytes per sample
            sample_rate = wf.getframerate()
            n_frames = wf.getnframes()
            raw = wf.readframes(n_frames)

        # Convert raw bytes to numpy array based on sample width
        if sample_width == 2:   # 16-bit PCM (most common from browser)
            dtype = np.int16
            max_val = 32768.0
        elif sample_width == 4:  # 32-bit PCM
            dtype = np.int32
            max_val = 2147483648.0
        elif sample_width == 1:  # 8-bit PCM (unsigned)
            samples = np.frombuffer(raw, dtype=np.uint8).astype(np.float32)
            samples = (samples - 128.0) / 128.0
            if n_channels > 1:
                samples = samples.reshape(-1, n_channels).mean(axis=1)
            return samples, sample_rate
        else:
            raise ValueError(f"Unsupported sample width: {sample_width}")

        samples = np.frombuffer(raw, dtype=dtype).astype(np.float32)
        samples /= max_val

        # Convert stereo to mono by averaging channels
        if n_channels > 1:
            samples = samples.reshape(-1, n_channels).mean(axis=1)

        return samples, sample_rate

    @staticmethod
    def _resample(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """
        Resample audio using numpy linear interpolation.
        No scipy/librosa/ffmpeg needed.
        """
        if orig_sr == target_sr:
            return audio

        duration = len(audio) / orig_sr
        target_length = int(duration * target_sr)
        resampled = np.interp(
            np.linspace(0, len(audio), target_length, endpoint=False),
            np.arange(len(audio)),
            audio,
        ).astype(np.float32)
        return resampled

    def transcribe_audio(self, audio_file_path: str, language: str = "en") -> dict:
        """
        Transcribe audio file to text using Whisper.
        Reads the WAV file manually to avoid requiring ffmpeg.

        Args:
            audio_file_path: Path to audio file (WAV only)
            language: Language code (default: "en" for English)

        Returns:
            dict with 'text' and 'language' keys
        """
        try:
            model = self.load_model()

            # Read WAV and convert to float32 numpy (bypasses ffmpeg)
            with open(audio_file_path, "rb") as f:
                wav_bytes = f.read()

            samples, orig_sr = self._read_wav_to_float32(wav_bytes)

            # Resample to Whisper's required 16 kHz
            audio_16k = self._resample(samples, orig_sr, WHISPER_SR)

            # Transcribe from numpy array (Whisper skips load_audio for arrays)
            result = model.transcribe(
                audio_16k,
                language=language if language != "auto" else None,
                fp16=False,  # Use FP32 for CPU compatibility
            )

            return {
                "text": result["text"].strip(),
                "language": result.get("language", language),
            }

        except Exception as e:
            print(f"❌ Whisper transcription error: {e}")
            raise

    def transcribe_audio_bytes(self, audio_bytes: bytes, language: str = "en") -> dict:
        """
        Transcribe audio from bytes (WAV format).
        Reads directly from bytes — no temp file needed for the audio
        conversion, but we still use one for compatibility.

        Args:
            audio_bytes: Audio data as bytes (WAV format)
            language: Language code (default: "en" for English)

        Returns:
            dict with 'text' and 'language' keys
        """
        try:
            model = self.load_model()

            # Read WAV bytes into float32 numpy array (no ffmpeg!)
            samples, orig_sr = self._read_wav_to_float32(audio_bytes)

            # Resample to 16 kHz for Whisper
            audio_16k = self._resample(samples, orig_sr, WHISPER_SR)

            # Transcribe from numpy array directly
            result = model.transcribe(
                audio_16k,
                language=language if language != "auto" else None,
                fp16=False,
            )

            return {
                "text": result["text"].strip(),
                "language": result.get("language", language),
            }

        except Exception as e:
            print(f"❌ Whisper transcription error: {e}")
            raise


# Singleton instance
def get_stt_manager() -> WhisperSTTManager:
    """Get the singleton STT manager instance"""
    return WhisperSTTManager()
