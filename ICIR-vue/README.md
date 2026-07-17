# MiMo 四联条形图独立项目

这个目录已经整理成可单独启动的版本，前后端和当前两份 CSV 数据都放在这里。

## 目录结构

```text
mimo-barcharts-standalone/
  backend/
    app.py
    data/
      industry_ic_analyse.csv
      market_ic_analyse.csv
  frontend/
    src/
    package.json
```

## 启动方式

### 1. 启动后端

```bash
cd backend
python3 -m pip install -r requirements.txt
python3 app.py
```

默认地址：`http://127.0.0.1:5001`

如果 5001 端口被占用，也可以这样启动：

```bash
PORT=5002 python3 app.py
```

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 4173
```

默认地址：`http://127.0.0.1:4173`

如果后端不是默认 `5001`，可以这样指定代理地址：

```bash
VITE_API_TARGET=http://127.0.0.1:5002 npm run dev -- --host 127.0.0.1 --port 4173
```

## 当前页面规则

- 页面仅保留 2×2 的四张条形图
- 顶部说明文案已删除
- 每张图右上角有自己的 `IC / IR` 选择器，互不影响
- `chart3`、`chart4` 目前仍为占位图，后续把新 CSV 放到 `backend/data/` 并在 `backend/app.py` 里登记即可
