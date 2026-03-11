from __future__ import annotations

import argparse
import logging
from pathlib import Path

from debtalk.app import DebtalkApp
from debtalk.config import AppConfig, CONFIG_PATH, ensure_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Global hotkey speech-to-text tool for Linux")
    parser.add_argument("--config", default=str(CONFIG_PATH), help="Path to config.toml")
    parser.add_argument("--print-config-path", action="store_true", help="Print the default config path and exit")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    if args.print_config_path:
        print(ensure_config())
        return 0
    ensure_config()
    config = AppConfig.from_file(Path(args.config))
    DebtalkApp(config).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
