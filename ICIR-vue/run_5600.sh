#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="/home/sdq_data_admin/internalcontrol/ICIR-vue"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
NODE_BIN="/home/sdq_data_admin/internalcontrol/.local/node-v22.16.0-linux-x64/bin"
BACKEND_SESSION="icir-backend"
FRONTEND_SESSION="icir-frontend"

start_backend() {
  tmux has-session -t "$BACKEND_SESSION" 2>/dev/null && return 0
  tmux new-session -d -s "$BACKEND_SESSION" \
    "cd '$BACKEND_DIR' && HOST=127.0.0.1 PORT=5001 ./.venv/bin/python app.py"
}

start_frontend() {
  tmux has-session -t "$FRONTEND_SESSION" 2>/dev/null && return 0
  tmux new-session -d -s "$FRONTEND_SESSION" \
    "cd '$FRONTEND_DIR' && export PATH='$NODE_BIN':\$PATH && node ./node_modules/vite/bin/vite.js --host 0.0.0.0 --port 5600 --strictPort"
}

stop_backend() {
  tmux kill-session -t "$BACKEND_SESSION" 2>/dev/null || true
}

stop_frontend() {
  tmux kill-session -t "$FRONTEND_SESSION" 2>/dev/null || true
}

status() {
  echo "[tmux]"
  tmux ls 2>/dev/null | grep -E "^($BACKEND_SESSION|$FRONTEND_SESSION):" || true
  echo
  echo "[ports]"
  ss -ltnp | egrep ':(5600|5001)' || true
}

case "${1:-start}" in
  start)
    start_backend
    start_frontend
    sleep 2
    status
    echo
    echo "Open: http://192.168.30.195:5600/"
    ;;
  stop)
    stop_frontend
    stop_backend
    status
    ;;
  restart)
    stop_frontend
    stop_backend
    start_backend
    start_frontend
    sleep 2
    status
    echo
    echo "Open: http://192.168.30.195:5600/"
    ;;
  status)
    status
    ;;
  *)
    echo "Usage: $0 [start|stop|restart|status]"
    exit 1
    ;;
esac
