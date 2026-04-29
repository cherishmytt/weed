<template>
  <div class="page-shell country-analysis-page">
    <LoadingEstimateOverlay
      :visible="loading && !hasCachedData"
      title="正在加载中"
      :description="loadingEstimateText"
    />

    <GlassPanel title="筛选" compact>
      <div class="filters">
        <el-segmented v-model="filters.timePreset" :options="timePresetOptions" />
        <el-date-picker
          v-if="filters.timePreset === 'custom'"
          v-model="filters.customRange"
          type="daterange"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
        />
        <el-select v-model="filters.area_label" clearable placeholder="区域">
          <el-option v-for="item in areaOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="filters.source_product" clearable placeholder="数据源">
          <el-option v-for="item in sourceProductOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="filters.country" clearable filterable placeholder="国家">
          <el-option v-for="item in countryOptions" :key="item" :label="item" :value="item" />
        </el-select>
        <div class="filter-actions">
          <el-button type="primary" @click="applyFilters">应用</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </div>
      </div>
    </GlassPanel>

    <el-alert
      v-if="requestError"
      :title="requestError"
      type="warning"
      show-icon
      :closable="false"
      class="state-alert"
    />

    <div class="viewport-wrap">
      <section class="viewport-panel hero-panel" :class="{ hidden: viewMode === 'detail' }">
        <div class="main-grid">
          <div class="left-column">
            <GlassPanel title="国家排行" :loading="baseLoading" loading-text="国家排行加载中">
              <BaseChart
                :option="countryTopOption"
                :height="340"
                :loading="baseLoading"
                loading-text="国家排行加载中"
                @chart-click="handleCountryChartClick"
              />
            </GlassPanel>
          </div>

          <GlassPanel
            title="国家专题图"
            class="map-panel"
            :loading="baseLoading || !worldMapReady"
            loading-text="专题图加载中"
          >
            <template #extra>
              <el-button text type="primary" @click="mapDialogVisible = true">放大</el-button>
            </template>
            <BaseChart
              v-if="worldMapReady"
              :option="worldMapOption"
              :height="560"
              :loading="baseLoading"
              loading-text="专题图加载中"
              @chart-click="handleMapClick"
            />
          </GlassPanel>

          <div class="right-column">
            <GlassPanel title="当前国家" :loading="detailLoading" loading-text="国家摘要加载中">
              <div v-if="countryDetail" class="country-summary">
                <div class="summary-item">
                  <span>国家</span>
                  <strong>{{ countryDetail.country_name }}</strong>
                </div>
                <div class="summary-item">
                  <span>火点总数</span>
                  <strong>{{ formatNumber(countryDetail.total_fire_points) }}</strong>
                </div>
                <div class="summary-item">
                  <span>高置信度</span>
                  <strong>{{ formatNumber(countryDetail.high_confidence_fire_points) }}</strong>
                </div>
                <div class="summary-item">
                  <span>夜间火点</span>
                  <strong>{{ formatNumber(countryDetail.night_fire_points) }}</strong>
                </div>
                <div class="summary-item">
                  <span>最大 FRP</span>
                  <strong>{{ formatMetric(countryDetail.max_frp) }}</strong>
                </div>
                <div class="summary-item">
                  <span>平均 FRP</span>
                  <strong>{{ formatMetric(countryDetail.avg_frp) }}</strong>
                </div>
                <div class="summary-item">
                  <span>最新更新</span>
                  <strong>{{ formatDateTime(countryDetail.latest_update, 'MM-DD HH:mm') }}</strong>
                </div>
                <div class="summary-item">
                  <span>主力卫星</span>
                  <strong>{{ countryDetail.satellites?.[0]?.name || '--' }}</strong>
                </div>
              </div>
              <el-empty v-else :description="currentCountryEmptyText" />
            </GlassPanel>

          </div>
        </div>

        <button class="view-toggle down" @click="viewMode = 'detail'">
          <el-icon><ArrowDownBold /></el-icon>
          <span>下探分析</span>
        </button>
      </section>

      <section class="viewport-panel detail-panel" :class="{ hidden: viewMode === 'map' }">
        <div class="detail-grid">
          <GlassPanel :title="trendTitle" :loading="detailLoading" loading-text="趋势加载中">
            <BaseChart
              v-if="viewMode === 'detail' && countryTrend.length"
              :key="`trend-${filters.country}-${dateParams.days}`"
              :option="countryTrendOption"
              :height="340"
              :loading="detailLoading"
              loading-text="趋势加载中"
            />
            <el-empty v-else :description="countryTrendEmptyText" />
          </GlassPanel>

          <GlassPanel title="FRP 分布" :loading="detailLoading" loading-text="FRP 分布加载中">
            <BaseChart
              v-if="viewMode === 'detail' && countryFrpDistribution.length"
              :key="`frp-${filters.country}-${dateParams.days}`"
              :option="countryFrpOption"
              :height="340"
              :loading="detailLoading"
              loading-text="FRP 分布加载中"
            />
            <el-empty v-else :description="countryFrpEmptyText" />
          </GlassPanel>

        </div>

        <button class="view-toggle up" @click="viewMode = 'map'">
          <el-icon><ArrowUpBold /></el-icon>
          <span>返回地图</span>
        </button>
      </section>
    </div>

    <el-dialog v-model="mapDialogVisible" title="国家专题图" width="72vw" top="6vh" destroy-on-close>
      <BaseChart
        v-if="worldMapReady"
        :option="worldMapOption"
        :height="720"
        :loading="baseLoading"
        loading-text="专题图加载中"
        @chart-click="handleMapClick"
      />
    </el-dialog>
  </div>
