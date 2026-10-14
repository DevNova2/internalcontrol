#!/usr/bin/env bash

set -eu

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${1:-5590}"
LOG_FILE="$PROJECT_DIR/.runtime/haochi-${PORT}.log"
WATCHDOG_PID_FILE="$PROJECT_DIR/.runtime/haochi-${PORT}-watchdog.pid"

if ss -ltn 2>/dev/null | grep -q ":${PORT}[[:space:]]"; then
  echo "服务运行中: http://0.0.0.0:${PORT}/"
  if [ -f "$WATCHDOG_PID_FILE" ]; then
    WATCHDOG_PID="$(cat "$WATCHDOG_PID_FILE" 2>/dev/null || true)"
    if [ -n "${WATCHDOG_PID:-}" ] && kill -0 "$WATCHDOG_PID" 2>/dev/null; then
      echo "watchdog PID: $WATCHDOG_PID"
    fi
  fi
  echo "日志文件: $LOG_FILE"
  exit 0
fi

echo "服务未运行"
exit 1
