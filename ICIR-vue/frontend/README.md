# 浩池独立图表项目

这是一个单独可运行的 `Vue + ECharts + Python` 项目，用于把 `浩池.xlsx` 转成静态 JSON，并在网页里播放展示多产品净值曲线。

## 项目结构

- `浩池.xlsx`：原始 Excel 数据文件
- `scripts/convert_xlsx_to_json.py`：Excel 转 JSON 脚本
- `public/haochi.json`：前端直接读取的静态数据
- `src/components/NetValueChart.vue`：ECharts 图表组件
- `src/composables/usePlayback.ts`：播放推进逻辑
- `src/pages/HomePage.vue`：页面与控制区

## 先转换数据

```bash
python3 scripts/convert_xlsx_to_json.py --xlsx "./浩池.xlsx" --out "./public/haochi.json"
```

## 启动前端

```bash
npm install
npm run dev
```

## 运行检查

```bash
npm run check
npm run test
npm run build
```
