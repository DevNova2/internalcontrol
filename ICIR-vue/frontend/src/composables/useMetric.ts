import { computed, ref } from 'vue'
import type { Metric } from '@/types/chart'

const metric = ref<Metric>('IR')

export function useMetric() {
  const metricLabel = computed(() => (metric.value === 'IR' ? '信息比率' : '信息系数'))

  function setMetric(nextMetric: Metric) {
    metric.value = nextMetric
  }

  return {
    metric,
    metricLabel,
    setMetric,
  }
}
