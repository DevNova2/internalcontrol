<script setup lang="ts">
import BarPanel from '@/components/BarPanel.vue'
import type { ChartPanelState } from '@/types/chart'

defineProps<{
  panels: ChartPanelState[]
}>()
</script>

<template>
  <section class="charts-grid" aria-label="四联条形图">
    <BarPanel
      v-for="panel in panels"
      :key="panel.meta.id"
      :meta="panel.meta"
      :rows="panel.rows"
      :available-metrics="panel.availableMetrics"
      :status="panel.status"
      :updated-at="panel.updatedAt"
      :error="panel.error"
    />
  </section>
</template>
