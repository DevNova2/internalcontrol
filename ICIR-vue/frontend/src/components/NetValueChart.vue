<script setup lang="ts">
import * as echarts from 'echarts'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { buildChartOption, type HaochiDataset } from '@/lib/chart'

const props = defineProps<{
  dataset: HaochiDataset | null
  currentIndex: number
  loading: boolean
}>()

const chartRef = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null
let resizeObserver: ResizeObserver | null = null

const option = computed(() => {
  if (!props.dataset || props.dataset.dates.length === 0) {
    return null
  }
  return buildChartOption(props.dataset, props.currentIndex)
})

function renderChart() {
  if (!chartRef.value || !option.value) return
  if (!chart) {
    chart = echarts.init(chartRef.value)
  }
  chart.setOption(option.value, true)
}

onMounted(() => {
  if (chartRef.value) {
    chart = echarts.init(chartRef.value)
    resizeObserver = new ResizeObserver(() => chart?.resize())
    resizeObserver.observe(chartRef.value)
  }
  renderChart()
})

watch(option, () => {
  renderChart()
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  chart?.dispose()
})
</script>

<template>
  <div class="chart-shell">
    <div v-if="loading" class="chart-placeholder">正在加载静态数据...</div>
    <div v-else-if="!dataset" class="chart-placeholder">未找到可用的图表数据</div>
    <div v-else ref="chartRef" class="chart-canvas" />
  </div>
</template>
