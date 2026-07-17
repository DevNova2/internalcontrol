import type { EChartsOption } from 'echarts'
import type { ChartRow, Metric } from '@/types/chart'

const BAR_COLORS = ['#3b82f6', '#4c8df7', '#5b99f8', '#6aa5f9', '#7cb3fb']

interface ChartStyle {
  backgroundColor: string | Record<string, unknown>
  barColor: Record<string, unknown> | ((params: { dataIndex: number }) => string)
  borderColor: string
  emphasisBorderColor: string
  emphasisShadowColor: string
  labelColor: string
  axisLineColor: string
  splitLineColor: string
}

function resolveChartStyle(chartId?: string): ChartStyle {
  if (chartId === 'industry') {
    return {
      backgroundColor: {
        type: 'linear',
        x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(215, 231, 255, 0.7)' },
          { offset: 1, color: 'rgba(30, 45, 92, 0.7)' },
        ],
      },
      barColor: {
        type: 'linear',
        x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(2, 18, 56, 1)' },
          { offset: 1, color: 'rgba(170, 196, 246, 0.7)' },
        ],
      },
      borderColor: 'rgba(2, 18, 56, 0.44)',
      emphasisBorderColor: 'rgba(215, 231, 255, 0.9)',
      emphasisShadowColor: 'rgba(2, 18, 56, 0.28)',
      labelColor: 'rgba(255,255,255,0.72)',
      axisLineColor: 'rgba(255,255,255,0.18)',
      splitLineColor: 'rgba(255,255,255,0.1)',
    }
  }

  if (chartId === 'market') {
    return {
      backgroundColor: 'rgba(215, 231, 255, 0.8)',
      barColor: {
        type: 'linear',
        x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: '#000000' },
          { offset: 1, color: '#64a1fc' },
        ],
      },
      borderColor: 'rgba(0, 0, 0, 0.30)',
      emphasisBorderColor: 'rgba(100, 161, 252, 0.9)',
      emphasisShadowColor: 'rgba(0, 0, 0, 0.28)',
      labelColor: 'rgba(15,53,106,0.7)',
      axisLineColor: 'rgba(15,53,106,0.15)',
      splitLineColor: 'rgba(15,53,106,0.08)',
    }
  }

  if (chartId === 'chart3') {
    return {
      backgroundColor: {
        type: 'linear',
        x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(23, 44, 83, 0.2)' },
          { offset: 1, color: 'rgba(215, 231, 255, 1)' },
        ],
      },
      barColor: {
        type: 'linear',
        x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: '#64a1fc' },
          { offset: 1, color: '#000000' },
        ],
      },
      borderColor: 'rgba(100, 161, 252, 0.44)',
      emphasisBorderColor: 'rgba(100, 161, 252, 0.9)',
      emphasisShadowColor: 'rgba(100, 161, 252, 0.28)',
      labelColor: 'rgba(255,255,255,0.72)',
      axisLineColor: 'rgba(255,255,255,0.18)',
      splitLineColor: 'rgba(255,255,255,0.1)',
    }
  }

  if (chartId === 'chart4') {
    return {
      backgroundColor: '#d7e7ff',
      barColor: {
        type: 'linear',
        x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(170, 196, 230, 0.7)' },
          { offset: 1, color: 'rgba(2, 18, 56, 1)' },
        ],
      },
      borderColor: 'rgba(2, 18, 56, 0.44)',
      emphasisBorderColor: 'rgba(215, 231, 255, 0.9)',
      emphasisShadowColor: 'rgba(2, 18, 56, 0.28)',
      labelColor: 'rgba(15,53,106,0.7)',
      axisLineColor: 'rgba(15,53,106,0.15)',
      splitLineColor: 'rgba(15,53,106,0.08)',
    }
  }

  return {
    backgroundColor: 'transparent',
    barColor: (params: { dataIndex: number }) => BAR_COLORS[params.dataIndex % BAR_COLORS.length],
    borderColor: 'rgba(96,165,250,0.45)',
    emphasisBorderColor: 'rgba(191,219,254,0.78)',
    emphasisShadowColor: 'rgba(59,130,246,0.22)',
    labelColor: 'rgba(15,53,106,0.7)',
    axisLineColor: 'rgba(15,53,106,0.15)',
    splitLineColor: 'rgba(15,53,106,0.08)',
  }
}

export interface ParsedYearMonth {
  year: string
  month: string
}

export function formatMetricValue(value: number) {
  return value.toFixed(4)
}

export function hasMetricRows(rows: ChartRow[], metric: Metric) {
  return rows.some((row) => Number.isFinite(row[metric]))
}

export function pickPreferredMetric(rowsCollection: ChartRow[][]): Metric {
  const hasIr = rowsCollection.some((rows) => hasMetricRows(rows, 'IR'))
  return hasIr ? 'IR' : 'IC'
}

export function buildSeriesData(rows: ChartRow[], metric: Metric) {
  return rows.map((row) => Number(row[metric]))
}

