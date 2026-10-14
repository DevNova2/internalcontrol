#!/usr/bin/env bash

set -eu

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${1:-5590}"

"$PROJECT_DIR/scripts/stop_5590.sh" "$PORT" >/dev/null 2>&1 || true
"$PROJECT_DIR/scripts/watch_5590.sh" "$PORT" >/dev/null 2>&1 &
sleep 3

if ss -ltn 2>/dev/null | grep -q ":${PORT}[[:space:]]"; then
  echo "服务启动成功: http://0.0.0.0:${PORT}/"
  echo "日志文件: $PROJECT_DIR/.runtime/haochi-${PORT}.log"
  exit 0
fi

echo "服务暂未拉起，若已安装 cron 守护，将在下一轮自动恢复"
exit 1
