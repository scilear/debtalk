from __future__ import annotations

import logging
import signal
import threading

from pynput import keyboard

from debtalk.audio import AudioChunker
from debtalk.config import AppConfig, runtime_environment
from debtalk.output import OutputDispatcher
from debtalk.transcriber import FasterWhisperTranscriber


LOGGER = logging.getLogger(__name__)


class DebtalkApp:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.output = OutputDispatcher(config)
        self.transcriber = FasterWhisperTranscriber(config, self._handle_text)
        self.audio = AudioChunker(config, self._handle_chunk)
        self._stop_event = threading.Event()
        self._hotkeys = keyboard.GlobalHotKeys({config.hotkey: self.toggle_recording})

    def run(self) -> None:
        LOGGER.info("Starting Debtalk on %s", runtime_environment())
        LOGGER.info("Output capabilities: %s", self.output.capability_summary())
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        self._hotkeys.start()
        self._stop_event.wait()
        self._hotkeys.stop()
        self.audio.stop()

    def toggle_recording(self) -> None:
        if self.audio.recording:
            LOGGER.info("Stopping recording")
            self.audio.stop()
            self.output.notify("Debtalk", "Recording stopped")
            return
        LOGGER.info("Starting recording")
        self.audio.start()
        self.output.notify("Debtalk", "Recording started")

    def _handle_chunk(self, samples, final: bool) -> None:
        self.transcriber.submit(samples, final)

    def _handle_text(self, text: str, final: bool) -> None:
        del final
        self.output.emit(text)

    def _signal_handler(self, signum, frame) -> None:
        del signum, frame
        self._stop_event.set()
