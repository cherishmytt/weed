<template>
  <div class="page-shell merged-analysis-page">
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
        <el-select v-model="filters.satellite" clearable placeholder="卫星">
          <el-option v-for="item in satelliteOptions" :key="item" :label="item" :value="item" />
        </el-select>
        <el-input v-model="filters.country" clearable placeholder="国家" />
        <div class="filter-actions">
          <el-button type="primary" @click="applyFilters">应用</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </div>
      </div>
    </GlassPanel>

    <section class="stat-grid">
      <StatCard label="火点总数" :value="formatNumber(overview.total_fire_points)" :loading="primaryLoading" icon="DataAnalysis" />
      <StatCard label="高置信度火点" :value="formatNumber(overview.high_confidence_fire_points)" :loading="primaryLoading" icon="WarningFilled" />
      <StatCard label="夜间火点" :value="formatNumber(overview.night_fire_points)" :loading="primaryLoading" icon="MoonNight" />
      <StatCard label="最大 FRP" :value="formatMetric(overview.max_frp)" :loading="primaryLoading" icon="Lightning" />
      <StatCard label="热点区域数" :value="formatNumber(hotspots.length)" :loading="hotspotsLoading" icon="LocationFilled" />
      <StatCard label="覆盖国家数" :value="formatNumber(choropleth.length)" :loading="primaryLoading" icon="OfficeBuilding" />
    </section>

    <section class="primary-grid">
      <GlassPanel :title="trendTitle" :loading="primaryLoading" loading-text="趋势加载中">
        <BaseChart :option="trendOption" :height="320" :loading="primaryLoading" loading-text="趋势加载中" />
      </GlassPanel>

      <GlassPanel title="国家火点 Top10" :loading="primaryLoading" loading-text="排行加载中">
        <BaseChart
          :option="countryTopOption"
          :height="320"
          :loading="primaryLoading"
          loading-text="排行加载中"
          @chart-click="handleCountryChartClick"
        />
      </GlassPanel>
    </section>

    <section class="secondary-grid">
      <GlassPanel title="国家专题图" class="map-panel" :loading="primaryLoading || !worldMapReady" loading-text="专题图加载中">
        <BaseChart
          v-if="worldMapReady"
          :option="worldMapOption"
          :height="420"
          :loading="primaryLoading"
          loading-text="专题图加载中"
          @chart-click="handleMapClick"
        />
      </GlassPanel>

      <div class="structure-column">
        <GlassPanel title="数据源占比" :loading="secondaryLoading" loading-text="占比加载中">
          <BaseChart :option="sourceProductOption" :height="196" :loading="secondaryLoading" loading-text="占比加载中" />
        </GlassPanel>

        <GlassPanel title="昼夜占比" :loading="secondaryLoading" loading-text="占比加载中">
          <BaseChart :option="daynightOption" :height="196" :loading="secondaryLoading" loading-text="占比加载中" />
        </GlassPanel>

      </div>
    </section>

    <section class="supplement-grid">
      <GlassPanel title="热点区域摘要" scrollable class="balanced-panel" :loading="hotspotsLoading" loading-text="热点摘要加载中">
        <div v-if="hotspots.length" class="hotspot-list">
          <article v-for="item in hotspots" :key="item.id" class="hotspot-item">
            <div class="hotspot-head">
              <strong>{{ item.major_country || item.id }}</strong>
              <span>{{ formatNumber(item.fire_count) }} 个火点</span>
            </div>
            <div class="hotspot-meta">
              <span>平均 FRP {{ formatMetric(item.avg_frp) }}</span>
              <span>最大 FRP {{ formatMetric(item.max_frp) }}</span>
            </div>
            <div class="hotspot-meta">
              <span>{{ formatDateTime(item.time_start, 'MM-DD HH:mm') }}</span>
              <span>{{ formatDateTime(item.time_end, 'MM-DD HH:mm') }}</span>
            </div>
          </article>
        </div>
        <el-empty v-else description="当前条件下暂无热点摘要" />
      </GlassPanel>

      <GlassPanel
        title="当前结果摘要"
        scrollable
        class="balanced-panel"
        :loading="primaryLoading || focusedCountryLoading || hotspotsLoading"
        loading-text="摘要加载中"
      >
        <div class="summary-list">
          <article v-for="item in summaryItems" :key="item.label">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </article>
        </div>
      </GlassPanel>
    </section>
  </div>
