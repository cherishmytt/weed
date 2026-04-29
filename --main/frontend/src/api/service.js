import http from './http'

export const authApi = {
  register: (data) => http.post('/auth/register', data),
  login: (data) => http.post('/auth/login', data),
  profile: () => http.get('/auth/profile'),
  changePassword: (data) => http.post('/auth/change-password', data),
}

export const userApi = {
  list: () => http.get('/users'),
  create: (data) => http.post('/users', data),
  update: (id, data) => http.put(`/users/${id}`, data),
  remove: (id) => http.delete(`/users/${id}`),
}

export const importApi = {
  batches: () => http.get('/import/batches'),
  uploadFireCsv: (formData) =>
    http.post('/import/fire-csv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  uploadCountryBoundary: (formData) =>
    http.post('/import/country-boundary', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  removeBatch: (id) => http.delete(`/import/batches/${id}`),
}

export const fireApi = {
  filterOptions: () => http.get('/fire/filter-options'),
  list: (params) => http.get('/fire/list', { params }),
  latest: (params) => http.get('/fire/latest', { params }),
  range: (params) => http.get('/fire/range', { params }),
  bbox: (params) => http.get('/fire/bbox', { params }),
  detail: (id) => http.get(`/fire/${id}`),
  related: (id) => http.get(`/fire/${id}/related`),
  remove: (id) => http.delete(`/fire/${id}`),
  exportUrl: (params) => {
    const query = new URLSearchParams(
      Object.entries(params || {}).filter(([, value]) => value !== '' && value != null),
    ).toString()
    const token = localStorage.getItem('fire-token')
    const base = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'
    return `${base}/fire/export?${query}${query ? '&' : ''}token=${token || ''}`
  },
}

export const analysisApi = {
  bundle: (params, config = {}) => http.get('/analysis/bundle', { params, ...config }),
  overview: (params, config = {}) => http.get('/analysis/overview', { params, ...config }),
  timeline: (params, config = {}) => http.get('/analysis/timeline', { params, ...config }),
  countryTop: (params, config = {}) => http.get('/analysis/country-top', { params, ...config }),
  countryBundle: (params, config = {}) => http.get('/analysis/country-bundle', { params, ...config }),
  countryTrend: (params, config = {}) => http.get('/analysis/country-trend', { params, ...config }),
  countryFrpDistribution: (params, config = {}) => http.get('/analysis/country-frp-distribution', { params, ...config }),
  countryDaynightPie: (params, config = {}) => http.get('/analysis/country-daynight-pie', { params, ...config }),
  countrySourceProductPie: (params, config = {}) => http.get('/analysis/country-source-product-pie', { params, ...config }),
  satellitePie: (params, config = {}) => http.get('/analysis/satellite-pie', { params, ...config }),
  sourceProductPie: (params, config = {}) => http.get('/analysis/source-product-pie', { params, ...config }),
  daynightPie: (params, config = {}) => http.get('/analysis/daynight-pie', { params, ...config }),
  frpDistribution: (params, config = {}) => http.get('/analysis/frp-distribution', { params, ...config }),
  countryChoropleth: (params, config = {}) => http.get('/analysis/country-choropleth', { params, ...config }),
  countryDetail: (params, config = {}) => http.get('/analysis/country-detail', { params, ...config }),
}

export const weatherApi = {
  point: (params, config = {}) => http.get('/weather/point', { params, ...config }),
  hotspotCenter: (hotspotId, config = {}) => http.get('/weather/hotspot-center', { params: { hotspotId }, ...config }),
}

export const hotspotApi = {
  list: (params) => http.get('/hotspots/list', { params }),
  top: (params) => http.get('/hotspots/top', { params }),
  detail: (id, params) => http.get(`/hotspots/${id}`, { params }),
}

export const dashboardApi = {
  summary: (params) => http.get('/dashboard/summary', { params }),
  hotspots: (params) => http.get('/dashboard/hotspots', { params }),
  rankings: (params) => http.get('/dashboard/rankings', { params }),
  trends: (params) => http.get('/dashboard/trends', { params }),
  cruisePoints: (params) => http.get('/dashboard/cruise-points', { params }),
}

export const syncApi = {
  estimate: (data) => http.post('/sync/estimate', data),
  runNow: (data) => http.post('/sync/run-now', data),
  status: (params, config = {}) => http.get('/sync/status', { params, ...config }),
  history: (params) => http.get('/sync/history', { params }),
}
