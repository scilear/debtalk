#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
SERVICE_SRC="$PROJECT_DIR/deploy/debtalk.service"
SERVICE_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
SERVICE_DEST="$SERVICE_DIR/debtalk.service"

APT_PACKAGES=(
  build-essential
  portaudio19-dev
  libasound2-dev
  ffmpeg
  python3-dev
  python3-venv
  xdotool
  xclip
  libxcb-xinerama0
)

WAYLAND_PACKAGES=(
  wtype
  wl-clipboard
  ydotool
)

log() {
  printf '[debtalk] %s\n' "$1"
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1
}

install_apt_packages() {
  local packages=("${APT_PACKAGES[@]}")
  if [[ "${1:-}" == "wayland" ]]; then
    packages+=("${WAYLAND_PACKAGES[@]}")
  fi
  if ! need_cmd apt-get; then
    log "apt-get not found; install these packages manually: ${packages[*]}"
    return
  fi
  log "Installing system packages with apt"
  sudo apt-get update
  sudo apt-get install -y "${packages[@]}"
}

create_venv() {
  if [[ ! -d "$VENV_DIR" ]]; then
    log "Creating virtual environment at $VENV_DIR"
    python3 -m venv "$VENV_DIR"
  fi
  log "Installing Python package into virtual environment"
  "$VENV_DIR/bin/pip" install --upgrade pip
  "$VENV_DIR/bin/pip" install -e "$PROJECT_DIR"
}

install_service() {
  mkdir -p "$SERVICE_DIR"
  sed "s#%h/Documents/Debtalk#$PROJECT_DIR#g" "$SERVICE_SRC" > "$SERVICE_DEST"
  log "Reloading user systemd units"
  systemctl --user daemon-reload
  log "Enabling and starting debtalk.service"
  systemctl --user enable --now debtalk.service
}

show_summary() {
  local config_path
  config_path="$("$VENV_DIR/bin/python" -m debtalk.main --print-config-path)"
  log "Install complete"
  log "Service: systemctl --user status debtalk.service"
  log "Logs: journalctl --user -u debtalk.service -f"
  log "Config: $config_path"
}

main() {
  local session_type="${XDG_SESSION_TYPE:-x11}"
  log "Detected session type: $session_type"
  install_apt_packages "$session_type"
  create_venv
  install_service
  show_summary
}

main "$@"
