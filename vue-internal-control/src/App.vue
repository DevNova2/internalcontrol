<script setup>
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import ChartPanel from './components/ChartPanel.vue'
import EChartsChart from './components/EChartsChart.vue'
import { loadInternalControlCharts, PRODUCTS } from './lib/internalControl'
import logoImage from './assets/logo.png'

const loading = ref(true)
const error = ref('')
const selectedProductId = ref(PRODUCTS[0].id)
const selectedDate = ref('')
const currentProduct = ref(PRODUCTS[0])
let refreshTimer = null
const REFRESH_INTERVAL_MS = 30_000
const charts = reactive({
  turn: { data: [], layout: {} },
  deviation: { data: [], layout: {} },
  settlement: { data: [], layout: {} },
  model: { data: [], layout: {} },
})

async function loadCharts() {
  loading.value = true
  error.value = ''
  try {
    const result = await loadInternalControlCharts(selectedProductId.value, selectedDate.value)
    currentProduct.value = result.product
    if (result.product?.date) {
      selectedDate.value = result.product.date
    }
    Object.assign(charts, {
      turn: result.turn,
      deviation: result.deviation,
      settlement: result.settlement,
      model: result.model,
    })
  } catch (err) {
    error.value = err instanceof Error ? err.message : '页面加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadCharts()
  refreshTimer = window.setInterval(loadCharts, REFRESH_INTERVAL_MS)
})

onBeforeUnmount(() => {
  if (refreshTimer) {
    window.clearInterval(refreshTimer)
  }
})
</script>

<template>
  <main class="page-shell">
    <div class="page-header">
      <div class="top-right-bar">
        <div class="toolbar toolbar--inline">
          <label class="toolbar-label" for="product-select">产品选择</label>
          <select
            id="product-select"
            v-model="selectedProductId"
            class="toolbar-select"
            @change="loadCharts"
          >
            <option
              v-for="product in PRODUCTS"
              :key="product.id"
              :value="product.id"
            >
              {{ product.label }}
            </option>
          </select>
        </div>

        <!--
        <div class="toolbar toolbar--inline">
          <label class="toolbar-label" for="trade-date">交易日期</label>
          <input
            id="trade-date"
            v-model="selectedDate"
            class="toolbar-select"
            type="date"
            @change="loadCharts"
          />
        </div>
        -->

        <div class="logo-container">
          <img :src="logoImage" alt="Treadle Fountain Logo" class="brand-logo" />
        </div>
      </div>
    </div>

    <div class="dashboard">
      <div class="left-column">
        <ChartPanel
          class="card card--turn"
          title="换仓数据"
          :tag="`产品 ${currentProduct.label}`"
        >
          <EChartsChart :data="charts.turn.data" :layout="charts.turn.layout" :loading="loading" realtime />
        </ChartPanel>

        <ChartPanel
          class="card card--model"
          title="超额差异图"
          :tag="`产品 ${currentProduct.label}`"
        >
          <EChartsChart :data="charts.model.data" :layout="charts.model.layout" :loading="loading" realtime />
        </ChartPanel>

        <ChartPanel
          class="card card--settlement"
          title="交割单图"
          :tag="`产品 ${currentProduct.label}`"
        >
          <EChartsChart :data="charts.settlement.data" :layout="charts.settlement.layout" :loading="loading" realtime />
        </ChartPanel>
      </div>

      <div class="right-column">
        <ChartPanel
          class="card card--deviation"
          title="中位数偏离"
          :tag="`产品 ${currentProduct.label}`"
        >
          <EChartsChart :data="charts.deviation.data" :layout="charts.deviation.layout" :loading="loading" />
        </ChartPanel>
      </div>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>
  </main>
</template>
