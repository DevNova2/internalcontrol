<template>
  <div ref="chartRef" class="plotly-chart" :class="{ 'plotly-chart--loading': loading }"></div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import Plotly from 'plotly.js-dist-min'

const props = defineProps({
  data: {
    type: Array,
    default: () => [],
  },
  layout: {
    type: Object,
    default: () => ({}),
  },
  config: {
    type: Object,
    default: () => ({}),
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const chartRef = ref(null)

async function renderChart() {
  await nextTick()
  if (!chartRef.value || props.loading) {
    return
  }

  await Plotly.react(chartRef.value, props.data, props.layout, {
    responsive: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    ...props.config,
  })
}

onMounted(renderChart)

watch(
  () => [props.data, props.layout, props.loading],
  () => {
    renderChart()
  },
  { deep: true },
)

onBeforeUnmount(() => {
  if (chartRef.value) {
    Plotly.purge(chartRef.value)
  }
})
</script>
