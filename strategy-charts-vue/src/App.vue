<script setup>
import { onMounted, reactive, ref } from 'vue'
import heatmapImageUrl from '../09_热力图_网页.svg?url'
import ChartCard from './components/ChartCard.vue'
import PlotlyChart from './components/PlotlyChart.vue'
import {
  buildPerformanceChart,
  buildSingleStrategyChart,
  loadDashboardData,
} from './lib/chartBuilders'

const loading = ref(true)
const error = ref('')
const charts = reactive({
  single: { data: [], layout: {}, metrics: [] },
  performance: { data: [], layout: {}, metrics: [] },
})

async function loadPage() {
  loading.value = true
  error.value = ''
  try {
    const { performanceData, singleData } = await loadDashboardData()
    Object.assign(charts.single, buildSingleStrategyChart(singleData))
    Object.assign(charts.performance, buildPerformanceChart(performanceData))
  } catch (err) {
    error.value = err instanceof Error ? err.message : '页面加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadPage)
</script>

<template>
  <main class="page-shell">
    <p v-if="error" class="error-banner">{{ error }}</p>

    <div class="chart-grid">
      <div class="left-panel">
        <ChartCard class="drawdown-card">
          <PlotlyChart :data="charts.single.data" :layout="charts.single.layout" :loading="loading" />
        </ChartCard>

        <ChartCard class="performance-card">
          <PlotlyChart :data="charts.performance.data" :layout="charts.performance.layout" :loading="loading" />
        </ChartCard>
      </div>

      <div class="side-panel">
        <div class="page-logo" aria-hidden="true">
          <img src="/assets/logo.png" alt="Treadle Fountain" class="page-logo__image" />
        </div>

        <ChartCard class="heatmap-card">
          <div class="heatmap-image-wrap">
            <img class="heatmap-image" :src="heatmapImageUrl" alt="月度收益热力图" />
          </div>
        </ChartCard>
      </div>
    </div>
  </main>
</template>
