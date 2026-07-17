<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { fetchChartData, fetchCharts } from '@/api/charts'
import ChartsGrid from '@/components/ChartsGrid.vue'
import type { ChartMeta, ChartPanelState } from '@/types/chart'

const panels = ref<ChartPanelState[]>([])
const pageError = ref('')

function buildLoadingPanels(chartMetas: ChartMeta[]): ChartPanelState[] {
  return chartMetas.map((meta) => ({
    meta,
    status: 'loading',
    rows: [],
    availableMetrics: [],
    updatedAt: null,
    error: '',
  }))
}

async function loadPanels() {
  pageError.value = ''

  try {
    const chartMetas = await fetchCharts()
    panels.value = buildLoadingPanels(chartMetas)

    panels.value = await Promise.all(
      chartMetas.map(async (meta) => {
        try {
          const payload = await fetchChartData(meta.id)
          return {
            meta,
            status: 'success',
            rows: payload.rows,
            availableMetrics: payload.availableMetrics,
            updatedAt: payload.updatedAt ?? null,
            error: '',
          } satisfies ChartPanelState
        } catch (error) {
          return {
            meta,
            status: 'error',
            rows: [],
            availableMetrics: [],
            updatedAt: null,
            error: error instanceof Error ? error.message : '请求失败',
          } satisfies ChartPanelState
        }
      })
    )
  } catch (error) {
    pageError.value = error instanceof Error ? error.message : '图表列表加载失败'
  }
}

onMounted(loadPanels)
</script>

<template>
  <main class="mimo-page">
    <div class="page-noise" />
    <div class="page-shell">
      <p v-if="pageError" class="page-error">{{ pageError }}</p>
      <ChartsGrid v-if="panels.length" :panels="panels" />
    </div>
  </main>
</template>