</template>

<script setup>
import dayjs from 'dayjs'
import * as echarts from 'echarts'
import { computed, onActivated, onMounted, reactive, ref } from 'vue'

import { analysisApi, fireApi, hotspotApi } from '@/api/service'
import BaseChart from '@/components/BaseChart.vue'
import GlassPanel from '@/components/GlassPanel.vue'
import LoadingEstimateOverlay from '@/components/LoadingEstimateOverlay.vue'
import StatCard from '@/components/StatCard.vue'
import { useUiStore } from '@/stores/ui'
import { AREA_PRESETS, SOURCE_PRODUCT_PRESETS, TIME_PRESET_OPTIONS, buildDateParams, normalizeOptionList } from '@/utils/fireDataConfig'
import { formatDateTime, formatNumber } from '@/utils/format'
import { makeCacheKey, readViewCache, writeViewCache } from '@/utils/viewCache'

const WORLD_MAP_NAME = 'merged-analysis-world-map'
const WORLD_MAP_DATA_CACHE_KEY = '__global_fire_world_geojson__'
const WORLD_MAP_DATA_LOADING_KEY = '__global_fire_world_geojson_loading__'
const FILTER_CACHE_KEY = 'analysis-merged-filters'
const PRIMARY_CACHE_NAMESPACE = 'analysis-merged-primary'
const SECONDARY_CACHE_NAMESPACE = 'analysis-merged-secondary'
const COUNTRY_CACHE_NAMESPACE = 'analysis-merged-country'
const HOTSPOT_CACHE_NAMESPACE = 'analysis-merged-hotspots'
const FILTER_OPTIONS_NAMESPACE = 'analysis-merged-filter-options'
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

const restoreSavedFilters = () => {
  if (typeof window === 'undefined') return null
  try {
    return JSON.parse(window.sessionStorage.getItem(FILTER_CACHE_KEY) || 'null')
  } catch {
    return null
  }
}

const savedFilters = restoreSavedFilters()

const filters = reactive({
  timePreset: savedFilters?.timePreset || '7d',
  customRange: savedFilters?.customRange || [],
  area_label: savedFilters?.area_label || 'world',
  source_product: savedFilters?.source_product || '',
  satellite: savedFilters?.satellite || '',
  country: savedFilters?.country || '',
})

const filterOptions = ref({
  area_labels: [],
  source_products: [],
  satellites: [],
  date_max: null,
})
const latestReference = ref(dayjs())
const loading = ref(false)
const hasCachedData = ref(false)
const worldMapReady = ref(Boolean(echarts.getMap(WORLD_MAP_NAME)))
const primaryLoading = ref(false)
const secondaryLoading = ref(false)
const hotspotsLoading = ref(false)
const focusedCountryLoading = ref(false)
let primaryRequestId = 0
let secondaryRequestId = 0
let hotspotRequestId = 0
let focusedCountryRequestId = 0

const overview = reactive({
  total_fire_points: 0,
  high_confidence_fire_points: 0,
  night_fire_points: 0,
  max_frp: 0,
  latest_update: null,
})

const timeline = ref([])
const countryTop = ref([])
const sourceProductPie = ref([])
const daynightPie = ref([])
const choropleth = ref([])
const hotspots = ref([])
const focusedCountry = ref(null)

const timePresetOptions = TIME_PRESET_OPTIONS
const areaOptions = computed(() => normalizeOptionList(filterOptions.value.area_labels, AREA_PRESETS))
const sourceProductOptions = computed(() => [{ value: '', label: '全部数据源' }, ...normalizeOptionList(filterOptions.value.source_products, SOURCE_PRODUCT_PRESETS)])
const satelliteOptions = computed(() => filterOptions.value.satellites || [])

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
  satellite: filters.satellite || undefined,
}))

const trendTitle = computed(() => `火点趋势（${dateParams.value.days}天）`)

const loadingEstimateText = computed(() => {
  if (filters.area_label === 'world' && dateParams.value.days >= 30) return '预计 6-12 秒'
  if (filters.area_label === 'world') return '预计 5-9 秒'
  if (dateParams.value.days >= 30) return '预计 4-8 秒'
  return '预计 3-6 秒'
})

