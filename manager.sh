#!/bin/bash

set -e

case "$1" in
  "start")
    echo "Starting all services..."
    docker-compose up -d
    ;;
  "stop")
    echo "Stopping services..."
    docker-compose down
    ;;
  "restart")
    echo "Restarting services..."
    docker-compose down
    docker-compose up -d
    ;;
  "status")
    echo "Checking service status..."
    docker-compose ps
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status}"
    ;;
esac