export function parseYearMonthLabel(label: string): ParsedYearMonth | null {
  const match = label.trim().match(/^(\d{4})-(\d{2})(?:-\d{2})?$/)
  if (!match) {
    return null
  }

  const [, year, month] = match
  return {
    year,
    month,
  }
}

export function collectAvailableYears(rows: ChartRow[]) {
  return Array.from(
    new Set(
      rows
        .map((row) => parseYearMonthLabel(row.label)?.year)
        .filter((year): year is string => Boolean(year))
    )
  ).sort((left, right) => Number(right) - Number(left))
}

export function filterRowsByYear(rows: ChartRow[], year: string) {
  return rows
    .filter((row) => parseYearMonthLabel(row.label)?.year === year)
    .map((row) => {
      const parsed = parseYearMonthLabel(row.label)
      return {
        ...row,
        label: parsed ? `${parsed.month}月` : row.label,
      }
    })
}

export function formatUpdatedAt(updatedAt?: string | null) {
  if (!updatedAt) {
    return ''
  }

  const date = new Date(updatedAt)
  if (Number.isNaN(date.getTime())) {
    return ''
  }

  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

export function shouldShowChart4YearTick(rows: ChartRow[], index: number) {
  const parsed = parseYearMonthLabel(rows[index]?.label ?? '')
  if (!parsed) {
    return false
  }

  const previous = parseYearMonthLabel(rows[index - 1]?.label ?? '')
  return previous?.year !== parsed.year
}

export function buildBarOption(rows: ChartRow[], metric: Metric, title: string, chartId?: string): EChartsOption {
  const labels = rows.map((row) => row.label)
  const values = buildSeriesData(rows, metric)
  const shouldRotate = chartId === 'industry' && labels.length > 8
  const labelFontSize = labels.length > 20 ? 10 : 12
  const style = resolveChartStyle(chartId)
  const isChart4 = chartId === 'chart4'

  const xAxisData: (string | string[])[] = isChart4
    ? rows.map((row) => {
        const parsed = parseYearMonthLabel(row.label)
        return parsed ? parsed.month : row.label
      })
    : labels

  const xAxisLabelFormatter = isChart4
    ? (_value: string, index: number) => {
        const parsed = parseYearMonthLabel(rows[index]?.label ?? '')
        return parsed && shouldShowChart4YearTick(rows, index) ? parsed.year : ''
      }
    : undefined

  const xAxisConfig: Record<string, unknown> = {
    type: 'category' as const,
    data: xAxisData,
    axisTick: { show: false },
    axisLabel: {
      color: style.labelColor,
      interval: 0,
      rotate: shouldRotate ? 32 : 0,
      fontSize: labelFontSize,
      margin: 16,
      ...(xAxisLabelFormatter ? { formatter: xAxisLabelFormatter } : {}),
    },
    axisLine: {
      lineStyle: { color: style.axisLineColor },
    },
    splitLine: { show: false },
  }

  const tooltipFormatter = isChart4
    ? (params: any) => {
        const item = Array.isArray(params) ? params[0] : params
        const row = rows[item.dataIndex]
        return `${title}<br/>${row?.label ?? item.name}<br/>${metric}: ${formatMetricValue(Number(item.data))}`
      }
    : (params: any) => {
        const item = Array.isArray(params) ? params[0] : params
        return `${title}<br/>${item.axisValue}<br/>${metric}: ${formatMetricValue(Number(item.data))}`
      }

  return {
    backgroundColor: style.backgroundColor,
    animationDuration: 520,
    animationDurationUpdate: 420,
    grid: {
      left: 18,
      right: 18,
      top: 20,
      bottom: shouldRotate ? 84 : 44,
      containLabel: true,
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow',
        shadowStyle: {
          color: 'rgba(255,255,255,0.05)',
        },
      },
      backgroundColor: 'rgba(7, 8, 10, 0.96)',
      borderColor: 'rgba(255,255,255,0.14)',
      borderWidth: 1,
      textStyle: {
        color: 'rgba(255,255,255,0.82)',
        fontFamily: 'inherit',
      },
      formatter: tooltipFormatter,
    },
    xAxis: xAxisConfig,
    yAxis: {
      type: 'value',
      axisLabel: {
        color: style.labelColor,
        fontSize: 11,
      },
      axisLine: {
        show: false,
      },
      axisTick: {
        show: false,
      },
      splitLine: {
        lineStyle: {
          color: style.splitLineColor,
        },
      },
    },
    series: [
      {
        type: 'bar',
        data: values,
        barMaxWidth: 28,
        itemStyle: {
          borderRadius: [6, 6, 2, 2],
          borderColor: style.borderColor,
          borderWidth: 1,
          color: style.barColor,
        },
        emphasis: {
          itemStyle: {
            borderColor: style.emphasisBorderColor,
            shadowBlur: 18,
            shadowColor: style.emphasisShadowColor,
          },
        },
      },
    ],
  }
}
