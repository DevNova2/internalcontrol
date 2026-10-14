import type { EChartsOption, LineSeriesOption } from 'echarts'

export interface HaochiDataset {
  dates: string[]
  data: Record<string, Array<number | null>>
}

const palette = ['#D6B36D', '#89B6FF', '#8b0000', '#F0826B', '#F1DB8A', '#B79CFF']
const visibleSeriesNames = new Set(['进取一号单位净值', '万得全a指数'])

export function buildVisibleSeries(dataset: HaochiDataset, currentIndex: number): LineSeriesOption[] {
  const safeIndex = Math.max(0, Math.min(currentIndex, dataset.dates.length - 1))

  return Object.entries(dataset.data)
    .filter(([name]) => visibleSeriesNames.has(name))
    .map(([name, values], idx) => ({
      type: 'line',
      name,
      smooth: 0.25,
      showSymbol: false,
      connectNulls: false,
      sampling: 'lttb',
      lineStyle: {
        width: 2.5,
        color: palette[idx % palette.length],
        shadowBlur: 10,
        shadowColor: 'rgba(0, 0, 0, 0.15)',
      },
      emphasis: {
        focus: 'series',
      },
      data: values.map((value, valueIndex) => (valueIndex <= safeIndex ? value : null)),
    }))
}

export function buildChartOption(dataset: HaochiDataset, currentIndex: number): EChartsOption {
  const series = buildVisibleSeries(dataset, currentIndex)

  return {
    backgroundColor: 'transparent',
    animation: false,
    animationDuration: 0,
    animationDurationUpdate: 0,
    color: palette,
    grid: {
      left: 56,
      right: 42,
      top: 104,
      bottom: 56,
    },
    legend: {
      top: 24,
      left: 24,
      icon: 'roundRect',
      itemWidth: 28,
      itemHeight: 8,
      textStyle: {
        color: '#dbe8ff',
        fontSize: 13,
      },
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'line',
        lineStyle: {
          color: 'rgba(214, 179, 109, 0.55)',
          width: 1,
        },
      },
      backgroundColor: 'rgba(8, 18, 34, 0.94)',
      borderColor: 'rgba(214, 179, 109, 0.28)',
      textStyle: {
        color: '#eef5ff',
      },
      valueFormatter: (value) => (typeof value === 'number' ? value.toFixed(4) : '--'),
    },
    xAxis: {
      type: 'category',
      data: dataset.dates,
      boundaryGap: false,
      axisLabel: {
        color: 'rgba(227, 238, 255, 0.78)',
        hideOverlap: true,
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(255, 255, 255, 0.20)',
        },
      },
      axisTick: {
        show: false,
      },
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLabel: {
        color: 'rgba(227, 238, 255, 0.8)',
        formatter: (value: number) => value.toFixed(2),
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(255, 255, 255, 0.12)',
          type: 'dashed',
        },
      },
      axisLine: {
        show: false,
      },
    },
    series,
  }
}
