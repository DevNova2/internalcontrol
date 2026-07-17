import { describe, expect, it } from 'vitest'
import { buildVisibleSeries, type HaochiDataset } from './chart'

const dataset: HaochiDataset = {
  dates: ['2024-01-01', '2024-01-02', '2024-01-03'],
  data: {
    A: [1, 2, 3],
    B: [null, 5, 6],
  },
}

describe('buildVisibleSeries', () => {
  it('只显示当前索引之前的数据', () => {
    const series = buildVisibleSeries(dataset, 1)
    expect(series[0].data).toEqual([1, 2, null])
  })

  it('保留前导 null，确保产品不会提前出现', () => {
    const series = buildVisibleSeries(dataset, 2)
    expect(series[1].data).toEqual([null, 5, 6])
  })
})
