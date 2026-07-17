<script setup lang="ts">
import type { Metric } from '@/types/chart'

const props = defineProps<{
  modelValue: Metric
}>()

const emit = defineEmits<{
  'update:modelValue': [value: Metric]
}>()

function handleMetricChange(event: Event) {
  const target = event.target as HTMLSelectElement
  emit('update:modelValue', target.value as Metric)
}
</script>

<template>
  <header class="hero-header">
    <div class="hero-copy">
      <p class="hero-kicker">MiMo Inspired Data View</p>
      <div class="hero-title-row">
        <h1>IC · IR</h1>
        <span class="hero-title-line" />
      </div>
      <p class="hero-description">
        四联条形图以统一指标联动展示行业与市场分组表现，保留极简交互与克制的编辑感布局。
      </p>
    </div>

    <div class="metric-switcher">
      <label class="metric-label" for="metric-select">指标</label>
      <div class="metric-field">
        <select id="metric-select" :value="props.modelValue" @change="handleMetricChange">
          <option value="IR">IR</option>
          <option value="IC">IC</option>
        </select>
      </div>
    </div>
  </header>
</template>