const summaryItems = computed(() => [
  { label: '时间范围', value: `${dateParams.value.start_date} 至 ${dateParams.value.end_date}` },
  { label: '当前区域', value: AREA_PRESETS[filters.area_label]?.label || filters.area_label || '全部区域' },
  { label: '当前数据源', value: SOURCE_PRODUCT_PRESETS[filters.source_product]?.label || filters.source_product || '全部数据源' },
  { label: '卫星筛选', value: filters.satellite || '全部卫星' },
  { label: '最新更新时间', value: formatDateTime(overview.latest_update) },
  { label: '当前焦点国家', value: focusedCountry.value?.country_name || filters.country || countryTop.value[0]?.name || '--' },
  { label: '焦点国家火点', value: formatNumber(focusedCountry.value?.total_fire_points) },
  { label: '焦点国家平均 FRP', value: formatMetric(focusedCountry.value?.avg_frp) },
])

const themeToken = (token, fallback) => {
  uiStore.themeMode
  if (typeof window === 'undefined') return fallback
  return getComputedStyle(document.documentElement).getPropertyValue(token).trim() || fallback
}

const chartPalette = computed(() => ({
  textPrimary: themeToken('--text-primary', '#eff6ff'),
  textSecondary: themeToken('--text-secondary', 'rgba(237,245,255,0.66)'),
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
  const match = color.match(/\d+(\.\d+)?/g)
  if (match?.length >= 3) {
    return `rgba(${match[0]}, ${match[1]}, ${match[2]}, ${alpha})`
  }
  return color
}

const pieOption = (data, colors) => ({
  backgroundColor: 'transparent',
  color: colors,
  tooltip: { trigger: 'item' },
  legend: {
    bottom: 0,
    textStyle: { color: chartPalette.value.textSecondary },
  },
  series: [
    {
      type: 'pie',
      radius: ['42%', '72%'],
      center: ['50%', '44%'],
      label: { color: chartPalette.value.textPrimary },
      data,
    },
  ],
})

const trendOption = computed(() => ({
  textStyle: { color: chartPalette.value.textPrimary },
  grid: { left: 42, right: 18, top: 30, bottom: 28 },
  tooltip: { trigger: 'axis' },
  xAxis: {
    type: 'category',
    data: timeline.value.map((item) => item.date),
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
      data: timeline.value.map((item) => item.value),
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

const countryTopOption = computed(() => ({
  textStyle: { color: chartPalette.value.textPrimary },
  grid: { left: 96, right: 18, top: 18, bottom: 18 },
  xAxis: {
    type: 'value',
    axisLabel: { color: chartPalette.value.textSecondary },
    splitLine: { lineStyle: { color: chartPalette.value.gridLine } },
  },
  yAxis: {
    type: 'category',
    data: countryTop.value.map((item) => item.name).reverse(),
    axisLabel: { color: chartPalette.value.textPrimary },
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

const sourceProductOption = computed(() =>
  pieOption(
    sourceProductPie.value.map((item) => ({
      name: SOURCE_PRODUCT_PRESETS[item.name]?.label || item.name,
      value: item.value,
    })),
    [chartPalette.value.accentCyan, chartPalette.value.accentOrange, chartPalette.value.accentBlue],
  ),
)

const daynightOption = computed(() =>
  pieOption(
    daynightPie.value.map((item) => ({
      name: item.name === 'D' ? '白天' : item.name === 'N' ? '夜间' : item.name,
      value: item.value,
    })),
    [chartPalette.value.accentOrange, chartPalette.value.accentBlue],
  ),
)

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
    bottom: 10,
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
        selected: item.name === (focusedCountry.value?.country_name || filters.country),
      })),
    },
  ],
}))

const persistFilters = () => {
  if (typeof window === 'undefined') return
  window.sessionStorage.setItem(
    FILTER_CACHE_KEY,
    JSON.stringify({
      timePreset: filters.timePreset,
      customRange: filters.customRange,
      area_label: filters.area_label,
      source_product: filters.source_product,
      satellite: filters.satellite,
      country: filters.country,
    }),
  )
}

const buildPrimaryCacheKey = () =>
  makeCacheKey({
    start_date: baseParams.value.start_date,
    end_date: baseParams.value.end_date,
    area_label: filters.area_label,
    source_product: filters.source_product,
    satellite: filters.satellite,
  })

const buildSecondaryCacheKey = () =>
  makeCacheKey({
    start_date: baseParams.value.start_date,
    end_date: baseParams.value.end_date,
    area_label: filters.area_label,
    source_product: filters.source_product,
    satellite: filters.satellite,
  })

const applyPrimaryPayload = (payload) => {
  Object.assign(overview, payload.overview || {})
  timeline.value = payload.timeline || []
  countryTop.value = payload.countryTop || []
  choropleth.value = payload.choropleth || []
}

const applySecondaryPayload = (payload) => {
  sourceProductPie.value = payload.sourceProductPie || []
  daynightPie.value = payload.daynightPie || []
}

const applyFocusedCountry = (payload) => {
  focusedCountry.value = payload || null
}

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

const loadFocusedCountry = async (country, { force = false } = {}) => {
  const requestId = ++focusedCountryRequestId
  if (!country) {
    focusedCountry.value = null
    focusedCountryLoading.value = false
    return
  }

  focusedCountryLoading.value = true
  const cacheKey = makeCacheKey({
    country,
    ...baseParams.value,
  })
  const cached = !force ? readViewCache(COUNTRY_CACHE_NAMESPACE, cacheKey, CACHE_TTL_MS) : null
  if (cached) {
    applyFocusedCountry(cached)
    if (requestId === focusedCountryRequestId) {
      focusedCountryLoading.value = false
    }
    return
  }

  try {
    const payload = await analysisApi.countryDetail({
      country,
      ...baseParams.value,
    })
    applyFocusedCountry(payload)
    writeViewCache(COUNTRY_CACHE_NAMESPACE, cacheKey, payload)
  } finally {
    if (requestId === focusedCountryRequestId) {
      focusedCountryLoading.value = false
    }
  }
}

const loadSecondaryInsights = async ({ force = false } = {}) => {
  const requestId = ++secondaryRequestId
  secondaryLoading.value = true
  const cacheKey = buildSecondaryCacheKey()
  const cached = !force ? readViewCache(SECONDARY_CACHE_NAMESPACE, cacheKey, CACHE_TTL_MS) : null
  if (cached) {
    applySecondaryPayload(cached)
    if (requestId === secondaryRequestId) {
      secondaryLoading.value = false
    }
    return
  }

  try {
    const [sourceProductPayload, daynightPayload] = await Promise.all([
      analysisApi.sourceProductPie(baseParams.value),
      analysisApi.daynightPie(baseParams.value),
    ])
    const payload = {
      sourceProductPie: sourceProductPayload || [],
      daynightPie: daynightPayload || [],
    }
    applySecondaryPayload(payload)
    writeViewCache(SECONDARY_CACHE_NAMESPACE, cacheKey, payload)
  } finally {
    if (requestId === secondaryRequestId) {
      secondaryLoading.value = false
    }
  }
}

const buildHotspotCacheKey = () =>
  makeCacheKey({
    window: dateParams.value.window,
    limit: 8,
    ...baseParams.value,
  })

const loadHotspotsSummary = async ({ force = false } = {}) => {
  const requestId = ++hotspotRequestId
  hotspotsLoading.value = true
  const cacheKey = buildHotspotCacheKey()
  const cached = !force ? readViewCache(HOTSPOT_CACHE_NAMESPACE, cacheKey, CACHE_TTL_MS) : null
  if (cached) {
    hotspots.value = cached
    if (requestId === hotspotRequestId) {
      hotspotsLoading.value = false
    }
    return
  }

  try {
    const payload = await hotspotApi.top({
      window: dateParams.value.window,
      limit: 8,
      ...baseParams.value,
    })
    hotspots.value = payload || []
    writeViewCache(HOTSPOT_CACHE_NAMESPACE, cacheKey, hotspots.value)
  } finally {
    if (requestId === hotspotRequestId) {
      hotspotsLoading.value = false
    }
  }
}

const loadBundle = async ({ force = false } = {}) => {
  const cacheKey = buildPrimaryCacheKey()
  const cached = !force ? readViewCache(PRIMARY_CACHE_NAMESPACE, cacheKey, CACHE_TTL_MS) : null

  hasCachedData.value = Boolean(cached)
  if (cached) {
    applyPrimaryPayload(cached)
  }

  if (cached && !force) {
    const nextCountry = filters.country || cached.defaultCountry || cached.countryTop?.[0]?.name || ''
    filters.country = nextCountry
    focusedCountry.value = null
    void Promise.allSettled([loadSecondaryInsights(), loadFocusedCountry(nextCountry), loadHotspotsSummary()])
    return
  }

  const requestId = ++primaryRequestId
  loading.value = true
  primaryLoading.value = true
  try {
    sourceProductPie.value = []
    daynightPie.value = []
    hotspots.value = []
    focusedCountry.value = null
    const [overviewPayload, timelinePayload, countryTopPayload, choroplethPayload] = await Promise.all([
      analysisApi.overview(baseParams.value),
      analysisApi.timeline({ days: dateParams.value.days, ...baseParams.value }),
      analysisApi.countryTop({ limit: 10, ...baseParams.value }),
      analysisApi.countryChoropleth({ metric: 'count', ...baseParams.value }),
    ])

    const payload = {
      overview: overviewPayload,
      timeline: timelinePayload,
      countryTop: countryTopPayload,
      choropleth: choroplethPayload,
      defaultCountry: filters.country || countryTopPayload?.[0]?.name || choroplethPayload?.[0]?.name || '',
    }

    applyPrimaryPayload(payload)
    writeViewCache(PRIMARY_CACHE_NAMESPACE, cacheKey, payload)
    filters.country = payload.defaultCountry
    hasCachedData.value = true
    void Promise.allSettled([
      loadSecondaryInsights({ force }),
      loadFocusedCountry(payload.defaultCountry, { force }),
      loadHotspotsSummary({ force }),
    ])
  } finally {
    if (requestId === primaryRequestId) {
      loading.value = false
      primaryLoading.value = false
    }
  }
}

const applyFilters = async () => {
  persistFilters()
  await loadBundle({ force: true })
}

const resetFilters = async () => {
  filters.timePreset = '7d'
  filters.customRange = []
  filters.area_label = 'world'
  filters.source_product = ''
  filters.satellite = ''
  filters.country = ''
  persistFilters()
  await loadBundle({ force: true })
}

const handleCountrySelect = async (country) => {
  if (!country) return
  filters.country = country
  persistFilters()
  loading.value = true
  try {
    await loadFocusedCountry(country)
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
  await loadBundle()
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
.merged-analysis-page {
  position: relative;
  padding-bottom: 8px;
}

.filters {
  display: grid;
  grid-template-columns: 1.25fr 1.2fr 1fr 1fr 1fr auto;
  gap: 12px;
}

.filter-actions {
  display: flex;
  gap: 10px;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 14px;
}

.primary-grid {
  display: grid;
  grid-template-columns: 1.3fr 1fr;
  gap: 16px;
}

.secondary-grid {
  display: grid;
  grid-template-columns: 1.45fr 0.82fr;
  gap: 16px;
  align-items: stretch;
}

.structure-column {
  display: grid;
  gap: 16px;
}

.map-panel :deep(.panel-body) {
  padding-top: 4px;
}

.supplement-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  align-items: stretch;
}

.balanced-panel {
  height: 360px;
  min-height: 360px;
}

.balanced-panel :deep(.panel) {
  height: 100%;
}

.balanced-panel :deep(.panel-body) {
  height: calc(100% - 38px);
  overflow: auto;
}

.hotspot-list,
.summary-list {
  display: grid;
  gap: 12px;
}

.hotspot-item,
.summary-list article {
  padding: 16px 18px;
  border-radius: 18px;
  border: 1px solid var(--line-soft);
  background: var(--bg-elevated);
}

.hotspot-head,
.hotspot-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.hotspot-head {
  margin-bottom: 10px;
}

.hotspot-meta {
  color: var(--text-secondary);
  font-size: 13px;
}

.hotspot-meta + .hotspot-meta {
  margin-top: 8px;
}

.summary-list article {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.summary-list span {
  color: var(--text-secondary);
}

@media (max-width: 1440px) {
  .filters,
  .stat-grid,
  .primary-grid,
  .secondary-grid,
  .supplement-grid {
    grid-template-columns: 1fr;
  }
}
</style>
