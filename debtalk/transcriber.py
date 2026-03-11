from __future__ import annotations

from dataclasses import dataclass
import logging
import queue
import threading

import numpy as np
from faster_whisper import WhisperModel

from debtalk.config import AppConfig, normalize_language


LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class TranscriptionJob:
    samples: np.ndarray
    final: bool


class FasterWhisperTranscriber:
    def __init__(self, config: AppConfig, on_text) -> None:
        self.config = config
        self.on_text = on_text
        self._queue: queue.Queue[TranscriptionJob] = queue.Queue()
        self._worker = threading.Thread(target=self._run, daemon=True)
        self._model = self._build_model()
        self._worker.start()

    def submit(self, samples: np.ndarray, final: bool) -> None:
        self._queue.put(TranscriptionJob(samples=samples, final=final))

    def _build_model(self) -> WhisperModel:
        compute_type = self.config.compute_type
        device = self.config.device
        if device == "auto":
            device = "cuda"
        try:
            return WhisperModel(
                self.config.model_size,
                device=device,
                compute_type=compute_type,
            )
        except Exception:
            LOGGER.exception("Falling back to CPU inference")
            return WhisperModel(
                self.config.model_size,
                device="cpu",
                compute_type="int8",
            )

    def _run(self) -> None:
        language = normalize_language(self.config.language)
        while True:
            job = self._queue.get()
            if len(job.samples) == 0:
                continue
            try:
                segments, _ = self._model.transcribe(
                    job.samples,
                    language=language,
                    vad_filter=True,
                    condition_on_previous_text=False,
                    beam_size=1,
                )
                text = " ".join(segment.text.strip() for segment in segments).strip()
            except Exception:
                LOGGER.exception("Transcription failed")
                continue
            if text:
                self.on_text(text, job.final)
