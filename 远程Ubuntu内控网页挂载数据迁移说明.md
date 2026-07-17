# 远程 Ubuntu 内控网页挂载数据迁移说明

## 目标

把 `vue-internal-control` 当前下载到本地 `public/data` 的一天 CSV/JSON 样本，切换为优先读取共享挂载目录里的实时数据。

核心要求：

- 主数据源：SMB/Windows 共享目录挂载后的实时文件。
- 备用数据源：保留原来的 `vue-internal-control/public/data` 固定样本，只有挂载目录读取失败时启用。
- 不改 Mongo 配置，不接新的 Mongo。
- 远程服务器是 Ubuntu，不能使用 Mac 的 `/Volumes/...` 路径，必须使用 Ubuntu 自己的挂载点。

## 共享目录与根路径

业务共享目录是：

```text
\\Desktop-hm4cqr6\交易组中间文件存储
```

我在 Mac 本地实际验证到的等价路径是：

```text
/Volumes/desktop-ldbc05e/test/交易组中间文件存储
```

Ubuntu 上不要照抄这个路径。Ubuntu 应该把 SMB 共享挂载到本机目录，例如：

```text
/mnt/trade_data
```

然后确认真实数据根目录是哪一种：

```text
/mnt/trade_data/交易组中间文件存储
```

或者如果共享外层还有 `test`：

```text
/mnt/trade_data/test/交易组中间文件存储
```

最终统一用环境变量控制：

```bash
export TRADE_DATA_ROOT="/mnt/trade_data/test/交易组中间文件存储"
```

代码里所有路径都必须从 `TRADE_DATA_ROOT` 拼出来。后续换挂载点时只改这个环境变量。

## Ubuntu 挂载示例

先安装 CIFS 工具：

```bash
sudo apt-get update
sudo apt-get install -y cifs-utils
```

创建挂载点：

```bash
sudo mkdir -p /mnt/trade_data
```

写 SMB 凭据文件，用户名密码按实际情况替换：

```bash
sudo tee /etc/.desktop_hm4cqr6_credentials >/dev/null <<'EOF'
username=你的SMB用户名
password=你的SMB密码
EOF

sudo chown root:root /etc/.desktop_hm4cqr6_credentials
sudo chmod 600 /etc/.desktop_hm4cqr6_credentials
```

如果 Ubuntu 能解析主机名：

```bash
sudo mount -t cifs '//Desktop-hm4cqr6/交易组中间文件存储' /mnt/trade_data \
  -o credentials=/etc/.desktop_hm4cqr6_credentials,iocharset=utf8,vers=3.0,uid=$(id -u),gid=$(id -g)
```

如果主机名解析不了，用实际 IP：

```bash
sudo mount -t cifs '//192.168.xx.xx/交易组中间文件存储' /mnt/trade_data \
  -o credentials=/etc/.desktop_hm4cqr6_credentials,iocharset=utf8,vers=3.0,uid=$(id -u),gid=$(id -g)
```

挂载后验证：

```bash
find /mnt/trade_data -maxdepth 4 -type d -name '交易组中间文件存储'
ls "$TRADE_DATA_ROOT"
ls "$TRADE_DATA_ROOT/data"
ls "$TRADE_DATA_ROOT/turnover" | tail
ls "$TRADE_DATA_ROOT/order"
```

共享目录根下应该能看到类似：

```text
data
turnover
order
asset_setting
cost_model
index
log
tmp_data
交易记录
估值表
```

## 四个产品映射

网页产品选择应有四个产品：

```text
gy  -> 进取1-中信-股衍
jq2 -> 进取2-东北-两融
jq3 -> 进取3-粤开-两融
yk  -> 屿阔-中金-两融
```

`turnover/<date>.json` 里的 key 也是这四个：

```text
gy / jq2 / jq3 / yk
```

注意 `turnover` 里的股票代码格式类似：

```text
SZ301073
SH600099
```

需要转换成行情文件里的格式：

```text
301073.SZ
600099.SH
```

转换规则：

```text
SZ301073 -> 301073.SZ
SH600099 -> 600099.SH
```

## 四张图的数据来源

### 1. 换仓图

来源：

