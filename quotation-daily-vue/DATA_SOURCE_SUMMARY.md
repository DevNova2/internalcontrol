# quotation-daily-vue 数据源说明

## 背景

本次改造目标是让 `quotation-daily-vue` 的 `/api/daily`：

- 默认只使用新 Tom Mongo 实时计算
- 不再依赖 `192.168.1.77` 的 `statistic.quo_chg / statistic.quo_bins`
- 不再默认优先读取 `public/data/daily-*.json`
- 保持原有接口返回结构不变

当前实际改造文件：

- `server.py`

## 这次实际连接过的 Mongo

### 1. 新 Tom Mongo

连接串：

```text
mongodb://Tom:tom@192.168.30.195:29900/admin?authSource=admin
```

用途：

- 这是当前网页唯一的实时主数据源
- `/api/daily` 默认从这里读取并现场计算

本次实际检查过的数据库与集合：

- 数据库 `basic_wind`
  - 集合 `w_vol_price`
  - 集合 `w_basic_info`
- 数据库 `basic_jq`
  - 集合 `jq_daily_valuation`
- 数据库 `economic`
  - 集合 `trade_dates`

## 当前网页实际使用的表

### `basic_wind.w_vol_price`

关键字段：

- `date`
- `code`
- `pct_chg`

用途：

- 个股涨跌幅基础数据
- 用于计算 `distribution`
- 用于计算 `marketGroups`
- 用于计算 `industryGroups`

说明：

- `pct_chg` 是小数，例如 `0.0123` 表示 `1.23%`

### `basic_wind.w_basic_info`

关键字段：

- `date`
- `code`
- `industry_gics`
- `industry`

用途：

- 提供行业映射
- 结合 `server.py` 里的 `map_industry_name` 和 `INDUSTRY_ORDER`
- 用于计算 `industryGroups`

### `basic_jq.jq_daily_valuation`

关键字段：

- `date`
- `code`
- `market_cap`
- `circulating_market_cap`

用途：

- 提供市值数据
- `market_cap` 优先
- 若 `market_cap <= 0`，则退回 `circulating_market_cap`
- 用于计算 `marketGroups`

说明：

- 当前整页数据日期是否能推进，受这张表是否更新影响很大
- 本次检查时，这张表最新日期停在 `2026-05-29`

### `economic.trade_dates`

关键字段：

- `trade_date`

用途：

- 用于解析 `date=latest`
- 或解析指定日期 `date=YYYY-MM-DD` 时最近的交易日上界

说明：

- 后端优先参考这张表
- 但最终返回的 `tradeDate`，还必须是三张业务表共同可用的最近日期：
  - `basic_wind.w_vol_price`
  - `basic_wind.w_basic_info`
  - `basic_jq.jq_daily_valuation`

## 当前接口字段与数据来源对应关系

### `tradeDate`

来源逻辑：

- 优先参考 `economic.trade_dates.trade_date`
- 再与三张业务表共同可用日期取交集
- 返回最近的共同可用交易日

### `distribution`

来源：

- `basic_wind.w_vol_price`

计算方式：

- 读取指定 `tradeDate` 的 `pct_chg`
- 按 1% 分桶现场聚合
- 输出结构保持不变：

```json
[
  {"bin": 0, "value": 123, "color": "black"}
]
```

### `marketGroups`

来源：

- `basic_wind.w_vol_price`
- `basic_jq.jq_daily_valuation`

计算方式：

- 按 `code` 合并
- 按市值从大到小排序
- 分 30 组
- 计算每组平均涨跌幅

### `industryGroups`

来源：

- `basic_wind.w_vol_price`
- `basic_wind.w_basic_info`

计算方式：

- 按 `code` 合并
- 根据行业映射归类
- 计算每个行业平均涨跌幅和股票数

### `summary`

来源：

- 由 `distribution` 现场汇总生成

计算方式：

- `positive`：`bin > 0`
- `negative`：`bin < 0`
- `zero`：`bin == 0`
- `total`：总股票数

## 这次明确不再依赖的旧数据源

### 旧统计库

旧连接：

```text
mongodb://192.168.1.77:27017/
```

旧数据库与集合：

- 数据库 `statistic`
  - 集合 `quo_chg`
  - 集合 `quo_bins`

当前状态：

- 已从默认数据链路中移除
- 不再用于 `/api/daily` 的实时计算

### 旧 Tom

旧连接：

```text
mongodb://Tom:tom@192.168.1.99:29900/
```

旧数据库：

- `basic_wind`
- `basic_jq`

当前状态：

- 已不再使用
- 当前代码不再连接 `192.168.1.99`

### 本地静态 JSON

路径：

- `public/data/daily-*.json`

当前状态：

- 不再默认优先使用
- 仅在新 Tom Mongo 读取失败时作为 fallback

## 本次检查时的实际结论

检查时确认：

- `basic_wind.w_vol_price` 存在且有近日期数据
- `basic_wind.w_basic_info` 存在且有近日期数据
- `basic_jq.jq_daily_valuation` 存在，但最新日期停在 `2026-05-29`
- `economic.trade_dates` 存在

因此当时网页 `date=latest` 的实际返回结果是：

- `tradeDate = 2026-05-29`

原因不是代码未更新，而是：

- `jq_daily_valuation` 还没更新到更近日期
- 后端会自动取三张业务表共同可用的最近日期

## 后续更新规则

如果后续以下三张表都补到更新日期：

- `basic_wind.w_vol_price`
- `basic_wind.w_basic_info`
- `basic_jq.jq_daily_valuation`

那么网页刷新后会自动拿到新的 `tradeDate`，不需要手工生成静态文件。
