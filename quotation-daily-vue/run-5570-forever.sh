#!/usr/bin/env bash
set -euo pipefail

LOG_DIR=/home/sdq_data_admin/internalcontrol/quotation-daily-vue
LOG_FILE="$LOG_DIR/quotation-5570.log"

mkdir -p "$LOG_DIR"

while true; do
  echo "[$(date '+%F %T')] starting quotation-daily-vue on :5570" >> "$LOG_FILE"
  /home/sdq_data_admin/internalcontrol/quotation-daily-vue/run-5570.sh >> "$LOG_FILE" 2>&1 || true
  echo "[$(date '+%F %T')] process exited, restarting in 3s" >> "$LOG_FILE"
  sleep 3
done
