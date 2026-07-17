# 策略图表 Vue 页面

独立启动：

```bash
cd /Users/w/Desktop/internalcontrol/strategy-charts-vue
npm install
npm run dev
```

默认访问：

```text
http://127.0.0.1:5583
```

页面内容：

- `222.py` 对应的月度收益热力图
- `performance_cumnet.pkl` 对应的累计净值对比图
- `plot_single_strategy.py` 对应的单策略净值与回撤图

数据来源：

- `public/data/min530.json`
- `public/data/performance_cumnet.json`
- `public/data/t3.json`

这些 JSON 已从仓库里的原始文件预生成，因此启动页面时不依赖 Python 环境。
