const CHART_FONT = 'Arial Unicode MS, Hiragino Sans GB, STHeiti, Songti SC, Microsoft YaHei, sans-serif'

function formatPercent(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '--'
  }
  return `${(value * 100).toFixed(digits)}%`
}

function parseDate(value) {
  return new Date(`${value}T00:00:00`)
}

function parseCsv(text) {
  const lines = text.trim().split(/\r?\n/).filter(Boolean)
  if (lines.length < 2) {
    throw new Error('净值与回撤 CSV 没有有效数据')
  }

  const headers = lines[0].replace(/^\uFEFF/, '').split(',').map((value) => value.trim())
  const records = lines.slice(1).map((line) => {
    const values = line.split(',').map((value) => value.trim())
    return Object.fromEntries(headers.map((header, index) => [header, values[index] ?? '']))
  })

  if (!headers.includes('date') || !headers.some((header) => ['nav', 'net_value'].includes(header))) {
    throw new Error('净值与回撤 CSV 必须包含 date 和 nav（或 net_value）列')
  }

  return records
}

export async function loadDashboardData() {
  const [perfResp, minResp, singleCsvResp, singleJsonResp] = await Promise.all([
    fetch('/data/performance_cumnet.json'),
    fetch('/data/min530.json'),
    fetch('/data/cp09.csv'),
    fetch('/data/cp.json'),
  ])

  if (!perfResp.ok || !minResp.ok || !singleJsonResp.ok) {
    throw new Error('图表数据加载失败，请检查 public/data 目录')
  }

  const [performanceData, min530Data, singleCsvText, fallbackSingleData] = await Promise.all([
    perfResp.json(),
    minResp.json(),
    singleCsvResp.text(),
    singleJsonResp.json(),
  ])

  const singleData = singleCsvResp.ok && /^\uFEFF?date\s*,/i.test(singleCsvText.trimStart())
    ? parseCsv(singleCsvText)
    : fallbackSingleData

  return {
    performanceData,
    min530Data,
    singleData,
  }
}

export function buildPerformanceChart(payload) {
  const colors = {
    strategy: '#C01900',
    '000985.XSHG': '#036FC0',
    alpha: '#0F356A',
  }

  const data = Object.entries(payload.series).map(([name, values]) => ({
    type: 'scatter',
    mode: 'lines',
    name,
    x: payload.dates,
    y: values,
    line: {
      width: 2.5,
      color: colors[name] || '#4B6A96',
    },
    hovertemplate: '%{x}<br>%{y:.4f}<extra>%{fullData.name}</extra>',
  }))

  const layout = {
    title: {
      text: '成长一号净值对比',
      x: 0.02,
      xanchor: 'left',
    },
    font: { family: CHART_FONT, color: '#0F356A' },
    paper_bgcolor: '#C5CDD7',
    plot_bgcolor: '#E6EBF5',
    legend: { orientation: 'h', y: 1.12 },
    margin: { l: 60, r: 30, t: 86, b: 50 },
    xaxis: {
      title: '日期',
      gridcolor: 'rgba(255,255,255,0.85)',
    },
    yaxis: {
      title: '累计净值',
      gridcolor: 'rgba(255,255,255,0.85)',
    },
    hovermode: 'x unified',
  }

  const metrics = Object.entries(payload.series).map(([name, values]) => {
    const lastValue = values[values.length - 1]
    return {
      label: `${name} 期末净值`,
      value: lastValue?.toFixed?.(4) ?? '--',
    }
  })

  return { data, layout, metrics }
}

