export const PRODUCTS = [
  {
    id: 'gy',
    label: '进取1-中信-股衍',
  },
  {
    id: 'jq2',
    label: '进取2-东北-两融',
  },
  {
    id: 'jq3',
    label: '进取3-粤开-两融',
  },
  {
    id: 'yk',
    label: '屿阔-中金-两融',
  },
]

const DEVIATION_CLAMP = 0.15
const DEVIATION_HEIGHT = 540
const TURN_CHART_HEIGHT = 180
const MODEL_CHART_HEIGHT = 160
const SETTLEMENT_HEIGHT = 180
const FALLBACK_DATE = '2026-04-20'
const FALLBACK_TURNOVER_PATH = '/data/common/2026-04-20.json'
const FALLBACK_SETTLEMENT_PATH = '/data/阿尔法1号-交易细节/2024-09-25/dma_zx.csv'
const FALLBACK_MODEL_PATH = '/data/阿尔法1号-长江两融/2024-11-15/minute_cj_first_v2_0.csv'

async function fetchInternalControlPayload(productId, tradeDate = '') {
  const params = new URLSearchParams({ product: productId })
  if (tradeDate) {
    params.set('date', tradeDate)
  }

  const response = await fetch(`/api/internal-control-data?${params.toString()}`)
  if (!response.ok) {
    let message = '页面加载失败'
    try {
      const payload = await response.json()
      message = payload.error || message
    } catch {
      message = `接口读取失败: ${response.status}`
    }
    throw new Error(message)
  }
  return response.json()
}

async function fetchStaticText(path) {
  const response = await fetch(path)
  if (!response.ok) {
    throw new Error(`读取本地样本失败: ${path}`)
  }
  return response.text()
}

async function fetchStaticJson(path) {
  const response = await fetch(path)
  if (!response.ok) {
    throw new Error(`读取本地样本失败: ${path}`)
  }
  return response.json()
}

function parseCsv(text) {
  const rows = []
  let row = []
  let field = ''
  let inQuotes = false

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i]
    const next = text[i + 1]

    if (char === '"') {
      if (inQuotes && next === '"') {
        field += '"'
        i += 1
      } else {
        inQuotes = !inQuotes
      }
    } else if (char === ',' && !inQuotes) {
      row.push(field)
      field = ''
    } else if ((char === '\n' || char === '\r') && !inQuotes) {
      if (char === '\r' && next === '\n') {
        i += 1
      }
      row.push(field)
      field = ''
      if (row.some((item) => item !== '')) {
        rows.push(row)
      }
      row = []
    } else {
      field += char
    }
  }

  if (field !== '' || row.length > 0) {
    row.push(field)
    if (row.some((item) => item !== '')) {
      rows.push(row)
    }
  }

  const headers = rows[0] || []
  return rows.slice(1).map((values) => {
    const record = {}
    headers.forEach((header, index) => {
      record[header] = values[index] ?? ''
    })
    return record
  })
}

function loadMatrixCsv(text) {
  const lines = parseCsv(text)
  if (!lines.length) {
    return { times: [], columns: [] }
  }

  const headers = Object.keys(lines[0])
  const timeKey = headers[0]
  const columnKeys = headers.slice(1)
  const times = []
  const columns = columnKeys.map((key) => ({ name: key, values: [] }))

  lines.forEach((line) => {
    times.push(String(line[timeKey] || '').slice(0, 5))
    columnKeys.forEach((key, index) => {
      const raw = line[key]
      const value = raw === '' ? null : Number(raw)
      columns[index].values.push(Number.isFinite(value) ? value : null)
    })
  })

  return { times, columns }
}

function toMonitorCode(rawCode) {
  if (!rawCode || rawCode.length < 4) {
    return rawCode
  }
  return `${rawCode.slice(2)}.${rawCode.slice(0, 2)}`
}