```text
{TRADE_DATA_ROOT}/data/{产品名}/{date}-gy.csv
{TRADE_DATA_ROOT}/turnover/{date}.json
```

例子：

```text
{TRADE_DATA_ROOT}/data/进取2-东北-两融/2026-06-09-gy.csv
{TRADE_DATA_ROOT}/turnover/2026-06-09.json
```

生成逻辑：

- 读取 `{date}-gy.csv`，它是宽表：
  - 第一列是时间。
  - 后续列是股票代码，例如 `300105.SZ`、`600830.SH`。
- 读取 turnover JSON 中当前产品的 `buy` 和 `sell` 股票列表。
- 将 turnover 代码转换成 `xxxxxx.SZ/SH` 后，在 `gy.csv` 列里找对应股票。
- buy 股票画一组线，sell 股票画一组线。

### 2. 中位数偏离图

来源同换仓图：

```text
{TRADE_DATA_ROOT}/data/{产品名}/{date}-gy.csv
{TRADE_DATA_ROOT}/turnover/{date}.json
```

生成逻辑：

- 用同一个 `{date}-gy.csv`。
- 排除 turnover buy/sell 股票。
- 对剩余股票取最后一个时间点的值。
- 计算中位数。
- 每只股票偏离：

```text
value / median - 1
```

- 页面显示时可以继续沿用原来的 `+/-15%` 截断逻辑。

### 3. 超额差异图

来源：

```text
{TRADE_DATA_ROOT}/data/{产品名}/{date}/*-gy-data.csv
{TRADE_DATA_ROOT}/turnover/{date}.json
```

例子：

```text
{TRADE_DATA_ROOT}/data/进取2-东北-两融/2026-06-09/091130-gy-data.csv
{TRADE_DATA_ROOT}/data/进取2-东北-两融/2026-06-09/091200-gy-data.csv
...
```

每个 `*-gy-data.csv` 是分钟行情文件，字段里有：

```text
code,lastPrice,lastClose
```

生成逻辑：

- 从 turnover JSON 取当前产品的 buy/sell 股票。
- 代码格式转换成 `xxxxxx.SZ/SH`。
- 遍历 `{date}` 目录下所有 `*-gy-data.csv` 文件。
- 文件名前 6 位是时间，例如：

```text
091130-gy-data.csv -> 09:11:30
145932-gy-data.csv -> 14:59:32
```

- 对 buy/sell 股票逐个计算：

```text
chg_pre = lastPrice / lastClose - 1
```

- 后端可以把结果转成前端旧模型图可直接使用的 `modelCsv`：

```text
date,order_type,time,code,chg_pre
2026-06-09,buy,09:11:30,301519.SZ,0.009471
2026-06-09,sell,09:11:30,603968.SH,-0.008443
```

- `order_type` 只能是：

```text
buy
sell
```

- 前端继续按原逻辑聚合：
  - 同一时间 buy 平均值。
  - 同一时间 sell 平均值。
  - `differ = sell - buy`。

不要再把 `minute_cj_first_v2_0.csv` 当成主数据源。它只能作为 fallback。

### 4. 交割单图

来源：

```text
{TRADE_DATA_ROOT}/order/{产品名}/{YYYYMMDD}-order.csv
```

例子：

```text
{TRADE_DATA_ROOT}/order/进取2-东北-两融/20260609-order.csv
```

字段类似：

```text
date,time,order_no,stock_code,order_side,order_price,order_volume,rebalance_or_turn
```

`进取1-中信-股衍` 可能额外有：

```text
保证金,名义本金,保证金占用率
```

这些额外字段不影响交割单图。

生成逻辑：

```text
成交额 = order_price * order_volume
```

符号规则：

```text
sell -> order_value 为正数
buy  -> order_value 为负数
```

累计净成交金额：

```text
net_sum 从 0 开始
net_sum += -order_value
```

也可以等价理解为：

```text
buy 让 net_sum 增加
sell 让 net_sum 减少
```

后端可以把它转成前端旧交割单图可直接使用的 `settlementCsv`：

```text
time,order_value,net_sum
09:30,-29754.00,29754.00
09:31,18420.00,11334.00
```