</template>

<script setup>
import dayjs from 'dayjs'
import * as echarts from 'echarts'
import { computed, onActivated, onMounted, reactive, ref } from 'vue'

import { analysisApi, fireApi } from '@/api/service'
import BaseChart from '@/components/BaseChart.vue'
import GlassPanel from '@/components/GlassPanel.vue'
import LoadingEstimateOverlay from '@/components/LoadingEstimateOverlay.vue'
import { useUiStore } from '@/stores/ui'
import { AREA_PRESETS, SOURCE_PRODUCT_PRESETS, TIME_PRESET_OPTIONS, buildDateParams, normalizeOptionList } from '@/utils/fireDataConfig'
import { formatDateTime, formatNumber } from '@/utils/format'
import { makeCacheKey, readViewCache, writeViewCache } from '@/utils/viewCache'

const WORLD_MAP_NAME = 'country-analysis-world-map'
const WORLD_MAP_DATA_CACHE_KEY = '__global_fire_world_geojson__'
const WORLD_MAP_DATA_LOADING_KEY = '__global_fire_world_geojson_loading__'
const FILTER_OPTIONS_NAMESPACE = 'country-analysis-filter-options'
const BASE_CACHE_NAMESPACE = 'country-analysis-base'
const DETAIL_CACHE_NAMESPACE = 'country-analysis-detail'
const CACHE_TTL_MS = 12 * 60 * 1000

const uiStore = useUiStore()

const ensureWorldMap = async () => {
  if (echarts.getMap(WORLD_MAP_NAME)) {
    worldMapReady.value = true
    return
  }
  const runtime = globalThis
  if (!runtime[WORLD_MAP_DATA_LOADING_KEY]) {
    runtime[WORLD_MAP_DATA_LOADING_KEY] = (async () => {
      const rawWorld =
        runtime[WORLD_MAP_DATA_CACHE_KEY] ||
        (await fetch('/data/world-countries-lite.json').then((response) => response.json()))
      const normalizedWorld = {
        ...rawWorld,
        features: (rawWorld.features || []).map((feature) => ({
          ...feature,
          properties: {
            ...(feature.properties || {}),
            name:
              feature.properties?.NAME_ZH ||
              feature.properties?.ADMIN ||
              feature.properties?.NAME ||
              feature.properties?.NAME_LONG ||
              feature.properties?.name ||
              '',
          },
        })),
      }

      runtime[WORLD_MAP_DATA_CACHE_KEY] = normalizedWorld
      return normalizedWorld
    })().finally(() => {
      runtime[WORLD_MAP_DATA_LOADING_KEY] = null
    })
  }

  const normalizedWorld = runtime[WORLD_MAP_DATA_CACHE_KEY] || (await runtime[WORLD_MAP_DATA_LOADING_KEY])
  if (!echarts.getMap(WORLD_MAP_NAME)) {
    echarts.registerMap(WORLD_MAP_NAME, normalizedWorld)
  }
  worldMapReady.value = true
}

