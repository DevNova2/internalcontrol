#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/home/sdq_data_admin/internalcontrol"
LOG_DIR="$BASE_DIR/logs/vue-pages"
export TRADE_DATA_ROOT="/mnt/trade_data"

REQUIRED_MOUNT_PATHS=(
  "/mnt/trade_data/data"
  "/mnt/trade_data/turnover"
  "/mnt/trade_data/order"
)

PORTS=(5560 5570 5580 5590 5600)

declare -A PROJECT_DIRS=(
  [5560]="$BASE_DIR/vue-internal-control"
  [5570]="$BASE_DIR/quotation-daily-vue"
  [5580]="$BASE_DIR/strategy-charts-vue"
  [5590]="$BASE_DIR/haochi-vue"
  [5600]="$BASE_DIR/ICIR-vue/frontend"
)

declare -A PROJECT_TYPES=(
  [5560]="vite"
  [5570]="python"
  [5580]="vite"
  [5590]="vite"
  [5600]="vite"
)

declare -A START_COMMANDS

fail() {
  echo "[ERROR] $*" >&2
  exit 1
}

info() {
  echo "[INFO] $*"
}

find_port_pids() {
  local port="$1"

  python3 - "$port" <<'PY'
import os
import socket
import sys

port = int(sys.argv[1])
inodes = set()

def collect_inodes(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            next(handle, None)
            for line in handle:
                parts = line.split()
                if len(parts) < 10:
                    continue
                local_address = parts[1]
                state = parts[3]
                inode = parts[9]
                _, port_hex = local_address.rsplit(":", 1)
                if state == "0A" and int(port_hex, 16) == port:
                    inodes.add(inode)
    except FileNotFoundError:
        return

collect_inodes("/proc/net/tcp")
collect_inodes("/proc/net/tcp6")

if not inodes:
    raise SystemExit(0)

pids = set()
for pid in os.listdir("/proc"):
    if not pid.isdigit():
        continue
    fd_dir = f"/proc/{pid}/fd"
    try:
        for fd in os.listdir(fd_dir):
            try:
                target = os.readlink(f"{fd_dir}/{fd}")
            except OSError:
                continue
            if target.startswith("socket:[") and target[8:-1] in inodes:
                pids.add(int(pid))
                break
    except OSError:
        continue

for pid in sorted(pids):
    print(pid)
PY
}

resolve_node_bin() {
  local project_dir="$1"
  local candidates=()

  shopt -s nullglob
  candidates+=("$project_dir"/node-v*/bin/node)
  candidates+=("$project_dir"/.local-node/node-v*/bin/node)
  candidates+=("$project_dir"/.local-node/*/bin/node)
  candidates+=("$BASE_DIR"/.local/node-v*/bin/node)
  candidates+=("$BASE_DIR"/.local/*/bin/node)
  shopt -u nullglob

  for candidate in "${candidates[@]}"; do
    if [[ -x "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  if command -v node >/dev/null 2>&1; then
    command -v node
    return 0
  fi

  return 1
}

kill_port() {
  local port="$1"
  local pids=""

  pids="$(find_port_pids "$port" || true)"

  if [[ -n "$pids" ]]; then
    info "Killing processes on port $port: $pids"
    kill $pids 2>/dev/null || true
    sleep 2
    if [[ -n "$(find_port_pids "$port" || true)" ]]; then
      kill -9 $pids 2>/dev/null || true
    fi
  fi
}

start_vite_project() {
  local port="$1"
  local project_dir="$2"
  local log_file="$3"
  local node_bin=""
  local vite_entry=""
  local command_string=""

  node_bin="$(resolve_node_bin "$project_dir")" || fail "No node executable found for $project_dir"

  if [[ -f "$project_dir/node_modules/vite/bin/vite.js" ]]; then
    vite_entry="$project_dir/node_modules/vite/bin/vite.js"
  elif [[ -x "$project_dir/node_modules/.bin/vite" ]]; then
    vite_entry="$project_dir/node_modules/.bin/vite"
  else
    fail "No local vite executable found for $project_dir"
  fi

  command_string="TRADE_DATA_ROOT=$TRADE_DATA_ROOT \"$node_bin\" \"$vite_entry\" --host 0.0.0.0 --port $port --strictPort"
  START_COMMANDS["$port"]="$command_string"

  (
    cd "$project_dir"
    nohup env TRADE_DATA_ROOT="$TRADE_DATA_ROOT" "$node_bin" "$vite_entry" --host 0.0.0.0 --port "$port" --strictPort >"$log_file" 2>&1 &
  )
}

start_python_project() {
  local port="$1"
  local project_dir="$2"
  local log_file="$3"
  local command_string=""

  command_string="TRADE_DATA_ROOT=$TRADE_DATA_ROOT QUOTATION_HOST=0.0.0.0 QUOTATION_PORT=$port python3 server.py"
  START_COMMANDS["$port"]="$command_string"

  (
    cd "$project_dir"
    nohup env TRADE_DATA_ROOT="$TRADE_DATA_ROOT" QUOTATION_HOST="0.0.0.0" QUOTATION_PORT="$port" python3 server.py >"$log_file" 2>&1 &
  )
}

wait_for_port() {
  local port="$1"
  local attempt=0

  while (( attempt < 30 )); do
    if python3 - "$port" <<'PY'
import socket
import sys

port = int(sys.argv[1])
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(0.5)
try:
    raise SystemExit(0 if sock.connect_ex(("127.0.0.1", port)) == 0 else 1)
finally:
    sock.close()
PY
    then
      return 0
    fi
    attempt=$((attempt + 1))
    sleep 1
  done

  return 1
}

port_state() {
  local port="$1"

  if python3 - "$port" <<'PY'
import socket
import sys

port = int(sys.argv[1])
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(0.5)
try:
    raise SystemExit(0 if sock.connect_ex(("127.0.0.1", port)) == 0 else 1)
finally:
    sock.close()
PY
  then
    printf '%s\n' "LISTEN"
  else
    printf '%s\n' "not-listening"
  fi
}

curl_status() {
  local port="$1"
  local url="http://127.0.0.1:$port/"
  local attempt=0
  local status="000"

  while (( attempt < 30 )); do
    status="$(curl -sS -o /dev/null -w '%{http_code}' "$url" || true)"
    if [[ "$status" == "200" ]]; then
      printf '%s\n' "$status"
      return 0
    fi
    attempt=$((attempt + 1))
    sleep 1
  done

  printf '%s\n' "$status"
  return 1
}

mkdir -p "$LOG_DIR"

for required_path in "${REQUIRED_MOUNT_PATHS[@]}"; do
  [[ -d "$required_path" ]] || fail "Trade data path missing: $required_path"
done

info "TRADE_DATA_ROOT=$TRADE_DATA_ROOT"
info "Mount check passed"

for port in "${PORTS[@]}"; do
  kill_port "$port"
done

for port in "${PORTS[@]}"; do
  project_dir="${PROJECT_DIRS[$port]}"
  project_type="${PROJECT_TYPES[$port]}"
  log_file="$LOG_DIR/$port.log"

  [[ -d "$project_dir" ]] || fail "Project directory not found: $project_dir"
  : >"$log_file"

  info "Starting port $port from $project_dir"
  if [[ "$project_type" == "vite" ]]; then
    start_vite_project "$port" "$project_dir" "$log_file"
  else
    start_python_project "$port" "$project_dir" "$log_file"
  fi
done

declare -A CURL_RESULTS

for port in "${PORTS[@]}"; do
  if wait_for_port "$port"; then
    info "Port $port is listening"
  else
    info "Port $port did not enter listening state in time"
  fi

  CURL_RESULTS["$port"]="$(curl_status "$port" || true)"
done

echo
echo "===== Vue Pages Status ====="
for port in "${PORTS[@]}"; do
  log_file="$LOG_DIR/$port.log"
  listen_state="$(port_state "$port")"

  echo "port=$port"
  echo "listen=$listen_state"
  echo "command=${START_COMMANDS[$port]}"
  echo "curl=${CURL_RESULTS[$port]}"
  echo "log=$log_file"
  echo
done

echo "===== Access URLs ====="
for port in "${PORTS[@]}"; do
  echo "http://192.168.30.195:$port/"
done
