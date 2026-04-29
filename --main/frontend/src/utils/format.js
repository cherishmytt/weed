import dayjs from 'dayjs'

export const formatDateTime = (value, pattern = 'YYYY-MM-DD HH:mm') =>
  value ? dayjs(value).format(pattern) : '--'

export const formatNumber = (value) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '--'
  return Number(value).toLocaleString('zh-CN')
}

export const confidenceLabel = (value) => {
  if (!value) return '--'
  const lower = String(value).toLowerCase()
  if (lower === 'h') return '高'
  if (lower === 'n') return '中'
  if (lower === 'l') return '低'
  return value
}