const filters = reactive({
  timePreset: '7d',
  customRange: [],
  area_label: 'world',
  source_product: '',
  country: '',
})

const filterOptions = ref({
  area_labels: [],
  source_products: [],
  date_max: null,
})
const latestReference = ref(dayjs())
const loading = ref(false)
const hasCachedData = ref(false)
const requestError = ref('')
const viewMode = ref('map')
const mapDialogVisible = ref(false)
const worldMapReady = ref(Boolean(echarts.getMap(WORLD_MAP_NAME)))
const baseLoading = ref(false)
const detailLoading = ref(false)
let baseRequestId = 0
let detailRequestId = 0

const choropleth = ref([])
const countryTop = ref([])
const countryDetail = ref(null)
const countryTrend = ref([])
const countryFrpDistribution = ref([])

const timePresetOptions = TIME_PRESET_OPTIONS
const areaOptions = computed(() => normalizeOptionList(filterOptions.value.area_labels, AREA_PRESETS))
const sourceProductOptions = computed(() => [
  { value: '', label: '全部数据源' },
  ...normalizeOptionList(filterOptions.value.source_products, SOURCE_PRODUCT_PRESETS),
])
const countryOptions = computed(() => {
  const fromChoropleth = choropleth.value.map((item) => item.name).filter(Boolean)
  const fromTop = countryTop.value.map((item) => item.name).filter(Boolean)
  return Array.from(new Set([...fromTop, ...fromChoropleth])).sort((a, b) => a.localeCompare(b, 'zh-Hans-CN'))
})

const dateParams = computed(() =>
  buildDateParams({
    preset: filters.timePreset,
    customRange: filters.customRange,
    latestReference: latestReference.value,
  }),
)

const baseParams = computed(() => ({
  start_date: dateParams.value.start_date,
  end_date: dateParams.value.end_date,
  area_label: filters.area_label || undefined,
  source_product: filters.source_product || undefined,
}))

const trendTitle = computed(() => `${filters.country || '当前国家'}趋势（${dateParams.value.days}天）`)
const currentCountryEmptyText = computed(() => requestError.value || (filters.country ? '当前国家暂无概览数据' : '请选择国家'))
const countryTrendEmptyText = computed(() => requestError.value || '当前国家暂无趋势数据')
const countryFrpEmptyText = computed(() => requestError.value || '当前国家暂无 FRP 分布')
const loadingEstimateText = computed(() => {
  if (filters.area_label === 'world' && dateParams.value.days >= 30) return '预计 6-12 秒'
  if (filters.area_label === 'world') return '预计 5-9 秒'
  if (dateParams.value.days >= 30) return '预计 4-8 秒'
  return '预计 3-6 秒'
})

const themeToken = (token, fallback) => {
  uiStore.themeMode
  if (typeof window === 'undefined') return fallback
  return getComputedStyle(document.documentElement).getPropertyValue(token).trim() || fallback
}

const chartPalette = computed(() => ({
  textPrimary: themeToken('--text-primary', '#edf5ff'),
  textSecondary: themeToken('--text-secondary', 'rgba(221,232,255,0.64)'),
  accentCyan: themeToken('--accent-cyan', '#59d6ff'),
  accentBlue: themeToken('--accent-blue', '#2f73ff'),
  accentOrange: themeToken('--accent-orange', '#ff8d43'),
  gridLine: uiStore.themeMode === 'light' ? 'rgba(37, 102, 186, 0.1)' : 'rgba(99,195,255,0.08)',
  axisLine: uiStore.themeMode === 'light' ? 'rgba(37, 102, 186, 0.16)' : 'rgba(99,195,255,0.18)',
  mapColors:
    uiStore.themeMode === 'light'
      ? ['#ecf4fb', '#cfe1f3', '#8db7df', '#d77027']
      : ['#17314a', '#266f94', '#f1a24a', '#ff6a3d'],
}))

const formatMetric = (value) => {
  const numeric = Number(value)
  return Number.isFinite(numeric) ? numeric.toFixed(2) : '--'
}

