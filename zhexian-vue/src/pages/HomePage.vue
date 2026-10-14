<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import NetValueChart from '@/components/NetValueChart.vue'
import { usePlayback } from '@/composables/usePlayback'
import type { HaochiDataset } from '@/lib/chart'

const AUTOPLAY_DURATION_MS = 90_000
const LOOP_DELAY_MS = 2_000

const dataset = ref<HaochiDataset | null>(null)
const loading = ref(true)
const error = ref('')

const { currentIndex, play, reset, speedMs } = usePlayback(() => dataset.value, {
  loop: true,
  loopDelayMs: LOOP_DELAY_MS,
})

async function loadDataset() {
  loading.value = true
  error.value = ''
  try {
    const response = await fetch('/haochi.json')
    if (!response.ok) {
      throw new Error(`数据文件读取失败: ${response.status}`)
    }
    dataset.value = (await response.json()) as HaochiDataset
    reset()
    const frameCount = Math.max(dataset.value.dates.length - 1, 1)
    speedMs.value = Math.max(16, Math.round(AUTOPLAY_DURATION_MS / frameCount))
    await nextTick()
    play()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '数据加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadDataset)
</script>

<template>
  <main class="dashboard-page">
    <div class="page-logo-wrap">
      <img class="page-logo" src="/logo.png" alt="Treadle Fountain logo" />
    </div>

    <p v-if="error" class="error-banner">{{ error }}</p>

    <section class="chart-panel">
      <NetValueChart :dataset="dataset" :current-index="currentIndex" :loading="loading" />
    </section>
  </main>
</template>
