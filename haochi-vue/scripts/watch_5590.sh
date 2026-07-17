#!/usr/bin/env bash

set -eu

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${1:-5590}"
RUNTIME_DIR="$PROJECT_DIR/.runtime"
LOG_FILE="$RUNTIME_DIR/haochi-${PORT}.log"
WATCHDOG_PID_FILE="$RUNTIME_DIR/haochi-${PORT}-watchdog.pid"
NODE_BIN="/home/sdq_data_admin/internalcontrol/.local/node-v22.16.0-linux-x64/bin/node"
VITE_BIN="$PROJECT_DIR/node_modules/vite/bin/vite.js"
DIST_DIR="$PROJECT_DIR/dist"

mkdir -p "$RUNTIME_DIR"
echo "$$" > "$WATCHDOG_PID_FILE"

if [ ! -f "$DIST_DIR/index.html" ]; then
  echo "$(date '+%F %T') dist 不存在，watchdog 退出" >> "$LOG_FILE"
  exit 1
fi

if [ ! -x "$NODE_BIN" ] || [ ! -f "$VITE_BIN" ]; then
  echo "$(date '+%F %T') Node 或 Vite 不存在，watchdog 退出" >> "$LOG_FILE"
  exit 1
fi

while true; do
  echo "$(date '+%F %T') starting vite preview on ${PORT}" >> "$LOG_FILE"
  "$NODE_BIN" "$VITE_BIN" preview --host 0.0.0.0 --port "$PORT" --strictPort >>"$LOG_FILE" 2>&1 || true
  echo "$(date '+%F %T') vite preview exited, restart in 2s" >> "$LOG_FILE"
  sleep 2
done
