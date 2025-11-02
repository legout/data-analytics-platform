#!/usr/bin/env bash
# Source this in shells or proxy launchers to activate the currently selected uv venv.
set -euo pipefail

VENVS_DIR="${HOME}/.uv/venvs"
CURRENT_FILE="${HOME}/.uv/.current-venv"

mkdir -p "${VENVS_DIR}"

ensure_default() {
  # If no current venv is set, ensure a 'base' exists and select it
  if [[ ! -f "$CURRENT_FILE" ]]; then
    if [[ ! -d "${VENVS_DIR}/base" ]]; then
      uv venv "${VENVS_DIR}/base"
    fi
    echo "${VENVS_DIR}/base" > "$CURRENT_FILE"
  fi
}

ensure_default

if [[ -f "$CURRENT_FILE" ]]; then
  VENV_PATH=$(cat "$CURRENT_FILE")
  if [[ -d "$VENV_PATH" && -f "$VENV_PATH/bin/activate" ]]; then
    # shellcheck disable=SC1090
    source "$VENV_PATH/bin/activate"
    export UV_ACTIVE_VENV="$VENV_PATH"
  fi
fi
