const { createApp, nextTick, onMounted, reactive, ref } = Vue

const CHART_COLORS = {
  zero: '#0d355c',
  positive: '#64a1fc',
  negative: '88A4CB',
}

createApp({
  setup() {
    const loading = ref(false)
    const error = ref('')
    const tradeDate = ref('')
    const startDate = ref('')
    const endDate = ref('')
    const viewScope = ref('daily')
    const statusTitle = ref('当前交易日')
    const statusText = ref('-')
    const chartCaption = ref('')
    const summary = reactive({
      positive: '-',
      negative: '-',
      zero: '-',
      total: 0,
    })
    const chartState = reactive({
      marketGroups: [],
      industryGroups: [],
      distribution: [],
    })

    function getChartHeight(chartId, fallback) {
      const target = document.getElementById(chartId)
      return target?.clientHeight || fallback
    }

    function resolveGroupBarColor(item) {
      if (item.chgMean > 0) return CHART_COLORS.positive
      if (item.chgMean < 0) return CHART_COLORS.negative
      return CHART_COLORS.zero
    }

    function resolveDistributionBarColor(item) {
      if (item.bin > 0) return CHART_COLORS.positive
      if (item.bin < 0) return CHART_COLORS.negative
      return CHART_COLORS.zero
    }

    function composeChartTitle(titleText) {
      return chartCaption.value ? `${titleText}<br><sup>${chartCaption.value}</sup>` : titleText
    }

    function buildGroupLayout(titleText, chartId, xaxisOverrides = {}) {
      return {
        height: getChartHeight(chartId, window.innerWidth < 900 ? 360 : 380),
        autosize: true,
        title: {
          text: composeChartTitle(titleText),
          x: 0.02,
          xanchor: 'left',
          font: { size: 18, color: '#0d355c' },
        },
        paper_bgcolor: '#d7e7ff',
        plot_bgcolor: '#d7e7ff',
        font: { size: 15, color: '#0d355c' },
        margin: { l: 62, r: 24, t: 56, b: 72 },
        showlegend: false,
        bargap: 0.18,
        xaxis: {
          title: titleText,
          tickfont: { size: 11 },
          showgrid: false,
          ...xaxisOverrides,
        },
        yaxis: {
          title: '涨跌幅',
          ticksuffix: '%',
          gridcolor: 'rgba(255, 255, 255, 0.6)',
          zeroline: true,
          zerolinecolor: 'rgba(255, 255, 255, 0.6)',
        },
      }
    }

    function buildDistributionLayout() {
      const distributionAxis = resolveDistributionAxis()
      return {
        height: getChartHeight('distribution-chart', window.innerWidth < 900 ? 420 : 780),
        autosize: true,
        title: {
          text: composeChartTitle('涨跌幅分布'),
          x: 0.02,
          xanchor: 'left',
          font: { size: 18, color: '#0d355c' },
        },
        paper_bgcolor: '#d7e7ff',
        plot_bgcolor: '#d7e7ff',
        font: { size: 15, color: '#0d355c' },
        margin: { l: 62, r: 24, t: 74, b: 72 },
        showlegend: false,
        bargap: 0.1,
        xaxis: {
          dtick: distributionAxis.dtick,
          range: distributionAxis.range,
          title: '涨跌幅',
          tickfont: { size: 12 },
          showgrid: false,
        },
        yaxis: {
          title: '分布数量',
          gridcolor: 'rgba(255, 255, 255, 0.6)',
        },
      }
    }

    function buildGroupTrace(items) {
      return [
        {
          type: 'bar',
          x: items.map((item) => item.group),
          y: items.map((item) => item.chgMean * 100),
          marker: { color: items.map(resolveGroupBarColor) },
          hovertemplate: '分组: %{x}<br>涨跌幅: %{y:.2f}%<extra></extra>',
        },
      ]
    }

    function resolveDistributionAxis() {
      if (viewScope.value === 'daily') {
        return {
          dtick: 1,
          range: [-21.5, 21.5],
        }
      }

      const nonZeroBins = chartState.distribution
        .filter((item) => item.value > 0)
        .map((item) => item.bin)

      if (!nonZeroBins.length) {
        return {
          dtick: 5,
          range: [-10.5, 10.5],
        }
      }

      const minBin = Math.min(...nonZeroBins)
      const maxBin = Math.max(...nonZeroBins)
      const padding = 2
      const minRange = Math.max(-100.5, minBin - padding)
      const maxRange = Math.min(100.5, maxBin + padding)
      const span = maxRange - minRange
      const dtick = span <= 20 ? 2 : span <= 50 ? 5 : 10

      return {
        dtick,
        range: [minRange, maxRange],
      }
    }

    function buildDistributionTrace() {
      return [
        {
          type: 'bar',
          x: chartState.distribution.map((item) => item.bin),
          y: chartState.distribution.map((item) => item.value),
          marker: { color: chartState.distribution.map(resolveDistributionBarColor) },
          hovertemplate: '涨跌幅: %{x}%<br>数量: %{y}<extra></extra>',
        },
      ]
    }

    async function renderCharts() {
      await nextTick()
      const marketTarget = document.getElementById('market-chart')
      const industryTarget = document.getElementById('industry-chart')
      const distributionTarget = document.getElementById('distribution-chart')
      if (!marketTarget || !industryTarget || !distributionTarget) {
        return
      }
      Plotly.react(marketTarget, buildGroupTrace(chartState.marketGroups), buildGroupLayout('按市值分组', 'market-chart', {
        tickmode: 'array',
        tickvals: ['1', '30'],
        ticktext: ['大', '小'],
      }), {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
      })
      Plotly.react(industryTarget, buildGroupTrace(chartState.industryGroups), buildGroupLayout('按行业分组', 'industry-chart'), {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
      })
      Plotly.react(distributionTarget, buildDistributionTrace(), buildDistributionLayout(), {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
      })
    }

    async function readJsonWithFallback(url, fallbackUrl = '') {
      const response = await fetch(url)
      const contentType = response.headers.get('content-type') || ''
      if (!response.ok) {
        let message = `请求失败: ${response.status}`
        try {
          const payload = await response.json()
          message = payload.error || message
        } catch (_) {
          // Keep the fallback message when the response is not JSON.
        }
        throw new Error(message)
      }

      if (!contentType.includes('application/json')) {
        if (fallbackUrl) {
          const fallbackResponse = await fetch(fallbackUrl)
          if (!fallbackResponse.ok) {
            throw new Error('本地静态数据加载失败')
          }
          return await fallbackResponse.json()
        }
        throw new Error('返回结果不是 JSON')
      }

      return await response.json()
    }

    function buildRangeStatusText(period) {
      return `${period.modeLabel}：${period.startDate} 至 ${period.endDate}，交易日 ${period.tradeDays} 天`
    }

    async function updatePayload(payload, scope) {
      viewScope.value = scope
      tradeDate.value = payload.tradeDate || ''
      if (scope === 'range' && payload.period) {
        statusTitle.value = '当前区间'
        statusText.value = buildRangeStatusText(payload.period)
        chartCaption.value = statusText.value
        startDate.value = payload.period.startDate || payload.tradeDate || ''
        endDate.value = payload.period.endDate || payload.tradeDate || ''
      } else {
        statusTitle.value = '当前交易日'
        statusText.value = payload.tradeDate || '-'
        chartCaption.value = payload.tradeDate ? `交易日：${payload.tradeDate}` : ''
        startDate.value = payload.tradeDate || ''
        endDate.value = payload.tradeDate || ''
      }
      summary.positive = payload.summary.positive
      summary.negative = payload.summary.negative
      summary.zero = payload.summary.zero
      summary.total = payload.summary.total
      chartState.marketGroups = payload.marketGroups
      chartState.industryGroups = payload.industryGroups || []
      chartState.distribution = payload.distribution
      await renderCharts()
    }

    async function loadDaily(dateValue = 'latest') {
      loading.value = true
      error.value = ''
      try {
        const fallbackDate = dateValue === 'latest' ? '2025-12-31' : dateValue
        const fallbackUrl = `/data/daily-${fallbackDate}.json`
        const payload = await readJsonWithFallback(
          `/api/daily?date=${encodeURIComponent(dateValue)}`,
          fallbackUrl
        )
        await updatePayload(payload, 'daily')
      } catch (err) {
        error.value = err instanceof Error ? err.message : '数据加载失败'
      } finally {
        loading.value = false
      }
    }

    async function loadRange(params) {
      loading.value = true
      error.value = ''
      try {
        const query = new URLSearchParams(params).toString()
        const payload = await readJsonWithFallback(`/api/range?${query}`)
        await updatePayload(payload, 'range')
      } catch (err) {
        error.value = err instanceof Error ? err.message : '数据加载失败'
      } finally {
        loading.value = false
      }
    }

    async function refreshRange() {
      if (!startDate.value || !endDate.value) {
        error.value = '请选择开始时间和结束时间'
        return
      }
      await loadRange({
        start: startDate.value,
        end: endDate.value,
      })
    }

    async function loadLatest() {
      await loadDaily('latest')
    }

    async function loadRangePreset(preset) {
      await loadRange({ preset })
    }

    function handleResize() {
      renderCharts()
    }

    onMounted(() => {
      loadDaily('latest')
      window.addEventListener('resize', handleResize)
    })

    return {
      loading,
      error,
      startDate,
      endDate,
      summary,
      statusTitle,
      statusText,
      refreshRange,
      loadLatest,
      loadRangePreset,
    }
  },
}).mount('#app')