function createBaseLayout(title, height) {
  return {
    title: {
      text: title,
      x: 0,
      xanchor: 'left',
      font: { size: 18, color: '#23314d' },
    },
    height,
    autosize: true,
    paper_bgcolor: '#d7e7ff',
    plot_bgcolor: '#edf2f7',
    font: { size: 13, color: '#1f2937' },
    margin: { l: 40, r: 20, t: 40, b: 20 },
    legend: {
      orientation: 'v',
      yanchor: 'top',
      y: 1,
      xanchor: 'left',
      x: 1.01,
      bgcolor: 'rgba(255,255,255,0.75)',
    },
    xaxis: {
      showgrid: true,
      gridcolor: '#dbe3ef',
      tickfont: { size: 10 },
    },
    yaxis: {
      showgrid: true,
      gridcolor: '#dbe3ef',
    },
  }
}

function formatPercent(value) {
  return `${(value * 100).toFixed(2)}%`
}

function createTurnChart(matrix, turnover, product) {
  const turnoverId = product.turnoverId || product.id
  const buyCodes = (turnover.buy?.[turnoverId] || []).map(toMonitorCode)
  const sellCodes = (turnover.sell?.[turnoverId] || []).map(toMonitorCode)
  const traces = []

  matrix.columns.forEach((column) => {
    if (buyCodes.includes(column.name)) {
      traces.push({
        x: matrix.times,
        y: column.values,
        type: 'scatter',
        mode: 'lines',
        name: column.name,
        line: { color: '#d37440', width: 1.3 },
        hovertemplate: `${column.name}<br>时间: %{x}<br>值: %{y:,.0f}<extra></extra>`,
      })
    } else if (sellCodes.includes(column.name)) {
      traces.push({
        x: matrix.times,
        y: column.values,
        type: 'scatter',
        mode: 'lines',
        name: column.name,
        line: { color: '#0070c0', width: 1.3 },
        hovertemplate: `${column.name}<br>时间: %{x}<br>值: %{y:,.0f}<extra></extra>`,
      })
    }
  })

  const layout = createBaseLayout(`${product.label} - 换仓数据`, TURN_CHART_HEIGHT)
  layout.showlegend = false
  layout.yaxis.title = 'Individual Stock Value'
  return { data: traces, layout }
}