const withAlpha = (color, alpha = 1) => {
  if (!color) return `rgba(89, 214, 255, ${alpha})`
  if (color.startsWith('#')) {
    const hex = color.replace('#', '')
    const value = hex.length === 3 ? hex.split('').map((item) => item + item).join('') : hex
    const red = Number.parseInt(value.slice(0, 2), 16)
    const green = Number.parseInt(value.slice(2, 4), 16)
    const blue = Number.parseInt(value.slice(4, 6), 16)
    return `rgba(${red}, ${green}, ${blue}, ${alpha})`
  }
  return color
}

const countryTopOption = computed(() => ({
  textStyle: { color: chartPalette.value.textPrimary },
  grid: { left: 92, right: 18, top: 18, bottom: 18 },
  xAxis: {
    type: 'value',
    axisLabel: { color: chartPalette.value.textSecondary },
    splitLine: { lineStyle: { color: chartPalette.value.gridLine } },
  },
  yAxis: {
    type: 'category',
    data: countryTop.value.map((item) => item.name).reverse(),
    axisLabel: { color: chartPalette.value.textPrimary, fontSize: 11 },
  },
  series: [
    {
      type: 'bar',
      data: countryTop.value.map((item) => item.value).reverse(),
      itemStyle: {
        color: chartPalette.value.accentOrange,
        borderRadius: [0, 12, 12, 0],
      },
    },
  ],
}))

const worldMapOption = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'item',
    formatter: (params) => `${params.name || '未知国家'}<br/>火点数：${Number(params.value || 0) || 0}`,
  },
  visualMap: {
    min: 0,
    max: Math.max(...choropleth.value.map((item) => Number(item.value || 0)), 10),
    left: 10,
    bottom: 142,
    text: ['高', '低'],
    calculable: true,
    textStyle: { color: chartPalette.value.textPrimary },
    inRange: { color: chartPalette.value.mapColors },
  },
  series: [
    {
      type: 'map',
      map: WORLD_MAP_NAME,
      nameProperty: 'name',
      layoutCenter: ['51%', '45%'],
      layoutSize: '105%',
      roam: true,
      selectedMode: 'single',
      itemStyle: {
        areaColor: uiStore.themeMode === 'light' ? '#f1f6fb' : '#15324c',
        borderColor: uiStore.themeMode === 'light' ? '#7fa9cd' : '#4ca5d6',
        borderWidth: 0.8,
      },
      emphasis: {
        label: { color: '#fff' },
        itemStyle: { areaColor: chartPalette.value.accentOrange, borderColor: '#ffd5b6' },
      },
      select: {
        label: { color: '#fff' },
        itemStyle: { areaColor: chartPalette.value.accentOrange },
      },
      data: choropleth.value.map((item) => ({
        name: item.name,
        value: Number(item.value || 0),
        selected: item.name === filters.country,
      })),
    },
  ],
}))

const countryTrendOption = computed(() => ({
  textStyle: { color: chartPalette.value.textPrimary },
  grid: { left: 44, right: 18, top: 30, bottom: 28 },
  tooltip: { trigger: 'axis' },
  xAxis: {
    type: 'category',
    data: countryTrend.value.map((item) => item.date),
    axisLabel: { color: chartPalette.value.textSecondary },
    axisLine: { lineStyle: { color: chartPalette.value.axisLine } },
  },
  yAxis: {
    type: 'value',
    axisLabel: { color: chartPalette.value.textSecondary },
    splitLine: { lineStyle: { color: chartPalette.value.gridLine } },
  },
  series: [
    {
      type: 'line',
      smooth: true,
      data: countryTrend.value.map((item) => item.value),
      symbolSize: 7,
      lineStyle: { width: 3, color: chartPalette.value.accentCyan },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: withAlpha(chartPalette.value.accentCyan, 0.4) },
          { offset: 1, color: withAlpha(chartPalette.value.accentCyan, 0.05) },
        ]),
      },
    },
  ],
}))

