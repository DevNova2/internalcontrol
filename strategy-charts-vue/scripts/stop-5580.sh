#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"
SUPERVISOR_PID_FILE="$RUN_DIR/strategy-charts-vue-5580-supervisor.pid"

stop_pid() {
  local pid="$1"
  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
    sleep 1
    if kill -0 "$pid" 2>/dev/null; then
      kill -9 "$pid" 2>/dev/null || true
    fi
  fi
}

if [[ -f "$SUPERVISOR_PID_FILE" ]]; then
  SUPERVISOR_PID="$(cat "$SUPERVISOR_PID_FILE")"
  stop_pid "$SUPERVISOR_PID"
  rm -f "$SUPERVISOR_PID_FILE"
  echo "已停止 5580 守护进程: $SUPERVISOR_PID"
else
  echo "未找到 5580 守护进程 PID 文件"
fi

pkill -f "busybox httpd -f -p 0.0.0.0:5580" 2>/dev/null || true
