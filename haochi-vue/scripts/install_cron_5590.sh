#!/usr/bin/env bash

set -eu

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${1:-5590}"
RUNTIME_DIR="$PROJECT_DIR/.runtime"
CRON_FILE="$RUNTIME_DIR/crontab-${PORT}.tmp"
ENSURE_SCRIPT="$PROJECT_DIR/scripts/ensure_5590.sh"

mkdir -p "$RUNTIME_DIR"

CURRENT_CRON="$(crontab -l 2>/dev/null || true)"
FILTERED_CRON="$(printf '%s\n' "$CURRENT_CRON" | grep -v "$ENSURE_SCRIPT $PORT" || true)"

{
  printf '%s\n' "$FILTERED_CRON"
  echo "@reboot $ENSURE_SCRIPT $PORT >/dev/null 2>&1"
  echo "* * * * * $ENSURE_SCRIPT $PORT >/dev/null 2>&1"
} > "$CRON_FILE"

crontab "$CRON_FILE"
rm -f "$CRON_FILE"

echo "cron 守护已安装"
echo "开机启动 + 每分钟巡检端口 $PORT"
