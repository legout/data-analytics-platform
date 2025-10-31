#!/usr/bin/env bash
set -euo pipefail

TARGET_PORT=${1:-${MARIMO_PORT:-7650}}

COMMAND=(
  jhsingle-native-proxy
  --destport "${TARGET_PORT}"
  --timeout 120
  --progressive
  --port 0
  --cmd
  marimo
  --
  --host 127.0.0.1
  --port "${TARGET_PORT}"
)

exec "${COMMAND[@]}"
