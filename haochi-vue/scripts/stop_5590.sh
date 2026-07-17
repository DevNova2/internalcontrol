#!/usr/bin/env bash

set -eu

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${1:-5590}"
PID_FILE="$PROJECT_DIR/.runtime/haochi-${PORT}.pid"
WATCHDOG_PID_FILE="$PROJECT_DIR/.runtime/haochi-${PORT}-watchdog.pid"

if [ -f "$WATCHDOG_PID_FILE" ]; then
  WATCHDOG_PID="$(cat "$WATCHDOG_PID_FILE" 2>/dev/null || true)"
  if [ -n "${WATCHDOG_PID:-}" ] && kill -0 "$WATCHDOG_PID" 2>/dev/null; then
    kill "$WATCHDOG_PID" 2>/dev/null || true
    sleep 1
    if kill -0 "$WATCHDOG_PID" 2>/dev/null; then
      kill -9 "$WATCHDOG_PID" 2>/dev/null || true
    fi
  fi
  rm -f "$WATCHDOG_PID_FILE"
fi

if [ -f "$PID_FILE" ]; then
  PID="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [ -n "${PID:-}" ] && kill -0 "$PID" 2>/dev/null; then
    kill "$PID" 2>/dev/null || true
    sleep 1
    if kill -0 "$PID" 2>/dev/null; then
      kill -9 "$PID" 2>/dev/null || true
    fi
  fi
  rm -f "$PID_FILE"
fi

echo "服务已停止"
