<template>
  <div ref="chartRef" class="chart" :class="{ 'chart--loading': loading }"></div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: {
    type: Array,
    default: () => [],
  },
  layout: {
    type: Object,
    default: () => ({}),
  },
  loading: {
    type: Boolean,
    default: false,
  },
  realtime: {
    type: Boolean,
    default: false,
  },
  fill: {
    type: Boolean,
    default: false,
  },
})

const chartRef = ref(null)
const refreshTick = ref(Date.now())
let chartInstance = null
let resizeObserver = null
let refreshTimer = null

function getBeijingSecondsOfDay() {
  const parts = new Intl.DateTimeFormat('zh-CN', {
    timeZone: 'Asia/Shanghai',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).formatToParts(new Date())

  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]))
  return Number(values.hour) * 3600 + Number(values.minute) * 60 + Number(values.second)
}

function toSeconds(rawValue) {
  const [hour = '0', minute = '0', second = '0'] = String(rawValue || '')
    .trim()
    .slice(0, 8)
    .split(':')

  const numbers = [Number(hour), Number(minute), Number(second)]
  if (!numbers.every(Number.isFinite)) {
    return null
  }

  return numbers[0] * 3600 + numbers[1] * 60 + numbers[2]
}

function clipArray(source, length) {
  return Array.isArray(source) ? source.slice(0, length) : source
}

function clipRealtimeData(data) {
  if (!props.realtime) {
    return data
  }

  const currentSeconds = getBeijingSecondsOfDay()
  const keepFullTimeline = String(props.layout?.title || '').includes('交易细节')

  return data.map((trace) => {
    if (!Array.isArray(trace?.x) || trace.x.length === 0) {
      return trace
    }

    const seconds = trace.x.map(toSeconds)
    if (seconds.every((value) => value == null)) {
      return trace
    }

    let cutoffIndex = seconds.findIndex((value) => value != null && value > currentSeconds)
    if (cutoffIndex === -1) {
      cutoffIndex = trace.x.length
    } else if (cutoffIndex === 0) {
      cutoffIndex = 1
    }

    if (keepFullTimeline) {
      return {
        ...trace,
        x: trace.x,
        y: Array.isArray(trace.y)
          ? trace.y.map((value, index) => (index < cutoffIndex ? value : null))
          : trace.y,
        text: Array.isArray(trace.text)
          ? trace.text.map((value, index) => (index < cutoffIndex ? value : ''))
          : trace.text,
        customdata: Array.isArray(trace.customdata)
          ? trace.customdata.map((value, index) => (index < cutoffIndex ? value : null))
          : trace.customdata,
      }
    }

    return {
      ...trace,
      x: trace.x.slice(0, cutoffIndex),
      y: clipArray(trace.y, cutoffIndex),
      text: clipArray(trace.text, cutoffIndex),
      customdata: clipArray(trace.customdata, cutoffIndex),
    }
  })
}

function getMargin(value, fallback) {
  return Number.isFinite(value) ? value : fallback
}

