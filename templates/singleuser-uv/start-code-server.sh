#!/usr/bin/env bash
set -euo pipefail

TARGET_PORT=${1:-${CODE_SERVER_PORT:-7600}}
export PASSWORD=${PASSWORD:-"${JUPYTERHUB_USER:-code-user}"}

COMMAND=(
  jhsingle-native-proxy
  --destport "${TARGET_PORT}"
  --timeout 120
  --progressive
  --port 0
  --cmd
  code-server
  --
  --bind-addr 127.0.0.1:"${TARGET_PORT}"
  --auth password
  --disable-telemetry
)

exec "${COMMAND[@]}"