export function buildHeatmapChart(records) {
  const sorted = [...records]
    .map((item) => ({ ...item, dateObj: parseDate(item.date), return_daily: Number(item.return_daily) }))
    .sort((a, b) => a.dateObj - b.dateObj)

  const monthlyMap = new Map()
  for (const item of sorted) {
    const year = item.dateObj.getFullYear()
    const month = item.dateObj.getMonth() + 1
    const key = `${year}-${String(month).padStart(2, '0')}`
    const current = monthlyMap.get(key) ?? { year, month, product: 1 }
    current.product *= 1 + item.return_daily
    monthlyMap.set(key, current)
  }

  const years = [...new Set(sorted.map((item) => item.dateObj.getFullYear()))].sort((a, b) => b - a)
  const matrix = []
  const text = []
  let positiveCount = 0
  let totalCount = 0

  for (const year of years) {
    const row = []
    const rowText = []
    let annualProduct = 1
    let annualHasValue = false

    for (let month = 1; month <= 12; month += 1) {
      const key = `${year}-${String(month).padStart(2, '0')}`
      const monthly = monthlyMap.get(key)
      const value = monthly ? monthly.product - 1 : null
      row.push(value)
      rowText.push(value === null ? '' : `${(value * 100).toFixed(1)}%`)
      if (value !== null) {
        annualProduct *= 1 + value
        annualHasValue = true
        totalCount += 1
        if (value > 0) {
          positiveCount += 1
        }
      }
    }

    const annualReturn = annualHasValue ? annualProduct - 1 : null
    row.push(annualReturn)
    rowText.push(annualReturn === null ? '' : `${(annualReturn * 100).toFixed(1)}%`)
    matrix.push(row)
    text.push(rowText)
  }

  const winRate = totalCount ? positiveCount / totalCount : 0
  const monthLabels = Array.from({ length: 12 }, (_, idx) => `${idx + 1}月`).concat('年度')
  const flatValues = matrix.flat().filter((value) => value !== null)
  const zmax = flatValues.length ? Math.max(...flatValues.map((v) => Math.abs(v))) : 0.1

  const data = [
    {
      type: 'heatmap',
      z: matrix,
      x: monthLabels,
      y: years.map(String),
      text,
      texttemplate: '%{text}',
      textfont: { family: CHART_FONT, color: '#0F356A', size: 12 },
      colorscale: [
        [0, '#0F356A'],
        [0.5, '#6F8FB8'],
        [1, '#C0D3EC'],
      ],
      zmin: -zmax,
      zmax,
      zmid: 0,
      hovertemplate: '年份=%{y}<br>列=%{x}<br>收益=%{text}<extra></extra>',
      colorbar: { title: { text: '收益率' } },
      xgap: 1,
      ygap: 1,
    },
  ]

  const layout = {
    title: {
      text: `<span style="font-size:14px">月度正收益胜率：${formatPercent(winRate)}</span>`,
      x: 0.02,
      xanchor: 'left',
    },
    font: { family: CHART_FONT, color: '#0F356A' },
    paper_bgcolor: '#8E9FB4',
    plot_bgcolor: '#8E9FB4',
    margin: { l: 70, r: 30, t: 42, b: 70 },
    xaxis: { title: '月份 / 年度累计', side: 'bottom' },
    yaxis: { title: '年份', autorange: 'reversed' },
  }

  const latestYear = years[0]
  const latestAnnual = matrix[0]?.[12] ?? null
  const metrics = [
    { label: '月度胜率', value: formatPercent(winRate) },
    { label: `${latestYear} 年度收益`, value: formatPercent(latestAnnual) },
    { label: '样本年份数', value: String(years.length) },
  ]

  return { data, layout, metrics }
}

export function buildSingleStrategyChart(records) {
  const sorted = [...records]
    .map((item) => ({
      ...item,
      date: item.date,
      net_value: Number(item.nav ?? item.net_value),
    }))
    .sort((a, b) => parseDate(a.date) - parseDate(b.date))
    .filter((item) => Number.isFinite(item.net_value))

  let maxNet = -Infinity
  const drawdowns = []
  const netValues = []
  const dates = []

  for (const item of sorted) {
    maxNet = Math.max(maxNet, item.net_value)
    dates.push(item.date)
    netValues.push(item.net_value)
    drawdowns.push((item.net_value / maxNet - 1) * 100)
  }

  const returns = []
  for (let i = 1; i < netValues.length; i += 1) {
    returns.push(netValues[i] / netValues[i - 1] - 1)
  }

  const mean = returns.reduce((sum, value) => sum + value, 0) / (returns.length || 1)
  const variance = returns.reduce((sum, value) => sum + (value - mean) ** 2, 0) / (returns.length || 1)
  const monthlyVol = Math.sqrt(variance) * Math.sqrt(21)
  const annualized = netValues.length ? netValues[netValues.length - 1] ** (252 / netValues.length) - 1 : null
  const maxDrawdown = drawdowns.length ? Math.min(...drawdowns) / 100 : null

  const data = [
    {
      type: 'scatter',
      mode: 'lines',
      name: '净值',
      x: dates,
      y: netValues,
      line: { color: '#C01900', width: 2.5 },
      hovertemplate: '%{x}<br>净值=%{y:.4f}<extra></extra>',
    },
    {
      type: 'scatter',
      mode: 'none',
      name: '回撤',
      x: dates,
      y: drawdowns,
      yaxis: 'y2',
      fill: 'tozeroy',
      fillcolor: 'rgba(3, 111, 192, 0.20)',
      hovertemplate: '%{x}<br>回撤=%{y:.2f}%<extra></extra>',
    },
  ]

  const layout = {
    title: {
      text: '进取一号净值与回撤',
      x: 0.02,
      xanchor: 'left',
    },
    font: { family: CHART_FONT, color: '#0F356A' },
    paper_bgcolor: '#C5CDD7',
    plot_bgcolor: '#E6EBF5',
    legend: { orientation: 'h', y: 1.16 },
    margin: { l: 60, r: 60, t: 96, b: 50 },
    xaxis: {
      title: '日期',
      gridcolor: 'rgba(255,255,255,0.65)',
      tickformat: '%Y/%m',
    },
    yaxis: {
      title: '累计净值',
      gridcolor: 'rgba(255,255,255,0.65)',
    },
    yaxis2: {
      title: '最大回撤 (%)',
      overlaying: 'y',
      side: 'right',
      showgrid: false,
      zeroline: true,
      zerolinecolor: 'rgba(255,255,255,0.65)',
      zerolinewidth: 1,
      ticksuffix: '%',
    },
    hovermode: 'x unified',
  }

  const metrics = [
    { label: '期末净值', value: netValues.at(-1)?.toFixed(4) ?? '--' },
    { label: '年化收益', value: formatPercent(annualized) },
    { label: '月波动', value: formatPercent(monthlyVol) },
    { label: '最大回撤', value: formatPercent(maxDrawdown) },
  ]

  return { data, layout, metrics }
}