function createDeviationChart(matrix, turnover, product) {
  const turnoverId = product.turnoverId || product.id
  const excluded = new Set([
    ...(turnover.buy?.[turnoverId] || []).map(toMonitorCode),
    ...(turnover.sell?.[turnoverId] || []).map(toMonitorCode),
  ])

  const validColumns = matrix.columns
    .filter((column) => !excluded.has(column.name))
    .map((column) => ({ name: column.name, value: column.values[column.values.length - 1] }))
    .filter((item) => Number.isFinite(item.value))
    .sort((a, b) => a.value - b.value)

  const values = validColumns.map((item) => item.value)
  const mid = Math.floor(values.length / 2)
  const median = values.length === 0 ? 0 : values.length % 2 ? values[mid] : (values[mid - 1] + values[mid]) / 2
  const rows = validColumns.map((item) => {
    const rawDeviation = median === 0 ? 0 : item.value / median - 1
    return {
      ...item,
      rawDeviation,
      clampedDeviation: Math.max(-DEVIATION_CLAMP, Math.min(DEVIATION_CLAMP, rawDeviation)),
      isOutlier: Math.abs(rawDeviation) > DEVIATION_CLAMP,
    }
  })

  const clampedValues = rows.map((item) => item.clampedDeviation)
  const positiveMax = Math.max(0, ...clampedValues)
  const negativeMin = Math.min(0, ...clampedValues)
  const negativeOutliers = rows.filter((item) => item.rawDeviation < -DEVIATION_CLAMP).length
  const positiveOutliers = rows.filter((item) => item.rawDeviation > DEVIATION_CLAMP).length

  const colors = rows.map((item) => {
    if (item.clampedDeviation >= 0) {
      const ratio = positiveMax ? item.clampedDeviation / positiveMax : 0
      return `rgba(7, 32, 97, ${0.35 + 0.65 * ratio})`
    }
    const ratio = negativeMin ? Math.abs(item.clampedDeviation / negativeMin) : 0
    return `rgba(76, 134, 197, ${0.30 + 0.60 * ratio})`
  })

  const layout = createBaseLayout(`${product.label} - 中位数偏离`, DEVIATION_HEIGHT)
  layout.showlegend = false
  layout.paper_bgcolor = '#d7e7ff'
  layout.xaxis = {
    ...layout.xaxis,
    title: 'Deviation (clipped at +/-15%)',
    tickformat: '.0%',
    zeroline: true,
    zerolinecolor: '#24324b',
    range: [-DEVIATION_CLAMP, DEVIATION_CLAMP],
  }
  layout.yaxis = {
    ...layout.yaxis,
    title: 'Stock',
  }
  layout.margin.r = 44
  layout.annotations = [{
    x: 1,
    y: 1.065,
    xref: 'paper',
    yref: 'paper',
    xanchor: 'right',
    yanchor: 'bottom',
    align: 'right',
    showarrow: false,
    font: { size: 12, color: '#516074' },
    text: `异常值: 低于 -15% ${negativeOutliers} 个 / 高于 15% ${positiveOutliers} 个`,
  }]

  return {
    data: rows.length ? [{
      y: rows.map((item) => item.name),
      x: rows.map((item) => item.clampedDeviation),
      type: 'bar',
      orientation: 'h',
      marker: {
        color: colors,
        line: {
          color: 'rgba(255,255,255,0)',
          width: 0,
        },
      },
      customdata: rows.map((item) => [item.rawDeviation, item.isOutlier ? '是' : '否']),
      text: rows.map((item) => (item.isOutlier
        ? `${item.rawDeviation > 0 ? '>' : '<'} ${formatPercent(DEVIATION_CLAMP)}`
        : formatPercent(item.rawDeviation))),
      textposition: 'auto',
      hovertemplate: '%{y}<br>原始偏离: %{customdata[0]:.2%}<br>显示偏离: %{x:.2%}<br>异常值: %{customdata[1]}<extra></extra>',
    }] : [],
    layout,
  }
}

