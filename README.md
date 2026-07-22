# Internal Control 项目服务器运维说明

本文档用于管理远程服务器 `sdqdata01` 上的内控网页项目，包含端口对应关系、启动、停止、重启、状态检查和日志查看命令。

## 基本信息

```text
服务器地址：192.168.30.195
项目根目录：/home/sdq_data_admin/internalcontrol
实时数据目录：/mnt/trade_data
统一日志目录：/home/sdq_data_admin/internalcontrol/logs/vue-pages
```

## 端口与项目对应关系

| 端口 | 项目目录 | 运行方式 | 访问地址 |
| --- | --- | --- | --- |
| 5560 | `vue-internal-control` | Vite + 实时数据 API | `http://192.168.30.195:5560/` |
| 5570 | `quotation-daily-vue` | Python | `http://192.168.30.195:5570/` |
| 5580 | `strategy-charts-vue` | 静态页面/守护脚本 | `http://192.168.30.195:5580/` |
| 5590 | `haochi-vue` | Vite Preview/守护脚本 | `http://192.168.30.195:5590/` |
| 5600 | `ICIR-vue` | Python 后端 + Vite 前端 | `http://192.168.30.195:5600/` |

## 拉取 GitHub 最新代码

```bash
cd ~/internalcontrol
git fetch origin main
git merge --ff-only origin/main
git status --short --branch
```

也可以直接执行：

```bash
cd ~/internalcontrol
git pull --ff-only origin main
```

## 一键重启全部项目

这是日常最推荐使用的命令：

```bash
cd ~/internalcontrol
bash restart_vue_pages.sh
```

该脚本会：

1. 检查 `/mnt/trade_data/data`、`turnover` 和 `order` 是否存在。
2. 停止 5560、5570、5580、5590、5600 端口的旧进程。
3. 重新启动五个项目。
4. 输出端口监听状态、HTTP 状态和日志位置。

> 注意：统一脚本与各项目独立脚本使用的进程管理方式不完全相同。日常建议始终使用统一脚本管理全部端口，避免与独立 watchdog、tmux 或 systemd 启动方式混用。只有明确需要单独管理某个项目时，才使用下面的单项目命令。

## 单独管理 5560

### 重启

```bash
cd ~/internalcontrol/vue-internal-control
fuser -k 5560/tcp 2>/dev/null || true
mkdir -p ~/internalcontrol/logs/vue-pages

nohup env TRADE_DATA_ROOT=/mnt/trade_data \
  ~/internalcontrol/.local/node-v22.16.0-linux-x64/bin/node \
  ./node_modules/vite/bin/vite.js \
  --host 0.0.0.0 --port 5560 --strictPort \
  > ~/internalcontrol/logs/vue-pages/5560.log 2>&1 &
```

### 检查状态和日志

```bash
curl -I --max-time 3 http://127.0.0.1:5560/
tail -n 50 ~/internalcontrol/logs/vue-pages/5560.log
```

5560 使用 Vite 监听源码变化。执行 `git pull` 修改前端源码后通常不需要重启服务，但大屏浏览器应手动刷新一次以确保加载新代码。

## 单独管理 5570

如果已经安装 `quotation-daily-5570.service`：

```bash
sudo systemctl restart quotation-daily-5570.service
sudo systemctl status quotation-daily-5570.service --no-pager
```

查看日志：

```bash
sudo journalctl -u quotation-daily-5570.service -n 50 --no-pager
```

如果提示 `Unit quotation-daily-5570.service not found`，使用统一脚本启动：

```bash
cd ~/internalcontrol
bash restart_vue_pages.sh
```

## 单独管理 5580

### 重启和检查状态

```bash
cd ~/internalcontrol/strategy-charts-vue
bash scripts/restart-5580.sh
bash scripts/status-5580.sh
```

### 查看日志

```bash
tail -n 50 ~/internalcontrol/strategy-charts-vue/.run/strategy-charts-vue-5580.log
```

如果修改了 5580 的前端源码，重启前先重新构建：

```bash
cd ~/internalcontrol/strategy-charts-vue
npm run build
bash scripts/restart-5580.sh
```

## 单独管理 5590

`start_5590.sh` 会先停止旧进程，因此也可以作为重启命令使用。

### 重启和检查状态

```bash
cd ~/internalcontrol/haochi-vue
bash scripts/start_5590.sh
bash scripts/status_5590.sh
```

### 停止

```bash
cd ~/internalcontrol/haochi-vue
bash scripts/stop_5590.sh
```

### 查看日志

```bash
tail -n 50 ~/internalcontrol/haochi-vue/.runtime/haochi-5590.log
```

如果修改了 5590 的前端源码，重启前先重新构建：

```bash
cd ~/internalcontrol/haochi-vue
npm run build
bash scripts/start_5590.sh
```

## 单独管理 5600

5600 项目同时包含前端和后端：

```text
前端端口：5600
后端端口：5001
前端 tmux 会话：icir-frontend
后端 tmux 会话：icir-backend
```

### 启动

```bash
cd ~/internalcontrol/ICIR-vue
bash run_5600.sh start
```

### 重启

```bash
cd ~/internalcontrol/ICIR-vue
bash run_5600.sh restart
```

### 停止

```bash
cd ~/internalcontrol/ICIR-vue
bash run_5600.sh stop
```

### 检查状态

```bash
cd ~/internalcontrol/ICIR-vue
bash run_5600.sh status
```

## 一次检查全部端口

```bash
for port in 5560 5570 5580 5590 5600; do
  curl -s -o /dev/null --max-time 3 \
    -w "端口 $port HTTP=%{http_code}\n" \
    "http://127.0.0.1:$port/"
done
```

检查监听状态：

```bash
ss -ltnp | grep -E ':(5560|5570|5580|5590|5600)'
```

## 统一脚本日志

如果项目由 `restart_vue_pages.sh` 启动，日志位于：

```text
~/internalcontrol/logs/vue-pages/5560.log
~/internalcontrol/logs/vue-pages/5570.log
~/internalcontrol/logs/vue-pages/5580.log
~/internalcontrol/logs/vue-pages/5590.log
~/internalcontrol/logs/vue-pages/5600.log
```

例如：

```bash
tail -f ~/internalcontrol/logs/vue-pages/5560.log
```

## 常用故障检查

### 检查实时数据挂载

```bash
findmnt -T /mnt/trade_data -o TARGET,SOURCE,FSTYPE
ls /mnt/trade_data/data
ls /mnt/trade_data/turnover | tail
ls /mnt/trade_data/order
```

### 检查 GitHub 连通性

```bash
cd ~/internalcontrol
timeout 15s git ls-remote origin HEAD
echo $?
```

返回提交哈希且退出码为 `0` 表示 GitHub 网络和认证正常。

### 5560 实时接口检查

```bash
curl -s 'http://127.0.0.1:5560/api/internal-control-data?product=gy' \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); print({k:d.get(k) for k in ("date", "sourceMode", "tradeDataRoot", "fallbackReason", "sources")})'
```

实时运行时应重点确认：

```text
sourceMode = realtime
tradeDataRoot = /mnt/trade_data
date = 最新可用交易日
```
