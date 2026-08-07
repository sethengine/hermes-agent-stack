#!/bin/bash
# {{SERVICE_NAME}} management script
# Generated from docker-compose-deployment skill template
# Symlink to ~/.local/bin/{{CTL_NAME}} for PATH access

set -e
SERVICE_DIR="$HOME/{{SERVICE_DIR}}"

case "${1:-status}" in
  up|start)
    cd "$SERVICE_DIR"
    docker compose up -d
    echo "Waiting for API..."
    for i in $(seq 1 30); do
      curl -sf http://localhost:{{PORT}}/ > /dev/null 2>&1 && break
      sleep 1
    done
    echo "✓ {{SERVICE_NAME}} running at http://localhost:{{PORT}}"
    ;;
  down|stop)
    cd "$SERVICE_DIR"
    docker compose down
    echo "✓ {{SERVICE_NAME}} stopped"
    ;;
  restart)
    "$0" down && "$0" up
    ;;
  status|ps)
    cd "$SERVICE_DIR"
    docker compose ps -a 2>&1 | grep -vE "(variable is not set|level=warning)"
    echo ""
    curl -sf http://localhost:{{PORT}}/ > /dev/null 2>&1 && echo "✓ API: UP" || echo "✗ API: DOWN"
    ;;
  logs)
    cd "$SERVICE_DIR"
    docker compose logs -f --tail=50 "${2:-api}"
    ;;
  pull)
    cd "$SERVICE_DIR"
    docker compose pull
    echo "✓ Images updated"
    ;;
  env)
    cat "$SERVICE_DIR/.env" | grep -v '^#' | grep -v '^$'
    ;;
  *)
    echo "Usage: {{CTL_NAME}} {up|down|restart|status|logs|pull|env}"
    echo ""
    echo "  up/start    Start {{SERVICE_NAME}}"
    echo "  down/stop   Stop {{SERVICE_NAME}}"
    echo "  restart     Restart {{SERVICE_NAME}}"
    echo "  status/ps   Show container status"
    echo "  logs [svc]  Tail logs (default: api)"
    echo "  pull        Update pre-built images"
    echo "  env         Show current config"
    exit 1
    ;;
esac
