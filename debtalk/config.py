from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import tomllib


CONFIG_DIR = Path.home() / ".config" / "debtalk"
CONFIG_PATH = CONFIG_DIR / "config.toml"


@dataclass(slots=True)
class AppConfig:
    hotkey: str = "<ctrl>+<space>"
    model_size: str = "base"
    language: str | None = None
    compute_type: str = "auto"
    device: str = "auto"
    sample_rate: int = 16000
    block_duration_ms: int = 30
    silence_threshold: int = 700
    silence_seconds: float = 0.75
    min_chunk_seconds: float = 5.0
    max_chunk_seconds: float = 20.0
    clipboard_fallback: bool = True
    notify: bool = True
    typing_interval_ms: int = 4

    @classmethod
    def from_file(cls, path: Path = CONFIG_PATH) -> "AppConfig":
        defaults = cls()
        if not path.exists():
            return defaults
        with path.open("rb") as handle:
            data = tomllib.load(handle)
        app = data.get("app", {})
        audio = data.get("audio", {})
        whisper = data.get("whisper", {})
        output = data.get("output", {})
        return cls(
            hotkey=app.get("hotkey", defaults.hotkey),
            model_size=whisper.get("model_size", defaults.model_size),
            language=whisper.get("language", defaults.language),
            compute_type=whisper.get("compute_type", defaults.compute_type),
            device=whisper.get("device", defaults.device),
            sample_rate=audio.get("sample_rate", defaults.sample_rate),
            block_duration_ms=audio.get("block_duration_ms", defaults.block_duration_ms),
            silence_threshold=audio.get("silence_threshold", defaults.silence_threshold),
            silence_seconds=audio.get("silence_seconds", defaults.silence_seconds),
            min_chunk_seconds=audio.get("min_chunk_seconds", defaults.min_chunk_seconds),
            max_chunk_seconds=audio.get("max_chunk_seconds", defaults.max_chunk_seconds),
            clipboard_fallback=output.get("clipboard_fallback", defaults.clipboard_fallback),
            notify=output.get("notify", defaults.notify),
            typing_interval_ms=output.get("typing_interval_ms", defaults.typing_interval_ms),
        )


def ensure_config() -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(DEFAULT_CONFIG, encoding="utf-8")
    return CONFIG_PATH


DEFAULT_CONFIG = """[app]
hotkey = "<ctrl>+<space>"

[audio]
sample_rate = 16000
block_duration_ms = 30
silence_threshold = 700
silence_seconds = 0.75
min_chunk_seconds = 5.0
max_chunk_seconds = 20.0

[whisper]
model_size = "base"
language = ""
compute_type = "auto"
device = "auto"

[output]
clipboard_fallback = true
notify = true
typing_interval_ms = 4
"""


def normalize_language(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def runtime_environment() -> str:
    session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
    if session_type:
        return session_type
    if os.environ.get("WAYLAND_DISPLAY"):
        return "wayland"
    if os.environ.get("DISPLAY"):
        return "x11"
    return "unknown"
