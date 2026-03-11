# Repository Guidelines

## Project Structure & Module Organization

Core application code lives in [`debtalk/`](/home/fabien/Documents/Debtalk/debtalk), with the main entry point in `debtalk/main.py`. Runtime components are split by concern: `app.py` for orchestration, `audio.py` for microphone capture and chunking, `transcriber.py` for `faster-whisper`, `output.py` for text injection and clipboard fallback, and `config.py` for TOML-based settings. Deployment assets live in [`deploy/`](/home/fabien/Documents/Debtalk/deploy), and [`install.sh`](/home/fabien/Documents/Debtalk/install.sh) bootstraps dependencies and the user service.

## Build, Test, and Development Commands

- `bash install.sh`: installs apt dependencies, creates `.venv`, installs the package, and enables the user service.
- `source .venv/bin/activate && pip install -e .`: editable local install without re-running the full bootstrap.
- `python -m debtalk.main --print-config-path`: creates the default config if missing and prints its location.
- `python -m compileall debtalk`: quick syntax verification across the package.
- `systemctl --user status debtalk.service`: checks whether the background service is active.

## Coding Style & Naming Conventions

Use Python 3.11+ with 4-space indentation and type hints for new code. Keep modules focused on one responsibility and prefer small classes or functions over monolithic scripts. Follow existing naming patterns: `snake_case` for functions, variables, and modules; `PascalCase` for classes; uppercase for module-level constants. Keep shell scripts POSIX-friendly where practical and fail fast with `set -euo pipefail`.

## Testing Guidelines

There is no formal test suite yet. For now, treat `python -m compileall debtalk` as the minimum gate and manually verify hotkey capture, transcription, and text insertion on the target desktop session. When adding tests, place them under `tests/`, name files `test_*.py`, and prefer `pytest` for unit coverage around chunking, config parsing, and output fallback behavior.

## Commit & Pull Request Guidelines

This workspace does not currently include Git history, so no repository-specific commit convention can be inferred. Use short, imperative commit subjects such as `Add clipboard fallback notification`. Pull requests should include a concise description, any setup or system-package changes, manual test notes, and screenshots or terminal logs when UI or service behavior changes.

## Security & Configuration Tips

Do not commit personal config files, model caches, or service overrides from `~/.config/debtalk` or `~/.config/systemd/user`. Document any new external command dependencies in both [`README.md`](/home/fabien/Documents/Debtalk/README.md) and [`install.sh`](/home/fabien/Documents/Debtalk/install.sh).
