<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { buildBarOption, hasMetricRows } from '@/lib/barchart'
import type { ChartMeta, ChartRow, Metric, PanelStatus } from '@/types/chart'

const props = defineProps<{
  meta: ChartMeta
  rows: ChartRow[]
  availableMetrics: Metric[]
  status: PanelStatus
  updatedAt?: string | null
  error?: string
}>()

const rootEl = ref<HTMLElement | null>(null)
const chartEl = ref<HTMLElement | null>(null)
const isVisible = ref(false)
const metric = ref<Metric>('IR')

let chart: echarts.ECharts | null = null
let observer: IntersectionObserver | null = null

const displayRows = computed<ChartRow[]>(() => props.rows)
const hasRows = computed(() => displayRows.value.length > 0)
const hasMetricData = computed(() => hasMetricRows(displayRows.value, metric.value))
const showMetricSelector = computed(() => props.availableMetrics.length > 1)
const displayTitle = computed(() => {
  if (props.meta.id === 'industry' || props.meta.id === 'market') {
    return `${props.meta.title}${metric.value}`
  }

  return props.meta.title
})

const placeholderMessage = computed(() => {
  if (props.status === 'error') {
    return props.error || '图表加载失败'
  }

  if (props.status === 'loading') {
    return '加载中...'
  }

  if (!hasRows.value) {
    return '待接入数据源'
  }

  return `${metric.value} 暂无可用值`
})

function ensureChart() {
  if (!chartEl.value) {
    return null
  }

  if (!chart) {
    chart = echarts.init(chartEl.value)
  }

  return chart
}

function destroyChart() {
  if (chart) {
    chart.dispose()
    chart = null
  }
}

function renderChart() {
  if (!hasRows.value || !hasMetricData.value) {
    destroyChart()
    return
  }

  const instance = ensureChart()
  if (!instance) {
    return
  }

  instance.setOption(buildBarOption(displayRows.value, metric.value, displayTitle.value, props.meta.id))
  instance.resize()
}

function handleResize() {
  chart?.resize()
}

function handleMetricChange(event: Event) {
  const target = event.target as HTMLSelectElement
  metric.value = target.value as Metric
}

onMounted(async () => {
  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          isVisible.value = true
          observer?.disconnect()
          observer = null
        }
      })
    },
    {
      threshold: 0.16,
    }
  )

  if (rootEl.value) {
    observer.observe(rootEl.value)
  }

  window.addEventListener('resize', handleResize)
  await nextTick()
  renderChart()
})

onBeforeUnmount(() => {
  observer?.disconnect()
  observer = null
  window.removeEventListener('resize', handleResize)
  destroyChart()
})

watch(
  () => [props.rows, props.availableMetrics] as const,
  ([rows, availableMetrics]) => {
    if (!rows.length || availableMetrics.length === 0) {
      metric.value = 'IR'
      return
    }

    if (availableMetrics.includes('IR')) {
      metric.value = 'IR'
      return
    }

    metric.value = availableMetrics[0]
  },
  { immediate: true, deep: true }
)

watch(
  () => [displayRows.value, metric.value, props.status],
  async () => {
    await nextTick()
    renderChart()
  },
  { deep: true }
)
</script>

<template>
  <article ref="rootEl" class="bar-panel" :class="{ 'is-visible': isVisible, 'bar-panel--first': meta.id === 'industry', 'bar-panel--second': meta.id === 'market', 'bar-panel--third': meta.id === 'chart3', 'bar-panel--fourth': meta.id === 'chart4' }">
    <div class="panel-heading">
      <div class="panel-heading-main">
        <div class="panel-title-wrap">
          <h2>{{ displayTitle }}</h2>
          <div class="panel-meta-row">
            <p>{{ meta.subtitle }}</p>
            <p v-if="meta.dateRangeLabel" class="panel-date-range">{{ meta.dateRangeLabel }}</p>
          </div>
        </div>
      </div>
      <div v-if="showMetricSelector" class="panel-control">
        <div class="metric-field metric-field--panel">
          <select :value="metric" :aria-label="`${displayTitle} 指标`" @change="handleMetricChange">
            <option v-for="option in availableMetrics" :key="option" :value="option">{{ option }}</option>
          </select>
        </div>
      </div>
    </div>

    <div class="panel-chart-shell" :class="{ 'is-placeholder': status !== 'success' || !hasRows || !hasMetricData }">
      <div v-if="status === 'success' && hasRows && hasMetricData" ref="chartEl" class="panel-chart" />
      <div v-else class="panel-placeholder">
        <span>{{ placeholderMessage }}</span>
      </div>
    </div>

  </article>
</template>