const countryFrpOption = computed(() => ({
  textStyle: { color: chartPalette.value.textPrimary },
  grid: { left: 44, right: 18, top: 30, bottom: 28 },
  xAxis: {
    type: 'category',
    data: countryFrpDistribution.value.map((item) => item.name),
    axisLabel: { color: chartPalette.value.textSecondary },
    axisLine: { lineStyle: { color: chartPalette.value.axisLine } },
  },
  yAxis: {
    type: 'value',
    axisLabel: { color: chartPalette.value.textSecondary },
    splitLine: { lineStyle: { color: chartPalette.value.gridLine } },
  },
  series: [
    {
      type: 'bar',
      data: countryFrpDistribution.value.map((item) => item.value),
      itemStyle: {
        color: chartPalette.value.accentBlue,
        borderRadius: [10, 10, 0, 0],
      },
    },
  ],
}))

const loadFilterOptions = async () => {
  const cached = readViewCache(FILTER_OPTIONS_NAMESPACE, 'default', CACHE_TTL_MS)
  if (cached) {
    filterOptions.value = cached
    latestReference.value = cached.date_max ? dayjs(cached.date_max) : dayjs()
    return
  }
  const payload = await fireApi.filterOptions()
  filterOptions.value = payload
  latestReference.value = payload.date_max ? dayjs(payload.date_max) : dayjs()
  writeViewCache(FILTER_OPTIONS_NAMESPACE, 'default', payload)
}

const buildBaseCacheKey = () =>
  makeCacheKey({
    ...baseParams.value,
    days: dateParams.value.days,
  })

const buildCountryCacheKey = (country) =>
  makeCacheKey({
    country,
    ...baseParams.value,
    days: dateParams.value.days,
  })

const loadBaseData = async ({ force = false } = {}) => {
  const requestId = ++baseRequestId
  baseLoading.value = true
  const cacheKey = buildBaseCacheKey()
  const cached = !force ? readViewCache(BASE_CACHE_NAMESPACE, cacheKey, CACHE_TTL_MS) : null
  hasCachedData.value = Boolean(cached)
  if (cached) {
    requestError.value = ''
    choropleth.value = cached.choropleth || []
    countryTop.value = cached.countryTop || []
    filters.country = filters.country || cached.defaultCountry || countryTop.value[0]?.name || ''
    if (requestId === baseRequestId) {
      baseLoading.value = false
    }
    return
  }

  try {
    const params = baseParams.value
    const [countryTopResult, choroplethResult] = await Promise.allSettled([
      analysisApi.countryTop({ limit: 15, ...params }, { silent: true }),
      analysisApi.countryChoropleth({ metric: 'count', ...params }, { silent: true }),
    ])

    const nextCountryTop = countryTopResult.status === 'fulfilled' ? countryTopResult.value : countryTop.value
    const nextChoropleth = choroplethResult.status === 'fulfilled' ? choroplethResult.value : choropleth.value

    countryTop.value = nextCountryTop || []
    choropleth.value = nextChoropleth || []
    filters.country = filters.country || countryTop.value[0]?.name || choropleth.value[0]?.name || ''
    requestError.value =
      countryTop.value.length || choropleth.value.length ? '' : '国家排行与专题图加载失败，请稍后重试'

    if (countryTop.value.length || choropleth.value.length) {
      writeViewCache(BASE_CACHE_NAMESPACE, cacheKey, {
        choropleth: choropleth.value,
        countryTop: countryTop.value,
        defaultCountry: filters.country,
      })
      hasCachedData.value = true
    }
  } finally {
    if (requestId === baseRequestId) {
      baseLoading.value = false
    }
  }
}

const loadCountrySpecific = async ({ force = false } = {}) => {
  const requestId = ++detailRequestId
  if (!filters.country) {
    requestError.value = ''
    countryDetail.value = null
    countryTrend.value = []
    countryFrpDistribution.value = []
    detailLoading.value = false
    return
  }

  detailLoading.value = true
  const cacheKey = buildCountryCacheKey(filters.country)
  const cached = !force ? readViewCache(DETAIL_CACHE_NAMESPACE, cacheKey, CACHE_TTL_MS) : null
  const hasUsableCache =
    cached &&
    cached.detail &&
    Array.isArray(cached.trend) &&
    Array.isArray(cached.frpDistribution)
  if (hasUsableCache) {
    requestError.value = ''
    countryDetail.value = cached.detail
    countryTrend.value = cached.trend
    countryFrpDistribution.value = cached.frpDistribution
    if (requestId === detailRequestId) {
      detailLoading.value = false
    }
    return
  }

  const params = {
    country: filters.country,
    ...baseParams.value,
  }

  try {
    const payload = await analysisApi.countryBundle(
      {
        days: dateParams.value.days,
        ...params,
      },
      { silent: true },
    )
    requestError.value = ''
    countryDetail.value = payload.detail || null
    countryTrend.value = payload.trend || []
    countryFrpDistribution.value = payload.frpDistribution || []
    writeViewCache(DETAIL_CACHE_NAMESPACE, cacheKey, {
      detail: countryDetail.value,
      trend: countryTrend.value,
      frpDistribution: countryFrpDistribution.value,
    })
  } catch {
    requestError.value = '国家专题图表加载失败，请稍后重试'
  } finally {
    if (requestId === detailRequestId) {
      detailLoading.value = false
    }
  }
}

