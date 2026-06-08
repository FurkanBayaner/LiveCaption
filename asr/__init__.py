"""ASR capture and speech-gating adapters."""

from asr.audio_capture import AudioCaptureError, AudioChunk, WasapiLoopbackAudioCapture
from asr.audio_pipeline import ASRAudioPipeline
from asr.speech_buffer import SpeechSegment, SpeechSegmentBuffer
from asr.vad_engine import SileroVADEngine, VADEngineError

__all__ = [
    "ASRAudioPipeline",
    "AudioCaptureError",
    "AudioChunk",
    "SileroVADEngine",
    "SpeechSegment",
    "SpeechSegmentBuffer",
    "VADEngineError",
    "WasapiLoopbackAudioCapture",
]
