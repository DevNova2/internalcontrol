#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"
PORT="5580"
SUPERVISOR_PID_FILE="$RUN_DIR/strategy-charts-vue-5580-supervisor.pid"

if [[ -f "$SUPERVISOR_PID_FILE" ]]; then
  SUPERVISOR_PID="$(cat "$SUPERVISOR_PID_FILE")"
  if kill -0 "$SUPERVISOR_PID" 2>/dev/null; then
    echo "5580 守护进程运行中，PID: $SUPERVISOR_PID"
  else
    echo "5580 守护进程 PID 文件存在，但进程已退出"
  fi
else
  echo "未找到 5580 守护进程 PID 文件"
fi

echo "检查 5580 监听状态"
ss -ltnp | grep ":$PORT" || true

echo "检查 5580 响应状态"
curl -I --max-time 3 "http://127.0.0.1:$PORT" | head -n 5
