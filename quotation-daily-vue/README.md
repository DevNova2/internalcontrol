# 当日盘面涨跌分布 Vue 展示页

独立启动：

```bash
cd /Users/w/Desktop/internalcontrol/quotation-daily-vue
npm run dev
```

默认访问：

```text
http://127.0.0.1:5581
```

环境变量：

```bash
QUOTATION_PORT=5582 npm run dev
QUOTATION_MONGO_URL='mongodb://192.168.1.77:27017/' npm run dev
```

数据来源：

- `statistic.quo_chg`：当日按市值分组平均涨跌幅
- `statistic.quo_bins`：当日涨跌幅分布
- `basic_wind.w_vol_price` + `basic_wind.w_basic_info`：按行业分组所需的个股涨跌幅和行业映射

当前仓库已内置一份本地静态样本数据：

- `public/data/daily-2025-12-31.json`

运行逻辑：

- 优先读取 `public/data/daily-*.json`
- 只有本地静态文件不存在时，才回退到 MongoDB

因此即使数据库不可用，当前项目也可以直接展示 `2025-12-31` 的页面。
