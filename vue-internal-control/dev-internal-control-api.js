import fs from 'node:fs/promises'
import path from 'node:path'

const PRODUCT_MAP = {
  gy: '进取1-中信-股衍',
  jq2: '进取2-东北-两融',
  jq3: '进取3-粤开-两融',
  yk: '屿阔-中金-两融',
}

const FALLBACK_DATE = '2026-04-20'
const FALLBACK_TURNOVER_RELATIVE = 'data/common/2026-04-20.json'
const FALLBACK_SETTLEMENT_RELATIVE = 'data/阿尔法1号-交易细节/2024-09-25/dma_zx.csv'
const FALLBACK_MODEL_RELATIVE = 'data/阿尔法1号-长江两融/2024-11-15/minute_cj_first_v2_0.csv'

function toPosix(filePath) {
  return filePath.split(path.sep).join('/')
}

async function pathExists(targetPath) {
  try {
    await fs.access(targetPath)
    return true
  } catch {
    return false
  }
}

async function readText(filePath) {
  return fs.readFile(filePath, 'utf8')
}

function parseCsv(text) {
  const rows = []
  let row = []
  let field = ''
  let inQuotes = false

  for (let index = 0; index < text.length; index += 1) {
    const char = text[index]
    const next = text[index + 1]

    if (char === '"') {
      if (inQuotes && next === '"') {
        field += '"'
        index += 1
      } else {
        inQuotes = !inQuotes
      }
    } else if (char === ',' && !inQuotes) {
      row.push(field)
      field = ''
    } else if ((char === '\n' || char === '\r') && !inQuotes) {
      if (char === '\r' && next === '\n') {
        index += 1
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
    headers.forEach((header, headerIndex) => {
      record[header] = values[headerIndex] ?? ''
    })
    return record
  })
}

function escapeCsvField(value) {
  const text = String(value ?? '')
  return /[",\n\r]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text
}

function buildCsv(headers, rows) {
  const lines = [headers.join(',')]
  rows.forEach((row) => {
    lines.push(headers.map((header) => escapeCsvField(row[header])).join(','))
  })
  return `${lines.join('\n')}\n`
}

function normalizeTurnoverCode(rawCode) {
  if (!rawCode || rawCode.length < 4) {
    return rawCode
  }
  return `${rawCode.slice(2)}.${rawCode.slice(0, 2)}`
}

function buildFallbackMonitorCsv(turnover, productId) {
  const codes = [
    ...(turnover.buy?.[productId] || []),
    ...(turnover.sell?.[productId] || []),
  ]
    .map(normalizeTurnoverCode)
    .filter(Boolean)

  const uniqueCodes = [...new Set(codes)]
  const headers = ['time', ...uniqueCodes]
  return `${headers.join(',')}\n`
}

function formatOrderDate(tradeDate) {
  return tradeDate.replaceAll('-', '')
}

function parseTimeFromMinuteFile(fileName) {
  const baseName = path.basename(fileName, '.csv')
  const timeDigits = baseName.slice(0, 6)
  if (!/^\d{6}$/.test(timeDigits)) {
    return ''
  }
  return `${timeDigits.slice(0, 2)}:${timeDigits.slice(2, 4)}:${timeDigits.slice(4, 6)}`
}

async function resolveTradeDataRoot() {
  const envRoot = process.env.TRADE_DATA_ROOT || ''
  const candidates = [
    envRoot,
    '/mnt/trade_data/test/交易组中间文件存储',
    '/mnt/trade_data/交易组中间文件存储',
  ].filter(Boolean)

  for (const candidate of candidates) {
    if (await pathExists(candidate)) {
      return candidate
    }
  }

  return envRoot
}

function getProductLabel(productId) {
  const productLabel = PRODUCT_MAP[productId]
  if (!productLabel) {
    throw new Error(`不支持的产品: ${productId}`)
  }
  return productLabel
}

async function getAvailableTradeDate(rootPath, productId) {
  const productLabel = getProductLabel(productId)
  const turnoverDir = path.join(rootPath, 'turnover')
  const entries = await fs.readdir(turnoverDir)
  const dates = entries
    .map((entry) => entry.match(/^(\d{4}-\d{2}-\d{2})\.json$/)?.[1] || '')
    .filter(Boolean)
    .sort()
    .reverse()

  for (const tradeDate of dates) {
    const monitorPath = path.join(rootPath, 'data', productLabel, `${tradeDate}-gy.csv`)
    const minuteDir = path.join(rootPath, 'data', productLabel, tradeDate)
    const orderPath = path.join(rootPath, 'order', productLabel, `${formatOrderDate(tradeDate)}-order.csv`)
    if (await pathExists(monitorPath) && await pathExists(minuteDir) && await pathExists(orderPath)) {
      return tradeDate
    }
  }

  throw new Error(`未找到 ${productLabel} 的可用日期`)
}

async function buildSettlementCsv(orderPath) {
  const rows = parseCsv(await readText(orderPath))
  let netSum = 0
  const settlementRows = rows
    .map((row) => {
      const orderPrice = Number(row.order_price)
      const orderVolume = Number(row.order_volume)
      if (!Number.isFinite(orderPrice) || !Number.isFinite(orderVolume)) {
        return null
      }
      const grossValue = orderPrice * orderVolume
      const side = String(row.order_side || '').trim().toLowerCase()
      const orderValue = side === 'sell' ? grossValue : side === 'buy' ? -grossValue : null
      if (!Number.isFinite(orderValue)) {
        return null
      }
      netSum += -orderValue
      return {
        time: String(row.time || '').slice(0, 5),
        order_value: orderValue.toFixed(2),
        net_sum: netSum.toFixed(2),
      }
    })
    .filter(Boolean)

  return {
    csv: buildCsv(['time', 'order_value', 'net_sum'], settlementRows),
    rowCount: settlementRows.length,
  }
}

async function buildModelCsv(minuteDir, turnover, productId, tradeDate) {
  const buyCodes = new Set((turnover.buy?.[productId] || []).map(normalizeTurnoverCode))
  const sellCodes = new Set((turnover.sell?.[productId] || []).map(normalizeTurnoverCode))
  const minuteFiles = (await fs.readdir(minuteDir))
    .filter((fileName) => fileName.endsWith('-gy-data.csv'))
    .sort()

  const rows = []

  for (const fileName of minuteFiles) {
    const time = parseTimeFromMinuteFile(fileName)
    if (!time) {
      continue
    }
    const fileRows = parseCsv(await readText(path.join(minuteDir, fileName)))
    fileRows.forEach((row) => {
      const code = String(row.code || '')
      const orderType = buyCodes.has(code) ? 'buy' : sellCodes.has(code) ? 'sell' : ''
      if (!orderType) {
        return
      }
      const lastPrice = Number(row.lastPrice)
      const lastClose = Number(row.lastClose)
      if (!Number.isFinite(lastPrice) || !Number.isFinite(lastClose) || lastClose === 0) {
        return
      }
      rows.push({
        date: tradeDate,
        order_type: orderType,
        time,
        code,
        chg_pre: (lastPrice / lastClose - 1).toFixed(6),
      })
    })
  }

  return {
    csv: buildCsv(['date', 'order_type', 'time', 'code', 'chg_pre'], rows),
    rowCount: rows.length,
  }
}

async function buildRealtimePayload({ rootPath, productId, tradeDate }) {
  const productLabel = getProductLabel(productId)
  const resolvedDate = tradeDate || await getAvailableTradeDate(rootPath, productId)
  const monitorPath = path.join(rootPath, 'data', productLabel, `${resolvedDate}-gy.csv`)
  const turnoverPath = path.join(rootPath, 'turnover', `${resolvedDate}.json`)
  const minuteDir = path.join(rootPath, 'data', productLabel, resolvedDate)
  const orderPath = path.join(rootPath, 'order', productLabel, `${formatOrderDate(resolvedDate)}-order.csv`)

  const [monitorCsv, turnover] = await Promise.all([
    readText(monitorPath),
    readText(turnoverPath).then((text) => JSON.parse(text)),
  ])
  const [settlementResult, modelResult] = await Promise.all([
    buildSettlementCsv(orderPath),
    buildModelCsv(minuteDir, turnover, productId, resolvedDate),
  ])

  return {
    product: productId,
    productLabel,
    date: resolvedDate,
    tradeDataRoot: rootPath,
    monitorCsv,
    turnover,
    settlementCsv: settlementResult.csv,
    modelCsv: modelResult.csv,
    sourceMode: 'realtime',
    fallbackReason: '',
    excessRows: modelResult.rowCount,
    settlementRows: settlementResult.rowCount,
    sources: {
      monitor: toPosix(monitorPath),
      turnover: toPosix(turnoverPath),
      order: toPosix(orderPath),
      minuteDir: toPosix(minuteDir),
    },
  }
}

async function buildFallbackPayload({ projectRoot, productId, reason }) {
  const productLabel = getProductLabel(productId)
  const publicRoot = path.join(projectRoot, 'public')
  const monitorPath = path.join(publicRoot, 'data', productLabel, `${FALLBACK_DATE}-gy.csv`)
  const turnoverPath = path.join(publicRoot, FALLBACK_TURNOVER_RELATIVE)
  const orderPath = path.join(publicRoot, FALLBACK_SETTLEMENT_RELATIVE)
  const modelPath = path.join(publicRoot, FALLBACK_MODEL_RELATIVE)
  const hasMonitorSample = await pathExists(monitorPath)
  const turnover = await readText(turnoverPath).then((text) => JSON.parse(text))
  const [settlementCsv, modelCsv, monitorCsv] = await Promise.all([
    readText(orderPath),
    readText(modelPath),
    hasMonitorSample
      ? readText(monitorPath)
      : Promise.resolve(buildFallbackMonitorCsv(turnover, productId)),
  ])

  return {
    product: productId,
    productLabel,
    date: FALLBACK_DATE,
    tradeDataRoot: '',
    monitorCsv,
    turnover,
    settlementCsv,
    modelCsv,
    sourceMode: 'fallback',
    fallbackReason: hasMonitorSample
      ? reason
      : `${reason}; fallback 日级样本缺失，已返回空白监控矩阵`,
    excessRows: Math.max(parseCsv(modelCsv).length, 0),
    settlementRows: Math.max(parseCsv(settlementCsv).length, 0),
    sources: {
      monitor: `/data/${productLabel}/${FALLBACK_DATE}-gy.csv`,
      turnover: `/${toPosix(FALLBACK_TURNOVER_RELATIVE)}`,
      order: `/${toPosix(FALLBACK_SETTLEMENT_RELATIVE)}`,
      minuteDir: `/${toPosix(FALLBACK_MODEL_RELATIVE)}`,
    },
  }
}

export async function createInternalControlPayload({ projectRoot, productId, tradeDate }) {
  const rootPath = await resolveTradeDataRoot()

  try {
    if (!rootPath || !await pathExists(rootPath)) {
      throw new Error(`TRADE_DATA_ROOT 不存在: ${rootPath || '(empty)'}`)
    }
    return await buildRealtimePayload({ rootPath, productId, tradeDate })
  } catch (error) {
    const reason = error instanceof Error ? error.message : '实时数据读取失败'
    return buildFallbackPayload({ projectRoot, productId, reason })
  }
}
