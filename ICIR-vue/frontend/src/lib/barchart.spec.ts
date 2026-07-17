import { describe, expect, it } from 'vitest'
import { buildSeriesData, collectAvailableYears, filterRowsByYear, parseYearMonthLabel, pickPreferredMetric, shouldShowChart4YearTick } from './barchart'
import type { ChartRow } from '@/types/chart'

const rows: ChartRow[] = [
  {
    label: '机械',
    IC: 0.0884,
    IR: 0.7741,
  },
  {
    label: '电子',
    IC: 0.0598,
    IR: 0.5597,
  },
]

describe('barchart helpers', () => {
  it('按当前指标提取序列数值', () => {
    expect(buildSeriesData(rows, 'IC')).toEqual([0.0884, 0.0598])
    expect(buildSeriesData(rows, 'IR')).toEqual([0.7741, 0.5597])
  })

  it('优先使用 IR 作为默认指标', () => {
    expect(pickPreferredMetric([rows])).toBe('IR')
  })

  it('当所有数据都没有 IR 时回退到 IC', () => {
    expect(
      pickPreferredMetric([
        [
          {
            label: '占位',
            IC: 0.12,
            IR: Number.NaN,
          },
        ],
      ])
    ).toBe('IC')
  })

  it('能从日期标签里解析年份和月份', () => {
    expect(parseYearMonthLabel('2025-07-31')).toEqual({
      year: '2025',
      month: '07',
    })
    expect(parseYearMonthLabel('机械')).toBeNull()
  })

  it('能提取可选年份并按新到旧排序', () => {
    expect(
      collectAvailableYears([
        { label: '2024-01-31', IC: 1 },
        { label: '2025-03-31', IC: 2 },
        { label: '2024-02-29', IC: 3 },
      ])
    ).toEqual(['2025', '2024'])
  })

  it('能按年份筛选并把横轴标签转换成月份', () => {
    expect(
      filterRowsByYear(
        [
          { label: '2024-01-31', IC: 1.1 },
          { label: '2024-02-29', IC: 2.2 },
          { label: '2025-01-31', IC: 3.3 },
        ],
        '2024'
      )
    ).toEqual([
      { label: '01月', IC: 1.1 },
      { label: '02月', IC: 2.2 },
    ])
  })

  it('月度图只在每年第一次出现时显示年份标签', () => {
    const monthlyRows: ChartRow[] = [
      { label: '2011-01-31', IR: 1.1 },
      { label: '2011-02-28', IR: 1.2 },
      { label: '2012-01-31', IR: 1.3 },
      { label: '2026-03-31', IR: 1.4 },
    ]

    expect(shouldShowChart4YearTick(monthlyRows, 0)).toBe(true)
    expect(shouldShowChart4YearTick(monthlyRows, 1)).toBe(false)
    expect(shouldShowChart4YearTick(monthlyRows, 2)).toBe(true)
    expect(shouldShowChart4YearTick(monthlyRows, 3)).toBe(true)
  })
})