function createSettlementChart(rows, product) {
  const sorted = rows
    .map((row) => ({
      time: String(row.time || '').slice(0, 5),
      orderValue: Number(row.order_value),
      netSum: Number(row.net_sum),
    }))
    .filter((row) => row.time && Number.isFinite(row.orderValue) && Number.isFinite(row.netSum))
    .sort((a, b) => a.time.localeCompare(b.time))
  const netValues = sorted.map((row) => row.netSum)
  const netMin = Math.min(0, ...netValues)
  const netMax = Math.max(0, ...netValues)
  const netPadding = Math.max((netMax - netMin) * 0.12, 1)

  const layout = {
    height: SETTLEMENT_HEIGHT,
    title: `${product.label} - 交割单图`,
    font: { size: 22 },
    template: 'presentation',
    paper_bgcolor: '#d7e7ff',
    legend: {
      data: [
        {
          name: '累计净成交',
          icon: 'path://M2 5 H22 V7 H2 Z',
        },
        {
          name: '卖出',
          icon: 'circle',
        },
        {
          name: '买入',
          icon: 'circle',
        },
      ],
      itemWidth: 22,
      itemHeight: 8,
      itemGap: 14,
    },
    xaxis: { title: '时间' },
    yaxis: {
      title: '累计净成交金额',
      range: [netMin - netPadding, netMax + netPadding],
      tickformat: ',.2f',
    },
    yaxis2: {
      title: '订单金额（负买，正卖）',
      side: 'right',
      overlaying: 'y',
    },
    margin: { l: 40, r: 20, t: 40, b: 20 },
  }

  if (sorted.some((row) => row.time === '14:30')) {
    layout.shapes = [{
      type: 'line',
      x0: '14:30',
      x1: '14:30',
      y0: 0,
      y1: 1,
      xref: 'x',
      yref: 'paper',
      line: { color: 'red', width: 2, dash: 'dash' },
    }]
  }

  return {
    data: [
      {
        x: sorted.map((row) => row.time),
        y: sorted.map((row) => row.netSum),
        type: 'scatter',
        name: '累计净成交',
        line: { color: '#1f77b4' },
        hovertemplate: '时间: %{x}<br>累计净成交: %{y:,.0f}<extra></extra>',
      },
      {
        x: sorted.map((row) => row.time),
        y: sorted.map((row) => row.orderValue),
        type: 'scatter',
        mode: 'markers',
        name: '订单金额',
        xaxis: 'x',
        yaxis: 'y2',
        marker: {
          size: 9,
          symbol: 'circle',
          opacity: 1,
          color: sorted.map((row) => row.orderValue),
          gradientBy: 'y',
          positiveColorsTopDown: ['#001042', '#6F8CB7', '#88A4CB'],
          negativeColorsTopDown: ['#C36532', '#A40000'],
          showscale: false,
        },
        hovertemplate: '时间: %{x}<br>订单金额: %{y:,.0f}<extra></extra>',
      },
      {
        x: [],
        y: [],
        type: 'scatter',
        mode: 'markers',
        name: '卖出',
        marker: {
          size: 9,
          symbol: 'circle',
          opacity: 1,
          color: 'rgba(178, 10, 28, 1)',
        },
        hovertemplate: '<extra></extra>',
      },
      {
        x: [],
        y: [],
        type: 'scatter',
        mode: 'markers',
        name: '买入',
        marker: {
          size: 9,
          symbol: 'circle',
          opacity: 1,
          color: 'rgba(5, 10, 172, 1)',
        },
        hovertemplate: '<extra></extra>',
      },
    ],
    layout,
  }
}

function createModelChart(rows, product) {
  const grouped = new Map()

  rows.forEach((row) => {
    const orderType = row.order_type
    if (orderType !== 'buy' && orderType !== 'sell') {
      return
    }
    const time = String(row.time || '').slice(0, 5)
    const key = `${time}|${orderType}`
    const current = grouped.get(key) || { sum: 0, count: 0 }
    current.sum += Number(row.chg_pre)
    current.count += 1
    grouped.set(key, current)
  })

  const times = [...new Set(rows.map((row) => String(row.time || '').slice(0, 5)))]
    .filter(Boolean)
    .sort()

  const buySeries = []
  const sellSeries = []
  const differSeries = []

  times.forEach((time) => {
    const buyData = grouped.get(`${time}|buy`)
    const sellData = grouped.get(`${time}|sell`)
    const buyValue = buyData ? buyData.sum / buyData.count * 100 : 0
    const sellValue = sellData ? sellData.sum / sellData.count * 100 : 0
    buySeries.push(buyValue)
    sellSeries.push(sellValue)
    differSeries.push(sellValue - buyValue)
  })

  const layout = createBaseLayout(`${product.label} - 超额差异图`, MODEL_CHART_HEIGHT)
  layout.yaxis = {
    ...layout.yaxis,
    title: '收益偏离',
    ticksuffix: '%',
  }
  layout.shapes = [{
    type: 'line',
    x0: 0,
    x1: 1,
    xref: 'paper',
    y0: 0,
    y1: 0,
    yref: 'y',
    line: { color: 'red', width: 2 },
  }]

  const data = [
    {
      x: times,
      y: differSeries,
      type: 'scatter',
      mode: 'lines',
      name: 'differ',
      line: { color: '#202020', width: 2 },
    },
    {
      x: times,
      y: sellSeries,
      type: 'scatter',
      mode: 'lines',
      name: 'sell',
      line: { color: '#4f9ceb', width: 1.8 },
    },
    {
      x: times,
      y: buySeries,
      type: 'scatter',
      mode: 'lines',
      name: 'buy',
      line: { color: '#de8a59', width: 1.8 },
    },
  ]

  layout.legend = {
    data: data.map((trace) => ({
      name: trace.name,
      // Render the legend as a plain line segment instead of ECharts' default line-with-circle icon.
      icon: 'path://M2 6 H22',
    })),
    itemWidth: 22,
    itemHeight: 6,
    itemGap: 14,
    top: 0,
  }

  return {
    data,
    layout,
  }
}

