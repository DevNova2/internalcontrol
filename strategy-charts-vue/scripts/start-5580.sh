#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"
PORT="5580"
SUPERVISOR_PID_FILE="$RUN_DIR/strategy-charts-vue-5580-supervisor.pid"
SUPERVISOR_SCRIPT="$ROOT_DIR/scripts/watch-5580.sh"

mkdir -p "$RUN_DIR"

if [[ ! -x "$SUPERVISOR_SCRIPT" ]]; then
  echo "守护脚本不存在或不可执行: $SUPERVISOR_SCRIPT"
  exit 1
fi

if [[ -f "$SUPERVISOR_PID_FILE" ]]; then
  SUPERVISOR_PID="$(cat "$SUPERVISOR_PID_FILE")"
  if kill -0 "$SUPERVISOR_PID" 2>/dev/null; then
    echo "5580 守护进程已在运行，PID: $SUPERVISOR_PID"
    echo "URL: http://192.168.30.195:$PORT/"
    exit 0
  fi
  rm -f "$SUPERVISOR_PID_FILE"
fi

nohup "$SUPERVISOR_SCRIPT" >/dev/null 2>&1 &
SUPERVISOR_PID=$!
echo "$SUPERVISOR_PID" >"$SUPERVISOR_PID_FILE"

sleep 1

if ! kill -0 "$SUPERVISOR_PID" 2>/dev/null; then
  echo "5580 守护进程启动失败"
  rm -f "$SUPERVISOR_PID_FILE"
  exit 1
fi

echo "5580 守护进程已启动"
echo "守护 PID: $SUPERVISOR_PID"
echo "URL: http://192.168.30.195:$PORT/"