不要再把 `dma_zx.csv` 当成主数据源。它只能作为 fallback。

## Django API 建议

保留或实现统一接口：

```text
/api/internal-control/?product=jq2&date=2026-06-09
```

参数：

```text
product: gy / jq2 / jq3 / yk
date: 可选，格式 YYYY-MM-DD
```

如果不传 `date`：

- 从 `{TRADE_DATA_ROOT}/turnover` 扫描最新的 `YYYY-MM-DD.json`。
- 对当前产品确认这些路径存在：

```text
{TRADE_DATA_ROOT}/data/{产品名}/{date}-gy.csv
{TRADE_DATA_ROOT}/data/{产品名}/{date}/
{TRADE_DATA_ROOT}/order/{产品名}/{YYYYMMDD}-order.csv
```

- 找到满足条件的最新日期作为默认日期。

建议 API 返回结构：

```json
{
  "product": "jq2",
  "productLabel": "进取2-东北-两融",
  "date": "2026-06-09",
  "tradeDataRoot": "/mnt/trade_data/test/交易组中间文件存储",
  "monitorCsv": "...",
  "turnover": {},
  "settlementCsv": "...",
  "modelCsv": "...",
  "sources": {
    "monitor": "/mnt/.../data/进取2-东北-两融/2026-06-09-gy.csv",
    "turnover": "/mnt/.../turnover/2026-06-09.json",
    "order": "/mnt/.../order/进取2-东北-两融/20260609-order.csv",
    "minuteDir": "/mnt/.../data/进取2-东北-两融/2026-06-09"
  }
}
```

`monitorCsv` 是原始 `{date}-gy.csv` 文本。

`turnover` 是解析后的 JSON。

`settlementCsv` 是后端从 `order` 文件实时生成的 CSV 文本：

```text
time,order_value,net_sum
```

`modelCsv` 是后端从 `*-gy-data.csv` 和 turnover 实时生成的 CSV 文本：

```text
date,order_type,time,code,chg_pre
```

## 前端改法

前端不要再把 `public/data` 作为主数据源。

主逻辑：

```text
loadInternalControlCharts(product, date)
  -> fetch /api/internal-control/?product={product}&date={date}
  -> 用 API 返回的 monitorCsv / turnover / settlementCsv / modelCsv 生成四张图
```

fallback 逻辑：

- 如果 `/api/internal-control/` 请求失败，才读取旧的固定样本：

```text
vue-internal-control/public/data/common/2026-04-20.json
vue-internal-control/public/data/进取1-中信-股衍/2026-04-20-gy.csv
vue-internal-control/public/data/进取2-东北-两融/2026-04-20-gy.csv
vue-internal-control/public/data/进取3-粤开-两融/2026-04-20-gy.csv
vue-internal-control/public/data/屿阔-中金-两融/2026-04-20-gy.csv
vue-internal-control/public/data/阿尔法1号-交易细节/2024-09-25/dma_zx.csv
vue-internal-control/public/data/阿尔法1号-长江两融/2024-11-15/minute_cj_first_v2_0.csv
```

注意：

- `dma_zx.csv` 和 `minute_cj_first_v2_0.csv` 只是 fallback。
- 挂载目录可读时，交割单图和超额差异图都必须从挂载目录实时生成。

## 当前本地已验证结果

我在 Mac 本地用挂载目录验证过 `2026-06-09`。

数据根目录：

```text
/Volumes/desktop-ldbc05e/test/交易组中间文件存储
```

验证结果：

```text
进取1-中信-股衍 / key gy
- 换仓图：35 条线匹配
- 中位数偏离：320 个股票柱
- 超额差异：235 个分钟文件，8225 个点
- 交割单：2163 行可计算

进取2-东北-两融 / key jq2
- 换仓图：32 条线匹配
- 中位数偏离：225 个股票柱
- 超额差异：517 个分钟文件，16544 个点
- 交割单：1841 行可计算

进取3-粤开-两融 / key jq3
- 换仓图：19 条线匹配
- 中位数偏离：131 个股票柱
- 超额差异：491 个分钟文件，9820 个点
- 交割单：1174 行可计算

屿阔-中金-两融 / key yk
- 换仓图：6 条线匹配
- 中位数偏离：47 个股票柱
- 超额差异：501 个分钟文件，2984 个点
- 交割单：131 行可计算
```