function normalizePayload(product, payload) {
  const productId = payload.product?.id || payload.product || product.id
  const productLabel = payload.product?.label || payload.productLabel || product.label
  const tradeDate = payload.product?.date || payload.date || FALLBACK_DATE
  const sourceMode = payload.sourceMode || 'realtime'
  const fallbackReason = payload.fallbackReason || ''
  const sources = payload.sources || {}
  const tradeDataRoot = payload.tradeDataRoot || sources.tradeDataRoot || ''

  return {
    product: {
      id: productId,
      label: productLabel,
      date: tradeDate,
      sourceMode,
      fallbackReason,
      tradeDataRoot,
      sources: {
        monitor: sources.monitor || sources.monitorCsv || '',
        turnover: sources.turnover || sources.turnoverJson || '',
        order: sources.order || sources.settlementCsv || '',
        minuteDir: sources.minuteDir || sources.modelCsv || '',
      },
    },
    monitorCsv: payload.monitorCsv || '',
    turnover: payload.turnover || {},
    settlementCsv: payload.settlementCsv || '',
    modelCsv: payload.modelCsv || '',
  }
}

async function loadFallbackPayload(product, requestError = '') {
  const fallbackMonitorPath = `/data/${product.label}/${FALLBACK_DATE}-gy.csv`
  const [monitorCsv, turnover, settlementCsv, modelCsv] = await Promise.all([
    fetchStaticText(fallbackMonitorPath),
    fetchStaticJson(FALLBACK_TURNOVER_PATH),
    fetchStaticText(FALLBACK_SETTLEMENT_PATH),
    fetchStaticText(FALLBACK_MODEL_PATH),
  ])

  return normalizePayload(product, {
    product: product.id,
    productLabel: product.label,
    date: FALLBACK_DATE,
    tradeDataRoot: '',
    monitorCsv,
    turnover,
    settlementCsv,
    modelCsv,
    sourceMode: 'fallback',
    fallbackReason: requestError || '挂载目录不可用，已切换到本地固定样本',
    sources: {
      monitor: fallbackMonitorPath,
      turnover: FALLBACK_TURNOVER_PATH,
      order: FALLBACK_SETTLEMENT_PATH,
      minuteDir: FALLBACK_MODEL_PATH,
    },
  })
}

export async function loadInternalControlCharts(productId = PRODUCTS[0].id, tradeDate = '') {
  const product = PRODUCTS.find((item) => item.id === productId) || PRODUCTS[0]
  let normalized

  try {
    const payload = await fetchInternalControlPayload(product.id, tradeDate)
    normalized = normalizePayload(product, payload)
  } catch (apiError) {
    const apiMessage = apiError instanceof Error ? apiError.message : '接口读取失败'
    try {
      normalized = await loadFallbackPayload(product, apiMessage)
    } catch (fallbackError) {
      const fallbackMessage = fallbackError instanceof Error ? fallbackError.message : '本地样本读取失败'
      throw new Error(`${apiMessage}；且 fallback 失败: ${fallbackMessage}`)
    }
  }

  const { monitorCsv, turnover, settlementCsv, modelCsv } = normalized

  const monitorMatrix = loadMatrixCsv(monitorCsv)
  const settlementRows = parseCsv(settlementCsv)
  const modelRows = parseCsv(modelCsv)

  return {
    product: normalized.product,
    turn: createTurnChart(monitorMatrix, turnover, normalized.product),
    deviation: createDeviationChart(monitorMatrix, turnover, normalized.product),
    settlement: createSettlementChart(settlementRows, normalized.product),
    model: createModelChart(modelRows, normalized.product),
  }
}
