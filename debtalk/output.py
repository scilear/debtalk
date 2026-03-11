from __future__ import annotations

import logging
import shlex
import shutil
import subprocess

from debtalk.config import AppConfig, runtime_environment


LOGGER = logging.getLogger(__name__)


class OutputDispatcher:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.environment = runtime_environment()

    def emit(self, text: str) -> None:
        if self._type_text(text):
            self.notify("Debtalk", text)
            return
        if self.config.clipboard_fallback and self._copy_clipboard(text):
            self.notify("Debtalk copied to clipboard", text)
            return
        self.notify("Debtalk could not inject text", text)

    def _type_text(self, text: str) -> bool:
        if self.environment == "x11" and shutil.which("xdotool"):
            delay = str(max(self.config.typing_interval_ms, 0))
            command = ["xdotool", "type", "--clearmodifiers", "--delay", delay, text]
            return self._run(command)
        if self.environment == "wayland":
            if shutil.which("wtype"):
                return self._run(["wtype", text])
            if shutil.which("ydotool"):
                return self._run(["ydotool", "type", text])
        return False

    def _copy_clipboard(self, text: str) -> bool:
        if self.environment == "wayland" and shutil.which("wl-copy"):
            return self._run(["wl-copy"], stdin=text)
        if self.environment == "x11" and shutil.which("xclip"):
            return self._run(["xclip", "-selection", "clipboard"], stdin=text)
        if shutil.which("xsel"):
            return self._run(["xsel", "--clipboard", "--input"], stdin=text)
        return False

    def notify(self, title: str, body: str) -> None:
        if not self.config.notify or not shutil.which("notify-send"):
            return
        clipped = body if len(body) <= 160 else f"{body[:157]}..."
        self._run(["notify-send", title, clipped])

    def _run(self, command: list[str], stdin: str | None = None) -> bool:
        try:
            subprocess.run(
                command,
                input=stdin,
                text=True,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            LOGGER.warning("Command failed: %s", shlex.join(command))
            return False

    def capability_summary(self) -> str:
        parts = [f"session={self.environment}"]
        parts.append(f"xdotool={bool(shutil.which('xdotool'))}")
        parts.append(f"wtype={bool(shutil.which('wtype'))}")
        parts.append(f"ydotool={bool(shutil.which('ydotool'))}")
        parts.append(f"clipboard={bool(shutil.which('wl-copy') or shutil.which('xclip') or shutil.which('xsel'))}")
        return ", ".join(parts)
