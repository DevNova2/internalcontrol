#!/usr/bin/env bash
set -euo pipefail

cd /home/sdq_data_admin/internalcontrol/quotation-daily-vue

export QUOTATION_HOST=0.0.0.0
export QUOTATION_PORT=5570

exec /usr/bin/python3 /home/sdq_data_admin/internalcontrol/quotation-daily-vue/server.py
