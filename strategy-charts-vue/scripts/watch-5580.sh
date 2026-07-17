#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"
DIST_DIR="$ROOT_DIR/dist"
PORT="5580"
CONFIG_FILE="$ROOT_DIR/scripts/httpd.conf"
LOG_FILE="$RUN_DIR/strategy-charts-vue-5580.log"

mkdir -p "$RUN_DIR"

if [[ ! -d "$DIST_DIR" ]]; then
  echo "dist 目录不存在，请先执行构建" >>"$LOG_FILE"
  exit 1
fi

while true; do
  printf '[%s] starting busybox httpd on port %s\n' "$(date '+%F %T')" "$PORT" >>"$LOG_FILE"
  busybox httpd -f -p "0.0.0.0:$PORT" -h "$DIST_DIR" -c "$CONFIG_FILE" >>"$LOG_FILE" 2>&1 || true
  printf '[%s] busybox httpd exited, restart in 1s\n' "$(date '+%F %T')" >>"$LOG_FILE"
  sleep 1
done
