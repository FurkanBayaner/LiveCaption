"""WASAPI loopback audio capture for system-output audio."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from config import ASR_CHUNK_SECONDS, AUDIO_SAMPLE_RATE

DEFAULT_CHANNELS = 1


class AudioCaptureError(RuntimeError):
    """Raised when system-output audio capture cannot continue."""


@dataclass(frozen=True, slots=True)
class AudioChunk:
    """A mono audio chunk normalized for VAD processing."""

    samples: object
    sample_rate: int

    @property
    def duration_seconds(self) -> float:
        """Return the chunk duration in seconds."""
        return len(self.samples) / self.sample_rate


class WasapiLoopbackAudioCapture:
    """Capture computer output audio through pyaudiowpatch WASAPI loopback."""

    def __init__(
        self,
        *,
        sample_rate: int = AUDIO_SAMPLE_RATE,
        chunk_seconds: float = ASR_CHUNK_SECONDS,
        channels: int = DEFAULT_CHANNELS,
        pyaudio_instance: Any | None = None,
    ) -> None:
        if sample_rate <= 0:
            raise ValueError("Audio sample rate must be positive.")
        if chunk_seconds <= 0:
            raise ValueError("Audio chunk duration must be positive.")
        if channels <= 0:
            raise ValueError("Audio channel count must be positive.")

        self._sample_rate = sample_rate
        self._chunk_seconds = chunk_seconds
        self._channels = channels
        self._frames_per_buffer = max(1, round(sample_rate * chunk_seconds))
        self._audio = pyaudio_instance
        self._stream: Any | None = None
        self._owns_audio = pyaudio_instance is None

    @property
    def sample_rate(self) -> int:
        """Return the capture sample rate expected by VAD and Whisper."""
        return self._sample_rate

    @property
    def frames_per_buffer(self) -> int:
        """Return the number of frames read per capture chunk."""
        return self._frames_per_buffer

    def start(self) -> None:
        """Open the WASAPI loopback stream."""
        if self._stream is not None:
            return

        pyaudio = _import_pyaudiowpatch()
        audio = self._audio or pyaudio.PyAudio()
        self._audio = audio
        device = self._find_loopback_device(audio, pyaudio)

        try:
            self._stream = audio.open(
                format=pyaudio.paInt16,
                channels=self._channels,
                rate=self._sample_rate,
                input=True,
                frames_per_buffer=self._frames_per_buffer,
                input_device_index=device["index"],
            )
        except Exception as exc:
            raise AudioCaptureError("Failed to open WASAPI loopback audio stream.") from exc

    def read_chunk(self) -> AudioChunk | None:
        """Read one chunk of system output audio as normalized mono float32 samples."""
        if self._stream is None:
            self.start()

        try:
            raw_data = self._stream.read(self._frames_per_buffer, exception_on_overflow=False)
        except Exception as exc:
            raise AudioCaptureError("Failed to read WASAPI loopback audio chunk.") from exc

        if not raw_data:
            return None

        samples = int16_pcm_to_float32_mono(
            raw_data,
            channels=self._channels,
        )
        return AudioChunk(samples=samples, sample_rate=self._sample_rate)

    def close(self) -> None:
        """Close stream and release pyaudiowpatch resources."""
        stream = self._stream
        self._stream = None
        if stream is not None:
            try:
                if getattr(stream, "is_active", lambda: False)():
                    stream.stop_stream()
                stream.close()
            except Exception as exc:
                raise AudioCaptureError("Failed to close WASAPI loopback stream.") from exc

        if self._owns_audio and self._audio is not None:
            terminate = getattr(self._audio, "terminate", None)
            if callable(terminate):
                terminate()
            self._audio = None

    def _find_loopback_device(self, audio: Any, pyaudio: Any) -> dict[str, Any]:
        try:
            wasapi_info = audio.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_output = audio.get_device_info_by_index(
                wasapi_info["defaultOutputDevice"]
            )
        except Exception as exc:
            raise AudioCaptureError("Failed to inspect WASAPI output devices.") from exc

        if default_output.get("isLoopbackDevice"):
            return default_output

        try:
            loopback_devices = tuple(audio.get_loopback_device_info_generator())
        except Exception as exc:
            raise AudioCaptureError("Failed to enumerate WASAPI loopback devices.") from exc

        default_name = str(default_output.get("name", ""))
        for device in loopback_devices:
            if default_name and default_name in str(device.get("name", "")):
                return device

        if loopback_devices:
            return loopback_devices[0]

        raise AudioCaptureError("No WASAPI loopback audio device was found.")


def int16_pcm_to_float32_mono(raw_data: bytes, *, channels: int) -> object:
    """Convert signed 16-bit PCM bytes to mono float32 samples in [-1.0, 1.0]."""
    if channels <= 0:
        raise ValueError("Audio channel count must be positive.")

    np = _import_numpy()
    samples = np.frombuffer(raw_data, dtype=np.int16)
    if samples.size == 0:
        return np.array([], dtype=np.float32)

    if channels > 1:
        usable = samples.size - (samples.size % channels)
        samples = samples[:usable].reshape(-1, channels).mean(axis=1)

    return (samples.astype(np.float32) / 32768.0).clip(-1.0, 1.0)


def _import_pyaudiowpatch() -> Any:
    try:
        import pyaudiowpatch
    except ImportError as exc:
        raise AudioCaptureError(
            "pyaudiowpatch is not installed. Install project requirements before ASR capture."
        ) from exc
    return pyaudiowpatch


def _import_numpy() -> Any:
    try:
        import numpy as np
    except ImportError as exc:
        raise AudioCaptureError(
            "NumPy is not installed. Install project requirements before ASR capture."
        ) from exc
    return np
