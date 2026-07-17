export type Metric = 'IC' | 'IR'

export interface ChartMeta {
  id: string
  kicker: string
  title: string
  subtitle: string
  dateRangeLabel?: string
}

export interface ChartRow {
  label: string
  IC?: number
  IR?: number
}

export interface ChartDataResponse {
  id: string
  rows: ChartRow[]
  updatedAt?: string | null
  availableMetrics: Metric[]
}

export type PanelStatus = 'idle' | 'loading' | 'success' | 'error'

export interface ChartPanelState {
  meta: ChartMeta
  status: PanelStatus
  rows: ChartRow[]
  availableMetrics: Metric[]
  updatedAt?: string | null
  error?: string
}
