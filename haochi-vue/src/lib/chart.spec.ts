import { describe, expect, it } from 'vitest'
import { buildVisibleSeries, type HaochiDataset } from './chart'

const dataset: HaochiDataset = {
  dates: ['2024-01-01', '2024-01-02', '2024-01-03'],
  data: {
    进取一号单位净值: [1, 2, 3],
    万得全a指数: [null, 5, 6],
    进取二号单位净值: [9, 9, 9],
  },
}

describe('buildVisibleSeries', () => {
  it('只返回需要展示的两条曲线', () => {
    const series = buildVisibleSeries(dataset, 2)
    expect(series.map((item) => item.name)).toEqual(['进取一号单位净值', '万得全a指数'])
  })

  it('只显示当前索引之前的数据', () => {
    const series = buildVisibleSeries(dataset, 1)
    expect(series[0].data).toEqual([1, 2, null])
  })

  it('保留前导 null，确保产品不会提前出现', () => {
    const series = buildVisibleSeries(dataset, 2)
    expect(series[1].data).toEqual([null, 5, 6])
  })
})