function formatThousandsFixed(value, decimals = 2) {
  const number = Number(value)
  if (!Number.isFinite(number)) {
    return value
  }
  return number.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

function buildScatterColor(trace) {
  if (!Array.isArray(trace.marker?.color)) {
    return trace.marker?.color || trace.line?.color || '#4f6ef7'
  }

  const numericValues = trace.marker.color.filter((value) => Number.isFinite(value))
  const max = Math.max(...numericValues, 1)
  const min = Math.min(...numericValues, -1)

  return (params) => {
    const value = trace.marker.color[params.dataIndex]
    if (!Number.isFinite(value)) {
      return '#b8c4d6'
    }
    if (value >= 0) {
      const ratio = max === 0 ? 0 : value / max
      return `rgba(178, 10, 28, ${0.35 + 0.65 * ratio})`
    }
    const ratio = min === 0 ? 0 : Math.abs(value / min)
    return `rgba(5, 10, 172, ${0.35 + 0.65 * ratio})`
  }
}

function convertSeries(trace) {
  if (trace.type === 'bar' && trace.orientation === 'h') {
    return {
      name: trace.name,
      type: 'bar',
      data: trace.x.map((value, index) => ({
        value,
        itemStyle: {
          color: Array.isArray(trace.marker?.color) ? trace.marker.color[index] : trace.marker?.color,
          borderColor: Array.isArray(trace.marker?.line?.color) ? trace.marker.line.color[index] : trace.marker?.line?.color,
          borderWidth: Array.isArray(trace.marker?.line?.width) ? trace.marker.line.width[index] : trace.marker?.line?.width,
        },
        rawText: Array.isArray(trace.text) ? trace.text[index] : trace.text,
      })),
      label: {
        show: Array.isArray(trace.text),
        position: 'right',
        formatter: ({ data }) => data.rawText || '',
      },
    }
  }

  if (trace.type === 'scatter' && trace.mode === 'markers') {
    return {
      name: trace.name,
      type: 'scatter',
      xAxisIndex: 0,
      yAxisIndex: trace.yaxis === 'y2' ? 1 : 0,
      symbolSize: trace.marker?.size || 8,
      itemStyle: {
        color: buildScatterColor(trace),
        opacity: trace.marker?.opacity ?? 1,
      },
      data: trace.x.map((value, index) => [value, trace.y[index]]),
    }
  }

  return {
    name: trace.name,
    type: 'line',
    xAxisIndex: 0,
    yAxisIndex: trace.yaxis === 'y2' ? 1 : 0,
    showSymbol: false,
    smooth: false,
    lineStyle: {
      color: trace.line?.color || '#3b82f6',
      width: trace.line?.width || 2,
    },
    data: trace.x.map((value, index) => [value, trace.y[index]]),
  }
}

function buildOption() {
  const data = clipRealtimeData(props.data || [])
  const firstTrace = data[0] || {}
  const horizontalBar = firstTrace.type === 'bar' && firstTrace.orientation === 'h'
  const dualAxis = data.some((trace) => trace.yaxis === 'y2')
  const legendLayout = props.layout.legend || {}

  if (horizontalBar) {
    return {
      animationDurationUpdate: 500,
      backgroundColor: props.layout.paper_bgcolor || '#ffffff',
      grid: {
        left: getMargin(props.layout.margin?.l, 56),
        right: getMargin(props.layout.margin?.r, 44),
        top: getMargin(props.layout.margin?.t, 36),
        bottom: getMargin(props.layout.margin?.b, 42),
        containLabel: true,
      },
      tooltip: {
        trigger: 'item',
      },
      xAxis: {
        type: 'value',
        min: props.layout.xaxis?.range?.[0],
        max: props.layout.xaxis?.range?.[1],
        axisLabel: {
          formatter: props.layout.xaxis?.tickformat === '.0%' ? (value) => `${Math.round(value * 100)}%` : undefined,
        },
        splitLine: {
          show: true,
          lineStyle: { color: '#dbe3ef' },
        },
      },
      yAxis: {
        type: 'category',
        data: firstTrace.y || [],
      },
      series: data.map(convertSeries),
    }
  }

  const categories = firstTrace.x || []
  const yAxes = [
    {
      type: 'value',
      name: props.layout.yaxis?.title || '',
      min: props.layout.yaxis?.range?.[0],
      max: props.layout.yaxis?.range?.[1],
      axisLabel: {
        formatter: props.layout.yaxis?.tickformat === ',.2f'
          ? (value) => formatThousandsFixed(value, 2)
          : (props.layout.yaxis?.ticksuffix ? `{value}${props.layout.yaxis.ticksuffix}` : undefined),
      },
      splitLine: {
        show: true,
        lineStyle: { color: '#dbe3ef' },
      },
    },
  ]

  if (dualAxis) {
    yAxes.push({
      type: 'value',
      name: props.layout.yaxis2?.title || '',
      min: props.layout.yaxis2?.range?.[0],
      max: props.layout.yaxis2?.range?.[1],
      splitLine: { show: false },
    })
  }

  return {
    animationDurationUpdate: 500,
    backgroundColor: props.layout.paper_bgcolor || '#ffffff',
    legend: {
      show: props.layout.showlegend !== false,
      top: legendLayout.top ?? 0,
      left: legendLayout.left ?? 'center',
      orient: legendLayout.orientation === 'v' ? 'vertical' : 'horizontal',
      itemWidth: legendLayout.itemWidth,
      itemHeight: legendLayout.itemHeight,
      itemGap: legendLayout.itemGap,
      data: legendLayout.data,
    },
    grid: {
      left: getMargin(props.layout.margin?.l, 56),
      right: getMargin(props.layout.margin?.r, dualAxis ? 72 : 32),
      top: getMargin(props.layout.margin?.t, 58),
      bottom: getMargin(props.layout.margin?.b, 52),
      containLabel: true,
    },
    tooltip: {
      trigger: 'axis',
    },
    xAxis: {
      type: 'category',
      data: categories,
      axisLabel: {
        rotate: props.layout.xaxis?.tickangle || 0,
        fontSize: props.layout.xaxis?.tickfont?.size || 10,
      },
      splitLine: {
        show: true,
        lineStyle: { color: '#dbe3ef' },
      },
    },
    yAxis: yAxes,
    series: data.map(convertSeries),
  }
}

function resizeChart() {
  chartInstance?.resize()
}

async function renderChart() {
  await nextTick()
  if (!chartRef.value) {
    return
  }

  if (props.fill) {
    chartRef.value.style.removeProperty('height')
  } else if (props.layout?.height) {
    chartRef.value.style.height = `${props.layout.height}px`
  } else {
    chartRef.value.style.removeProperty('height')
  }

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  if (props.loading) {
    chartInstance.showLoading('default', {
      text: '加载中...',
      color: '#264f8f',
      maskColor: 'rgba(255,255,255,0.75)',
    })
    return
  }

  chartInstance.hideLoading()
  chartInstance.setOption(buildOption(), true)
}

onMounted(() => {
  renderChart()

  if (props.realtime) {
    refreshTimer = window.setInterval(() => {
      refreshTick.value = Date.now()
    }, 10000)
  }

  if (typeof ResizeObserver !== 'undefined' && chartRef.value) {
    resizeObserver = new ResizeObserver(resizeChart)
    resizeObserver.observe(chartRef.value)
  } else {
    window.addEventListener('resize', resizeChart)
  }
})

watch(
  () => [props.data, props.layout, props.loading, props.realtime, refreshTick.value],
  () => {
    renderChart()
  },
  { deep: true },
)

onBeforeUnmount(() => {
  window.clearInterval(refreshTimer)
  resizeObserver?.disconnect()
  window.removeEventListener('resize', resizeChart)
  chartInstance?.dispose()
  chartInstance = null
})
</script>