已知小边界：

- `进取3-粤开-两融` 的 turnover 中有一只 `605069.SH`，它能在分钟 `gy-data` 里找到，所以超额差异图没问题；但它不在日级 `{date}-gy.csv` 宽表里，所以换仓图如果只用 `{date}-gy.csv`，这只股票那条线会缺。
- `屿阔-中金-两融` 的超额差异有少量早盘点 `lastPrice/lastClose` 为空，应该跳过这些点，后续分钟正常。

## 远程 Ubuntu 必做验证

设置环境变量：

```bash
export TRADE_DATA_ROOT="/mnt/trade_data/test/交易组中间文件存储"
```

验证目录：

```bash
echo "$TRADE_DATA_ROOT"
ls "$TRADE_DATA_ROOT/data"
ls "$TRADE_DATA_ROOT/turnover" | tail
ls "$TRADE_DATA_ROOT/order"
```

验证接口：

```bash
curl 'http://127.0.0.1:8000/api/internal-control/?product=gy'
curl 'http://127.0.0.1:8000/api/internal-control/?product=jq2'
curl 'http://127.0.0.1:8000/api/internal-control/?product=jq3'
curl 'http://127.0.0.1:8000/api/internal-control/?product=yk'
```

每个接口都必须确认：

```text
monitorCsv 非空
turnover 有对应 product key
settlementCsv 行数 > 0
modelCsv 行数 > 0
sources.monitor 指向 TRADE_DATA_ROOT/data
sources.turnover 指向 TRADE_DATA_ROOT/turnover
sources.order 指向 TRADE_DATA_ROOT/order
sources.minuteDir 指向 TRADE_DATA_ROOT/data/{产品}/{date}
```

建议用脚本粗验行数：

```bash
curl -s 'http://127.0.0.1:8000/api/internal-control/?product=jq2' \
  | python3 - <<'PY'
import json, sys
d = json.load(sys.stdin)
print("product:", d.get("product"), d.get("productLabel"))
print("date:", d.get("date"))
print("tradeDataRoot:", d.get("tradeDataRoot"))
print("monitorCsv chars:", len(d.get("monitorCsv", "")))
print("settlementCsv rows:", len(d.get("settlementCsv", "").splitlines()) - 1)
print("modelCsv rows:", len(d.get("modelCsv", "").splitlines()) - 1)
print("sources:", d.get("sources"))
PY
```

## 给远程 agent 的关键修正点

如果远程 agent 之前已经做过一版，但还在扫描：

```text
dma_zx.csv
minute_cj_first_v2_0.csv
```

那么要改掉。

正确逻辑是：

```text
交割单图主数据 = order/{产品}/{YYYYMMDD}-order.csv 实时生成 settlementCsv
超额差异图主数据 = data/{产品}/{date}/*-gy-data.csv + turnover/{date}.json 实时生成 modelCsv
```

旧文件：

```text
dma_zx.csv
minute_cj_first_v2_0.csv
```

只能作为挂载失败时 fallback，不能作为挂载目录可用时的主逻辑。

## 不要做的事

- 不要改 `Internal_System/Datas/db_client.py`。
- 不要把 `192.168.1.77:27017` 改成挂载目录。
- 不要接新的 Mongo。
- 不要把 Mac 的 `/Volumes/...` 写死到 Ubuntu。
- 不要继续依赖历史 `/mnt/trade_data/position/realtime/...` 口径。
- 不要让交割单图和超额差异图继续固定读 `dma_zx.csv` / `minute_cj_first_v2_0.csv` 作为主数据。

## 最终判断标准

部署完成后，网页应满足：

- 产品下拉有 4 个产品。
- 不传日期时默认使用挂载目录最新可用日期。
- 四个产品切换后，四张图都随产品变化。
- 页面或 API 能显示当前命中的 `TRADE_DATA_ROOT` 和 `sources`。
- 挂载目录不可用时，页面能回退到 `public/data` 固定样本，并给出提示。

