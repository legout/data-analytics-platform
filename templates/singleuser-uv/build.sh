#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME=${1:-local/custom-singleuser}
DOCKERFILE=${DOCKERFILE:-Dockerfile}

docker build \
  -t "$IMAGE_NAME" \
  -f "$DOCKERFILE" \
  --build-arg UV_VERSION=${UV_VERSION:-latest} \
  .