const applyFilters = async () => {
  loading.value = true
  try {
    await loadBaseData({ force: true })
    await loadCountrySpecific({ force: true })
  } finally {
    loading.value = false
  }
}

const resetFilters = async () => {
  filters.timePreset = '7d'
  filters.customRange = []
  filters.area_label = 'world'
  filters.source_product = ''
  filters.country = ''
  await applyFilters()
}

const handleCountrySelect = async (country) => {
  if (!country || country === filters.country) return
  filters.country = country
  loading.value = true
  try {
    await loadCountrySpecific()
  } finally {
    loading.value = false
  }
}

const handleCountryChartClick = async (params) => {
  await handleCountrySelect(params?.name)
}

const handleMapClick = async (params) => {
  await handleCountrySelect(params?.name)
}

const bootstrap = async () => {
  await Promise.all([ensureWorldMap(), loadFilterOptions()])
  loading.value = true
  try {
    await loadBaseData()
    await loadCountrySpecific()
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await bootstrap()
})

onActivated(async () => {
  if (!hasCachedData.value) {
    await bootstrap()
  }
})
</script>

<style scoped>
.country-analysis-page {
  position: relative;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  height: 100%;
  min-height: 0;
  padding-bottom: 8px;
  overflow: hidden;
}

.state-alert {
  margin-bottom: 12px;
}

.filters {
  display: grid;
  grid-template-columns: 1.25fr 1.1fr 1fr 1fr 1fr auto;
  gap: 12px;
}

.filter-actions {
  display: flex;
  gap: 10px;
}

.viewport-wrap {
  position: relative;
  min-height: 0;
  overflow: hidden;
}

.viewport-panel {
  position: absolute;
  inset: 0;
  display: grid;
  min-height: 0;
  transition: transform 0.32s ease, opacity 0.24s ease;
}

.viewport-panel.hidden {
  opacity: 0;
  pointer-events: none;
}

.hero-panel.hidden {
  transform: translateY(-6%);
}

.detail-panel.hidden {
  transform: translateY(6%);
}

.main-grid {
  display: grid;
  grid-template-columns: 240px minmax(0, 2.05fr) 240px;
  gap: 14px;
  min-height: 0;
}

.left-column,
.right-column {
  display: grid;
  gap: 14px;
  min-height: 0;
}

.map-panel :deep(.panel-body) {
  padding-top: 4px;
}

.country-summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.summary-item {
  padding: 12px 14px;
  border-radius: 16px;
  border: 1px solid var(--line-soft);
  background: var(--bg-elevated);
}

.summary-item span {
  color: var(--text-secondary);
}

.summary-item strong {
  display: block;
  margin-top: 8px;
}

.view-toggle {
  position: absolute;
  left: 50%;
  z-index: 3;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  color: var(--text-primary);
  border-radius: 999px;
  border: 1px solid var(--line-soft);
  background: rgba(6, 18, 30, 0.9);
  transform: translateX(-50%);
  cursor: pointer;
}

.view-toggle.down {
  bottom: 10px;
}

.view-toggle.up {
  top: 10px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  min-height: 0;
  padding-top: 44px;
}

@media (max-width: 1440px) {
  .filters,
  .main-grid,
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .country-analysis-page {
    height: auto;
    overflow: auto;
  }

  .viewport-panel {
    position: relative;
    inset: auto;
  }

  .view-toggle {
    position: static;
    transform: none;
    justify-self: center;
    margin-top: 12px;
  }
}
</style>
