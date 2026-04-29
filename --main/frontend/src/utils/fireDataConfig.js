import dayjs from 'dayjs'

export const AREA_PRESETS = {
  world: { label: '全球', view: 'world' },
  seasia: { label: '东南亚', view: 'seasia' },
  australia: { label: '澳大利亚', view: 'australia' },
  south_america: { label: '南美', view: 'south_america' },
}

export const SOURCE_PRODUCT_PRESETS = {
  VIIRS_NOAA20_NRT: { label: 'NOAA-20' },
  VIIRS_SNPP_NRT: { label: 'S-NPP' },
}

export const TIME_PRESET_OPTIONS = [
  { label: '最近1天', value: '1d' },
  { label: '最近7天', value: '7d' },
  { label: '最近30天', value: '30d' },
  { label: '自定义', value: 'custom' },
]

export const HOTSPOT_WINDOW_MAP = {
  '1d': '24h',
  '7d': '7d',
  '30d': '30d',
  custom: '30d',
}

export const normalizeOptionList = (values = [], presetMap = {}) => {
  const presetEntries = Object.entries(presetMap)
  const dynamicValues = Array.isArray(values) ? values.filter(Boolean) : []
  const merged = new Set([...presetEntries.map(([value]) => value), ...dynamicValues])
  return Array.from(merged).map((value) => ({
    value,
    label: presetMap[value]?.label || value,
  }))
}

export const resolveAreaView = (areaLabel) => AREA_PRESETS[areaLabel]?.view || 'world'

export const buildDateParams = ({
  preset = '7d',
  customRange = [],
  latestReference = dayjs(),
} = {}) => {
  const anchor = dayjs(latestReference || dayjs())
  if (preset === 'custom' && customRange?.length === 2) {
    const start = dayjs(customRange[0]).startOf('day')
    const end = dayjs(customRange[1]).endOf('day')
    return {
      start_date: start.format('YYYY-MM-DD'),
      end_date: end.format('YYYY-MM-DD'),
      start: start.toISOString(),
      end: end.toISOString(),
      days: Math.max(end.startOf('day').diff(start.startOf('day'), 'day') + 1, 1),
      window: HOTSPOT_WINDOW_MAP.custom,
    }
  }

  const days = preset === '30d' ? 30 : preset === '1d' ? 1 : 7
  const start = anchor.subtract(days - 1, 'day').startOf('day')
  const end = anchor.endOf('day')
  return {
    start_date: start.format('YYYY-MM-DD'),
    end_date: end.format('YYYY-MM-DD'),
    start: start.toISOString(),
    end: end.toISOString(),
    days,
    window: HOTSPOT_WINDOW_MAP[preset] || '7d',
  }
}
