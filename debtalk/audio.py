from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from queue import Queue
import threading
import time

import numpy as np
import sounddevice as sd

from debtalk.config import AppConfig


ChunkCallback = Callable[[np.ndarray, bool], None]


@dataclass(slots=True)
class AudioChunk:
    samples: np.ndarray
    final: bool


class AudioChunker:
    def __init__(self, config: AppConfig, on_chunk: ChunkCallback) -> None:
        self.config = config
        self.on_chunk = on_chunk
        self._stream: sd.InputStream | None = None
        self._frames: list[np.ndarray] = []
        self._buffered_samples = 0
        self._lock = threading.Lock()
        self._recording = False
        self._last_voice_time = 0.0
        self._chunk_start_time = 0.0
        self._queue: Queue[np.ndarray | None] = Queue()
        self._worker = threading.Thread(target=self._process_loop, daemon=True)
        self._worker.start()

    @property
    def recording(self) -> bool:
        with self._lock:
            return self._recording

    def start(self) -> None:
        with self._lock:
            if self._recording:
                return
            self._frames = []
            self._buffered_samples = 0
            self._recording = True
            now = time.monotonic()
            self._last_voice_time = now
            self._chunk_start_time = now
        blocksize = int(self.config.sample_rate * self.config.block_duration_ms / 1000)
        self._stream = sd.InputStream(
            samplerate=self.config.sample_rate,
            channels=1,
            dtype="int16",
            blocksize=blocksize,
            callback=self._audio_callback,
        )
        self._stream.start()

    def stop(self) -> None:
        with self._lock:
            if not self._recording:
                return
            self._recording = False
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        self._queue.put(None)

    def _audio_callback(self, indata: np.ndarray, frames: int, audio_time, status) -> None:
        del frames, audio_time
        if status:
            return
        self._queue.put(indata.copy().reshape(-1))

    def _process_loop(self) -> None:
        silence_window = self.config.silence_seconds
        min_samples = int(self.config.min_chunk_seconds * self.config.sample_rate)
        max_samples = int(self.config.max_chunk_seconds * self.config.sample_rate)
        while True:
            chunk = self._queue.get()
            if chunk is None:
                self._flush(final=True)
                continue
            now = time.monotonic()
            amplitude = int(np.abs(chunk.astype(np.int32)).mean())
            with self._lock:
                if not self._recording:
                    continue
                self._frames.append(chunk)
                self._buffered_samples += len(chunk)
                if amplitude >= self.config.silence_threshold:
                    self._last_voice_time = now
                buffered_samples = self._buffered_samples
                silence_elapsed = now - self._last_voice_time
            if buffered_samples >= max_samples:
                self._flush(final=False)
                continue
            if buffered_samples >= min_samples and silence_elapsed >= silence_window:
                self._flush(final=False)

    def _flush(self, final: bool) -> None:
        with self._lock:
            if not self._frames:
                return
            frames = self._frames
            self._frames = []
            self._buffered_samples = 0
            self._chunk_start_time = time.monotonic()
            self._last_voice_time = self._chunk_start_time
        samples = np.concatenate(frames).astype(np.float32) / 32768.0
        self.on_chunk(samples, final)
