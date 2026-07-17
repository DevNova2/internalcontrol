import type { ChartDataResponse, ChartMeta } from '@/types/chart'

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url, {
    headers: {
      Accept: 'application/json',
    },
    cache: 'no-store',
  })

  if (!response.ok) {
    let message = `请求失败: ${response.status}`

    try {
      const payload = (await response.json()) as { error?: string }
      if (payload.error) {
        message = payload.error
      }
    } catch {
      // Ignore JSON parse failures and keep the fallback message.
    }

    throw new Error(message)
  }

  return (await response.json()) as T
}

export function fetchCharts() {
  return getJson<ChartMeta[]>('/api/charts')
}

export function fetchChartData(chartId: string) {
  return getJson<ChartDataResponse>(`/api/charts/${chartId}/data`)
}
