<template>
  <div class="screen-page" :class="{ demo: isDemo }">
    <LoadingEstimateOverlay :visible="bootLoading" title="正在加载中" :description="loadingEstimateText" />

    <header class="screen-header">
      <div class="header-title">
        <h1>全球野火火点监测与时空分析平台</h1>
        <div class="header-flags">
          <div class="chip-row">
            <span class="chip strong-chip">{{ screenContextLabel }}</span>
            <span class="chip" :class="{ 'strong-chip': presentationStore.cruising }">
              {{ presentationStore.cruising ? '巡航中' : '巡航暂停' }}
            </span>
          </div>
          <div class="chip-row">
            <span class="chip">时间 {{ nowText }}</span>
            <span class="chip">更新 {{ formatDateTime(summary.latest_update, 'MM-DD HH:mm') }}</span>
          </div>
        </div>
      </div>

      <div class="header-controls">
        <div class="header-filters">
          <div class="control-caption">筛选范围</div>
          <div class="filter-group">
            <div class="filter-cell filter-cell--compact">
              <span class="field-label">时间窗口</span>
              <el-segmented v-model="filters.timePreset" size="small" :options="screenTimePresetOptions" />
            </div>
            <div v-if="filters.timePreset === 'custom'" class="filter-cell filter-cell--wide">
              <span class="field-label">自定义时间</span>
              <el-date-picker
                v-model="filters.customRange"
                type="daterange"
                value-format="YYYY-MM-DD"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
              />
            </div>
            <div class="filter-cell">
              <span class="field-label">区域</span>
              <el-select v-model="filters.area_label" clearable placeholder="区域">
                <el-option v-for="item in areaOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </div>
            <div class="filter-cell">
              <span class="field-label">数据源</span>
              <el-select v-model="filters.source_product" clearable placeholder="数据源">
                <el-option v-for="item in sourceProductOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </div>
            <div class="filter-cell">
              <span class="field-label">卫星</span>
              <el-select v-model="filters.satellite" clearable placeholder="卫星">
                <el-option v-for="item in satelliteOptions" :key="item" :label="item" :value="item" />
              </el-select>
            </div>
          </div>
        </div>

        <div class="action-group">
          <el-button class="action-btn action-btn--apply" @click="applyFilters">应用筛选</el-button>
          <el-button class="action-btn action-btn--reset" @click="resetFilters">重置筛选</el-button>
          <el-button class="action-btn action-btn--cruise" @click="toggleCruise">
            {{ presentationStore.cruising ? '暂停巡航' : '开始巡航' }}
          </el-button>
          <el-button class="action-btn action-btn--view" @click="resetView">重置视角</el-button>
          <el-button class="action-btn action-btn--back" @click="router.push('/overview')">返回系统</el-button>
          <el-button class="action-btn action-btn--demo" @click="isDemo ? exitDemo() : router.push('/demo')">
            {{ isDemo ? '退出演示' : '进入演示' }}
          </el-button>
        </div>
      </div>
    </header>

    <section class="screen-grid">
      <aside class="side-column left-column">
        <GlassPanel
          ref="focusPanelRef"
          :title="focusPanelTitle"
          compact
          scrollable
          class="focus-panel"
          @mouseenter="pauseFocusScroll"
          @mouseleave="restartFocusScroll"
        >
          <div class="focus-caption">{{ focusPanelCaption }}</div>
          <div v-if="!selectedFire && !activeHotspot && summaryLoading" class="card-state">当前关注加载中</div>
          <template v-else>
            <div class="detail-grid focus-grid">
              <div v-for="item in focusStats" :key="item.label" class="detail-item detail-item--focus">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </div>
            </div>
            <div class="focus-weather">
              <div class="sub-panel-header">
                <span>联动天气</span>
                <span class="muted">{{ weatherStatusText }}</span>
              </div>
              <div v-if="weatherLoading" class="card-state subtle">天气加载中</div>
              <div v-else-if="weatherStats.length" class="weather-grid weather-grid--inline">
                <div v-for="item in weatherStats" :key="item.label" class="weather-item weather-item--compact">
                  <span>{{ item.label }}</span>
                  <strong>{{ item.value }}</strong>
                </div>
              </div>
              <div v-else class="card-state subtle">点击火点或热点后显示天气</div>
            </div>
          </template>
        </GlassPanel>
      </aside>

      <div class="center-column screen-card stage-shell">
        <div class="stage-aura"></div>
        <div class="stage-scan"></div>
        <div class="stage-corners" aria-hidden="true">
          <span class="stage-corner top-left"></span>
          <span class="stage-corner top-right"></span>
          <span class="stage-corner bottom-left"></span>
          <span class="stage-corner bottom-right"></span>
        </div>
        <CesiumMap
          ref="mapRef"
          :points="displayPoints"
          :hotspots="hotspots"
          :selected-country="selectedCountry"
          :initial-view="areaViewKey"
          :show-hotspots="true"
          :show-fire-points="true"
          :show-countries="false"
          :cluster-fire-points="false"
          :glow-mode="isDemo"
          @select-hotspot="handleSelectHotspot"
          @select-fire="handleFireClick"
          @select-country="handleCountrySelect"
        />
      </div>

      <aside class="side-column right-column">
        <div class="screen-card chart-card rank-card">
          <div class="panel-header">
            <h3>国家排行</h3>
            <span class="muted">Top {{ rankings.countryTop.length || 0 }}</span>
          </div>
          <div
            ref="rankScrollRef"
            class="rank-chart-scroll"
            @mouseenter="pauseRankScroll"
            @mouseleave="restartRankScroll"
          >
            <BaseChart
              :option="countryRankOption"
              :height="countryRankChartHeight"
              :loading="rankingLoading"
              loading-text="国家排行计算中"
            />
          </div>
        </div>
      </aside>
    </section>

    <section class="bottom-grid">
      <div class="screen-card trend-card">
        <div class="panel-header trend-panel-header">
          <div class="trend-title">
            <h3>趋势分析</h3>
            <span class="muted">{{ `${dateParams.days}天窗口 · ${demoStatusText}` }}</span>
          </div>
          <div class="trend-messages" v-if="messages.length">
            <span v-for="(item, index) in messages.slice(0, 2)" :key="`${item.acq_datetime}-${index}`">
              {{ item.message }}
            </span>
          </div>
        </div>
        <div class="trend-grid">
          <div class="trend-pane">
            <div class="trend-pane-header">
              <strong>火点数量趋势</strong>
              <span class="muted">按日统计</span>
            </div>
            <BaseChart :option="timelineOption" :height="138" :loading="trendLoading" loading-text="数量趋势加载中" />
          </div>
          <div class="trend-pane">
            <div class="trend-pane-header">
              <strong>FRP 日均强度</strong>
              <span class="muted">按日统计</span>
            </div>
            <BaseChart :option="frpTrendOption" :height="138" :loading="trendLoading" loading-text="FRP 趋势加载中" />
          </div>
        </div>
        <div class="timeline-box">
          <TimePlayback
            v-model="currentIndex"
            :options="timelineOptions"
            :granularity="'day'"
            :interval="2200"
            :autoplay="isDemo && presentationStore.demoRunning"
            :show-granularity-toggle="false"
            @play-change="handleDemoPlayback"
          />
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import dayjs from 'dayjs'
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { dashboardApi, fireApi, weatherApi } from '@/api/service'
import BaseChart from '@/components/BaseChart.vue'
import CesiumMap from '@/components/CesiumMap.vue'
import GlassPanel from '@/components/GlassPanel.vue'
import LoadingEstimateOverlay from '@/components/LoadingEstimateOverlay.vue'
import TimePlayback from '@/components/TimePlayback.vue'
import { usePresentationStore } from '@/stores/presentation'
import { useUiStore } from '@/stores/ui'
import {
  AREA_PRESETS,
  SOURCE_PRODUCT_PRESETS,
  TIME_PRESET_OPTIONS,
  buildDateParams,
  normalizeOptionList,
  resolveAreaView,
} from '@/utils/fireDataConfig'
import { formatDateTime, formatNumber } from '@/utils/format'
import { makeCacheKey, readViewCache, writeViewCache } from '@/utils/viewCache'

const POINT_FETCH_LIMITS = {
  world: { '1d': 1800, '7d': 2600, '30d': 3200, custom: 2600 },
  default: { '1d': 2200, '7d': 3000, '30d': 3600, custom: 3000 },
}
const SCREEN_CACHE_NAMESPACE = 'screen-dashboard'
const SCREEN_CACHE_TTL_MS = 8 * 60 * 1000

const route = useRoute()
const router = useRouter()
const presentationStore = usePresentationStore()
const uiStore = useUiStore()
const mapRef = ref()
const isDemo = computed(() => Boolean(route.meta?.demo))

const bootLoading = ref(false)
const summaryLoading = ref(false)
const rankingLoading = ref(false)
const hotspotLoading = ref(false)
const trendLoading = ref(false)
const nowText = ref(dayjs().format('YYYY-MM-DD HH:mm:ss'))
const currentIndex = ref(0)
const latestReference = ref(dayjs())
const filterOptions = ref({
  area_labels: [],
  source_products: [],
  satellites: [],
  date_max: null,
})

const filters = reactive({
  timePreset: '7d',
  customRange: [],
  area_label: 'world',
  source_product: '',
  satellite: '',
})

const summary = reactive({
  total_fire_points: 0,
  today_fire_points: 0,
  high_confidence_fire_points: 0,
  night_fire_points: 0,
  max_frp: 0,
  latest_update: '',
})

const rankings = reactive({
  countryTop: [],
  satellitePie: [],
  daynightPie: [],
})

const trendData = ref([])
const messages = ref([])
const hotspots = ref([])
const cruisePoints = ref([])
const firePoints = ref([])
const activeHotspot = ref(null)
const selectedFire = ref(null)
const selectedCountry = ref('')
const weather = ref(null)
const weatherLoading = ref(false)
const requestToken = ref(0)
const rankScrollRef = ref(null)
const focusPanelRef = ref(null)
const flowTick = ref(0)

let clockTimer = null
let cruiseTimer = null
let rankScrollTimer = null
let focusScrollTimer = null
let flowTimer = null
let rankScrollDirection = 1
let focusScrollDirection = 1

const screenTimePresetOptions = computed(() => TIME_PRESET_OPTIONS.filter((item) => item.value !== '1d'))
const areaOptions = computed(() => normalizeOptionList(filterOptions.value.area_labels, AREA_PRESETS))
const sourceProductOptions = computed(() => normalizeOptionList(filterOptions.value.source_products, SOURCE_PRODUCT_PRESETS))
const satelliteOptions = computed(() => filterOptions.value.satellites || [])

const dateParams = computed(() =>
  buildDateParams({
    preset: filters.timePreset,
    customRange: filters.customRange,
    latestReference: latestReference.value,
  }),
)

const screenQueryParams = computed(() => ({
  start_date: dateParams.value.start_date,
  end_date: dateParams.value.end_date,
  area_label: filters.area_label || undefined,
  source_product: filters.source_product || undefined,
  satellite: filters.satellite || undefined,
}))

const areaViewKey = computed(() => resolveAreaView(filters.area_label))
const currentAreaLabel = computed(() => AREA_PRESETS[filters.area_label]?.label || filters.area_label || '全域')
const screenContextLabel = computed(() => (filters.area_label === 'world' ? '全球视角' : currentAreaLabel.value))
const demoFlowActive = computed(() => isDemo.value && presentationStore.demoRunning)
const loadingEstimateText = computed(() => {
  if (filters.area_label === 'world' && dateParams.value.days >= 30) return '预计 6-12 秒'
  if (filters.area_label === 'world') return '预计 5-9 秒'
  return '预计 4-8 秒'
})

const timelineOptions = computed(() => {
  const groups = new Map()
  firePoints.value.forEach((item) => {
    const key = dayjs(item.acq_datetime).format('YYYY-MM-DD')
    if (!groups.has(key)) {
      groups.set(key, {
        value: key,
        label: key,
        shortLabel: dayjs(key).format('MM-DD'),
      })
    }
  })
  return Array.from(groups.values()).sort((a, b) => a.value.localeCompare(b.value))
})

const displayPoints = computed(() => {
  const active = timelineOptions.value[currentIndex.value]
  if (!active) return firePoints.value
  return firePoints.value.filter((item) => dayjs(item.acq_datetime).format('YYYY-MM-DD') === active.value)
})

const themeToken = (token, fallback) => {
  uiStore.themeMode
  if (typeof window === 'undefined') return fallback
  return getComputedStyle(document.documentElement).getPropertyValue(token).trim() || fallback
}

const chartPalette = computed(() => ({
  textPrimary: themeToken('--text-primary', '#ffffff'),
  textSecondary: themeToken('--text-secondary', 'rgba(237,245,255,0.7)'),
  accentCyan: themeToken('--accent-cyan', '#59d6ff'),
  accentBlue: themeToken('--accent-blue', '#2f73ff'),
  accentOrange: themeToken('--accent-orange', '#ff8d43'),
  gridLine: uiStore.themeMode === 'light' ? 'rgba(37, 102, 186, 0.1)' : 'rgba(99,195,255,0.08)',
}))

const trendAxisDates = computed(() => {
  if (trendData.value.length) {
    return trendData.value.map((item) => dayjs(item.date).format('YYYY-MM-DD'))
  }
  return timelineOptions.value.map((item) => item.value)
})

const trendAxisLabels = computed(() => trendAxisDates.value.map((item) => dayjs(item).format('MM-DD')))

const trendValues = computed(() => {
  if (trendData.value.length) return trendData.value.map((item) => item.value ?? 0)
  return trendAxisDates.value.map(() => 0)
})

const flowHeadPosition = computed(() => {
  const maxIndex = Math.max(trendAxisDates.value.length - 1, 0)
  if (maxIndex <= 0) return 0
  return (flowTick.value % 240) / 240 * maxIndex
})

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

const buildValueAxis = () => ({
  type: 'value',
  min: 0,
  max: Math.max(trendAxisLabels.value.length - 1, 0),
  interval: 1,
  boundaryGap: false,
  axisLabel: {
    color: chartPalette.value.textSecondary,
    fontSize: 11,
    formatter: (value) => {
      const index = Math.round(Number(value))
      return Number.isInteger(index) ? trendAxisLabels.value[index] || '' : ''
    },
  },
  splitLine: { show: false },
})

const buildNumericSeries = (values) => values.map((value, index) => [index, Number(value ?? 0)])

const interpolateFlowPoint = (values, position) => {
  const maxIndex = Math.max(values.length - 1, 0)
  if (!maxIndex) return [0, Number(values[0] ?? 0)]
  const clamped = Math.min(Math.max(position, 0), maxIndex)
  const left = Math.floor(clamped)
  const right = Math.min(left + 1, maxIndex)
  const progress = clamped - left
  const start = Number(values[left] ?? 0)
  const end = Number(values[right] ?? start)
  return [clamped, Number((start + (end - start) * progress).toFixed(2))]
}

const buildFlowTrail = (values, trailSpan = 1.65, samples = 9) => {
  if (!demoFlowActive.value || values.length < 2) return []
  const points = []
  for (let index = samples - 1; index >= 0; index -= 1) {
    const offset = (trailSpan * index) / (samples - 1)
    points.push(interpolateFlowPoint(values, flowHeadPosition.value - offset))
  }
  return points
}

const createFlowSeries = (color, values) => {
  const trailData = buildFlowTrail(values)
  if (!trailData.length) return []
  return [
    {
      name: `flow-trail-${color}`,
      type: 'line',
      z: 4,
      silent: true,
      showSymbol: false,
      smooth: true,
      animationDurationUpdate: 120,
      animationEasingUpdate: 'linear',
      data: trailData,
      lineStyle: {
        width: 6,
        color: withAlpha(color, 0.94),
        shadowBlur: 18,
        shadowColor: withAlpha(color, 0.46),
        cap: 'round',
      },
      tooltip: { show: false },
    },
    {
      name: `flow-head-${color}`,
      type: 'effectScatter',
      coordinateSystem: 'cartesian2d',
      z: 5,
      animationDurationUpdate: 120,
      animationEasingUpdate: 'linear',
      data: [trailData[trailData.length - 1]],
      symbolSize: 14,
      showEffectOn: 'render',
      rippleEffect: {
        scale: 2.8,
        brushType: 'stroke',
        period: 3.2,
      },
      itemStyle: {
        color,
        shadowBlur: 20,
        shadowColor: withAlpha(color, 0.56),
      },
      tooltip: { show: false },
    },
  ]
}

const buildTrendTooltip = (label, unit = '') => ({
  trigger: 'axis',
  formatter: (params) => {
    const basePoint =
      params.find((item) => item.seriesName === label) ||
      params.find((item) => item.seriesType === 'line' && Array.isArray(item.value))
    const point = Array.isArray(basePoint?.value) ? basePoint.value : [basePoint?.dataIndex ?? 0, basePoint?.value ?? 0]
    const index = Math.max(0, Math.min(trendAxisDates.value.length - 1, Math.round(Number(point[0] ?? 0))))
    return `${trendAxisDates.value[index] || '--'}<br/>${label}：${formatMetricValue(point[1], unit)}`
  },
  axisPointer: {
    type: 'line',
    lineStyle: {
      color: 'rgba(141, 213, 255, 0.26)',
      type: 'dashed',
      width: 1,
    },
  },
})

const countryRankOption = computed(() => ({
  backgroundColor: 'transparent',
  grid: { left: 92, right: 18, top: 18, bottom: 16 },
  xAxis: {
    type: 'value',
    axisLabel: { color: chartPalette.value.textSecondary },
    splitLine: { lineStyle: { color: chartPalette.value.gridLine } },
  },
  yAxis: {
    type: 'category',
    data: rankings.countryTop.map((item) => item.name).reverse(),
    axisLabel: { color: chartPalette.value.textPrimary, fontSize: 11 },
  },
  series: [
    {
      type: 'bar',
      data: rankings.countryTop.map((item) => item.value).reverse(),
      itemStyle: { color: chartPalette.value.accentOrange, borderRadius: [0, 10, 10, 0] },
    },
  ],
}))

const countryRankChartHeight = computed(() => Math.max(440, rankings.countryTop.length * 52 + 64))

const timelineOption = computed(() => ({
  backgroundColor: 'transparent',
  grid: { left: 44, right: 18, top: 26, bottom: 26 },
  xAxis: buildValueAxis(),
  yAxis: {
    type: 'value',
    axisLabel: { color: chartPalette.value.textSecondary },
    splitLine: { lineStyle: { color: chartPalette.value.gridLine } },
  },
  tooltip: buildTrendTooltip('火点数量趋势'),
  series: [
    {
      name: '火点数量趋势',
      type: 'line',
      smooth: true,
      data: buildNumericSeries(trendValues.value),
      lineStyle: { width: 3, color: chartPalette.value.accentCyan },
      areaStyle: { color: `${chartPalette.value.accentCyan}24` },
      symbolSize: 6,
      showSymbol: false,
    },
    ...createFlowSeries(chartPalette.value.accentCyan, trendValues.value),
  ],
}))

const frpTrendSeries = computed(() => {
  const buckets = new Map()
  firePoints.value.forEach((item) => {
    const key = dayjs(item.acq_datetime).format('YYYY-MM-DD')
    const frp = Number(item.frp)
    if (!key || !Number.isFinite(frp)) return
    const current = buckets.get(key) || { sum: 0, count: 0 }
    current.sum += frp
    current.count += 1
    buckets.set(key, current)
  })
  return trendAxisDates.value.map((date) => {
    const row = buckets.get(date)
    return row?.count ? Number((row.sum / row.count).toFixed(1)) : 0
  })
})

const frpTrendOption = computed(() => ({
  backgroundColor: 'transparent',
  grid: { left: 44, right: 18, top: 26, bottom: 26 },
  xAxis: buildValueAxis(),
  yAxis: {
    type: 'value',
    axisLabel: { color: chartPalette.value.textSecondary },
    splitLine: { lineStyle: { color: chartPalette.value.gridLine } },
  },
  tooltip: buildTrendTooltip('FRP 日均强度'),
  series: [
    {
      name: 'FRP 日均强度',
      type: 'line',
      smooth: true,
      data: buildNumericSeries(frpTrendSeries.value),
      lineStyle: { width: 3, color: chartPalette.value.accentOrange },
      areaStyle: { color: `${chartPalette.value.accentOrange}20` },
      symbolSize: 6,
      showSymbol: false,
    },
    ...createFlowSeries(chartPalette.value.accentOrange, frpTrendSeries.value),
  ],
}))

const demoStatusText = computed(() => {
  if (!isDemo.value) return presentationStore.cruising ? '自动巡航' : '手动查看'
  return presentationStore.demoRunning ? `阶段：${presentationStore.demoStage}` : '演示暂停'
})

const sourceProductLabel = (value) => SOURCE_PRODUCT_PRESETS[value]?.label || value || '--'
const formatMetricValue = (value, unit = '') => {
  const numeric = Number(value)
  if (Number.isFinite(numeric)) {
    const fractionDigits = Math.abs(numeric % 1) > 0.001 ? 1 : 0
    return `${numeric.toLocaleString('zh-CN', {
      minimumFractionDigits: fractionDigits,
      maximumFractionDigits: 1,
    })}${unit}`
  }
  return value === null || value === undefined || value === '' ? '--' : `${value}${unit}`
}
const formatWeatherWind = (speed, direction) => {
  const speedText = speed === null || speed === undefined ? '--' : `${speed}km/h`
  const directionText = direction === null || direction === undefined ? '--' : `${direction}°`
  return `${speedText} / ${directionText}`
}

const focusPanelTitle = computed(() => {
  if (selectedFire.value) return '当前关注 · 火点'
  if (activeHotspot.value) return '当前关注 · 热点'
  return '当前关注'
})

const focusPanelCaption = computed(() => {
  if (selectedFire.value) {
    return `${selectedFire.value.country_name || '未知区域'} · 已选火点详情`
  }
  if (activeHotspot.value) {
    return `${activeHotspot.value.major_country || activeHotspot.value.id || '热点区域'} · 已选热点簇`
  }
  return `${screenContextLabel.value} · 当前筛选概览`
})

const focusStats = computed(() => {
  if (selectedFire.value) {
    return [
      { label: '国家', value: selectedFire.value.country_name || '未知' },
      { label: '时间', value: formatDateTime(selectedFire.value.acq_datetime) },
      { label: '数据源', value: sourceProductLabel(selectedFire.value.source_product) },
      { label: '卫星', value: selectedFire.value.satellite || '--' },
      { label: 'FRP', value: formatMetricValue(selectedFire.value.frp) },
      { label: '昼夜', value: selectedFire.value.daynight || '--' },
    ]
  }
  if (activeHotspot.value) {
    return [
      { label: '区域', value: activeHotspot.value.major_country || activeHotspot.value.id || '未知热点' },
      { label: '火点数', value: formatNumber(activeHotspot.value.fire_count) },
      { label: '平均 FRP', value: formatMetricValue(activeHotspot.value.avg_frp) },
      { label: '最大 FRP', value: formatMetricValue(activeHotspot.value.max_frp) },
      { label: '开始时间', value: formatDateTime(activeHotspot.value.time_start) },
      { label: '结束时间', value: formatDateTime(activeHotspot.value.time_end) },
    ]
  }
  return [
    { label: '累计火点', value: formatNumber(summary.total_fire_points) },
    { label: '今日火点', value: formatNumber(summary.today_fire_points) },
    { label: '高置信度', value: formatNumber(summary.high_confidence_fire_points) },
    { label: '夜间火点', value: formatNumber(summary.night_fire_points) },
    { label: '峰值 FRP', value: formatMetricValue(summary.max_frp) },
    { label: '最新更新', value: formatDateTime(summary.latest_update) },
  ]
})

const weatherStats = computed(() => {
  if (!weather.value) return []
  return [
    { label: '温度', value: formatMetricValue(weather.value.temperature_2m, '°C') },
    { label: '当前降水', value: formatMetricValue(weather.value.precipitation, 'mm') },
    { label: '24h降水', value: formatMetricValue(weather.value.precipitation_24h, 'mm') },
    { label: '风速 / 风向', value: formatWeatherWind(weather.value.wind_speed_10m, weather.value.wind_direction_10m) },
  ]
})

const weatherStatusText = computed(() => {
  if (weatherLoading.value) return '同步中'
  if (weatherStats.value.length) return '已联动'
  return '待联动'
})

const rankScrollSignature = computed(() => rankings.countryTop.map((item) => `${item.name}:${item.value}`).join('|'))
const focusScrollSignature = computed(() =>
  [
    focusPanelTitle.value,
    selectedFire.value?.id || selectedFire.value?.acq_datetime || '',
    activeHotspot.value?.id || '',
    focusStats.value.map((item) => `${item.label}:${item.value}`).join('|'),
    weatherStats.value.map((item) => `${item.label}:${item.value}`).join('|'),
    weatherLoading.value ? 'loading' : 'ready',
  ].join('||'),
)

const resolvePointLimit = () => {
  const group = filters.area_label === 'world' ? POINT_FETCH_LIMITS.world : POINT_FETCH_LIMITS.default
  return group[filters.timePreset] || group.custom
}

const loadFilterOptions = async () => {
  filterOptions.value = await fireApi.filterOptions()
  latestReference.value = filterOptions.value.date_max ? dayjs(filterOptions.value.date_max) : dayjs()
}

const loadWeatherForCoordinates = async (latitude, longitude) => {
  if (!Number.isFinite(Number(latitude)) || !Number.isFinite(Number(longitude))) {
    weather.value = null
    return
  }
  weatherLoading.value = true
  try {
    weather.value = await weatherApi.point({ latitude, longitude })
  } finally {
    weatherLoading.value = false
  }
}

const loadPrimaryData = async (ticket) => {
  bootLoading.value = true
  const params = screenQueryParams.value
  try {
    const pointData = await fireApi.range({
      start: dateParams.value.start,
      end: dateParams.value.end,
      limit: resolvePointLimit(),
      ...params,
    })
    if (ticket !== requestToken.value) return
    firePoints.value = pointData || []
    currentIndex.value = Math.max(timelineOptions.value.length - 1, 0)
  } finally {
    if (ticket === requestToken.value) {
      bootLoading.value = false
    }
  }
}

const buildScreenCacheKey = () =>
  makeCacheKey({
    start_date: screenQueryParams.value.start_date,
    end_date: screenQueryParams.value.end_date,
    area_label: filters.area_label,
    source_product: filters.source_product,
    satellite: filters.satellite,
    mode: isDemo.value ? 'demo' : 'screen',
  })

const applyScreenSnapshot = (payload) => {
  Object.assign(summary, payload.summary || {})
  Object.assign(rankings, payload.rankings || {})
  trendData.value = payload.trendData || []
  messages.value = payload.messages || []
  hotspots.value = payload.hotspots || []
  cruisePoints.value = payload.cruisePoints || []
  firePoints.value = payload.firePoints || []
  currentIndex.value = Math.min(
    Math.max((payload.currentIndex ?? Math.max(timelineOptions.value.length - 1, 0)), 0),
    Math.max(timelineOptions.value.length - 1, 0),
  )
}

const loadSecondaryData = async (ticket) => {
  const params = screenQueryParams.value

  summaryLoading.value = true
  trendLoading.value = true
  rankingLoading.value = true
  hotspotLoading.value = true

  const summaryTask = dashboardApi.summary(params)
    .then((payload) => {
      if (ticket !== requestToken.value) return
      Object.assign(summary, payload)
    })
    .finally(() => {
      if (ticket === requestToken.value) summaryLoading.value = false
    })

  const trendTask = dashboardApi.trends({ days: Math.min(dateParams.value.days, 30), ...params })
    .then((payload) => {
      if (ticket !== requestToken.value) return
      trendData.value = payload.timeline || []
      messages.value = payload.messages || []
    })
    .finally(() => {
      if (ticket === requestToken.value) trendLoading.value = false
    })

  const rankingTask = dashboardApi.rankings({ country_limit: 14, ...params })
    .then((payload) => {
      if (ticket !== requestToken.value) return
      Object.assign(rankings, payload)
    })
    .finally(() => {
      if (ticket === requestToken.value) rankingLoading.value = false
    })

  const hotspotTask = dashboardApi.hotspots({ window: dateParams.value.window, limit: 10, ...params })
    .then((payload) => {
      if (ticket !== requestToken.value) return
      hotspots.value = payload || []
      cruisePoints.value = (payload || []).slice(0, 8).map((item, index) => ({
        id: item.id,
        name: item.major_country || `热点 ${index + 1}`,
        longitude: item.center_longitude,
        latitude: item.center_latitude,
        fire_count: item.fire_count,
        max_frp: item.max_frp,
        area_label: item.area_label,
      }))
      restartCruiseLoop()
    })
    .finally(() => {
      if (ticket === requestToken.value) hotspotLoading.value = false
    })

  await Promise.allSettled([summaryTask, trendTask, rankingTask, hotspotTask])
}

const loadScreenData = async ({ force = false } = {}) => {
  const ticket = Date.now()
  requestToken.value = ticket
  selectedFire.value = null
  activeHotspot.value = null
  weather.value = null
  const cacheKey = buildScreenCacheKey()
  const cached = !force ? readViewCache(SCREEN_CACHE_NAMESPACE, cacheKey, SCREEN_CACHE_TTL_MS) : null
  if (cached) {
    applyScreenSnapshot(cached)
    bootLoading.value = false
    return
  }
  await loadPrimaryData(ticket)
  await loadSecondaryData(ticket)
  writeViewCache(SCREEN_CACHE_NAMESPACE, cacheKey, {
    summary: { ...summary },
    rankings: { ...rankings },
    trendData: trendData.value,
    messages: messages.value,
    hotspots: hotspots.value,
    cruisePoints: cruisePoints.value,
    firePoints: firePoints.value,
    currentIndex: currentIndex.value,
  })
}

const getFocusScrollContainer = () => focusPanelRef.value?.$el?.querySelector('.panel-body.scrollable') || null

const stopAutoScroll = (type) => {
  if (type === 'rank' && rankScrollTimer) {
    clearInterval(rankScrollTimer)
    rankScrollTimer = null
  }
  if (type === 'focus' && focusScrollTimer) {
    clearInterval(focusScrollTimer)
    focusScrollTimer = null
  }
}

const restartAutoScroll = async (type) => {
  stopAutoScroll(type)
  await nextTick()
  const container = type === 'rank' ? rankScrollRef.value : getFocusScrollContainer()
  if (!container) return
  const maxScroll = container.scrollHeight - container.clientHeight
  if (maxScroll <= 8) {
    container.scrollTop = 0
    return
  }
  if (type === 'rank') rankScrollDirection = 1
  if (type === 'focus') focusScrollDirection = 1
  let pauseFrames = 16
  const timer = window.setInterval(() => {
    const target = type === 'rank' ? rankScrollRef.value : getFocusScrollContainer()
    if (!target) return
    const limit = target.scrollHeight - target.clientHeight
    if (limit <= 8) {
      target.scrollTop = 0
      stopAutoScroll(type)
      return
    }
    if (pauseFrames > 0) {
      pauseFrames -= 1
      return
    }
    const direction = type === 'rank' ? rankScrollDirection : focusScrollDirection
    const nextScroll = target.scrollTop + direction
    if (nextScroll >= limit) {
      target.scrollTop = limit
      if (type === 'rank') rankScrollDirection = -1
      if (type === 'focus') focusScrollDirection = -1
      pauseFrames = 18
      return
    }
    if (nextScroll <= 0) {
      target.scrollTop = 0
      if (type === 'rank') rankScrollDirection = 1
      if (type === 'focus') focusScrollDirection = 1
      pauseFrames = 18
      return
    }
    target.scrollTop = nextScroll
  }, 34)
  if (type === 'rank') rankScrollTimer = timer
  if (type === 'focus') focusScrollTimer = timer
}

const pauseRankScroll = () => stopAutoScroll('rank')
const restartRankScroll = async () => restartAutoScroll('rank')
const pauseFocusScroll = () => stopAutoScroll('focus')
const restartFocusScroll = async () => restartAutoScroll('focus')

const startFlowLoop = () => {
  if (flowTimer) {
    clearInterval(flowTimer)
    flowTimer = null
  }
  if (!demoFlowActive.value || trendAxisDates.value.length < 2) return
  flowTimer = window.setInterval(() => {
    flowTick.value += 1
  }, 90)
}

const clearTimers = () => {
  if (clockTimer) clearInterval(clockTimer)
  if (cruiseTimer) clearInterval(cruiseTimer)
  if (rankScrollTimer) clearInterval(rankScrollTimer)
  if (focusScrollTimer) clearInterval(focusScrollTimer)
  if (flowTimer) clearInterval(flowTimer)
  clockTimer = null
  cruiseTimer = null
  rankScrollTimer = null
  focusScrollTimer = null
  flowTimer = null
}

const flyToCruisePoint = async (index) => {
  const point = cruisePoints.value[index]
  if (!point) return
  presentationStore.setCruiseTarget(index, point.name, point.id)
  mapRef.value?.flyToCoordinates({
    longitude: point.longitude,
    latitude: point.latitude,
    height: filters.area_label === 'world' ? 4200000 : 2600000,
    duration: presentationStore.flyDurationSeconds,
  })
  await handleHotspotClick(point)
}

const startCruiseLoop = async () => {
  if (!presentationStore.cruising || !cruisePoints.value.length) return
  await flyToCruisePoint(presentationStore.currentCruiseIndex % cruisePoints.value.length)
  cruiseTimer = window.setInterval(() => {
    const nextIndex = (presentationStore.currentCruiseIndex + 1) % cruisePoints.value.length
    flyToCruisePoint(nextIndex)
  }, presentationStore.cruiseIntervalSeconds * 1000)
}

const restartCruiseLoop = async () => {
  if (cruiseTimer) {
    clearInterval(cruiseTimer)
    cruiseTimer = null
  }
  if (presentationStore.cruising && cruisePoints.value.length) {
    await startCruiseLoop()
  }
}

const resetView = () => {
  presentationStore.resetCruise()
  mapRef.value?.flyHome()
}

const toggleCruise = async () => {
  if (cruiseTimer) {
    clearInterval(cruiseTimer)
    cruiseTimer = null
  }
  if (presentationStore.cruising) {
    presentationStore.pauseCruise()
  } else {
    presentationStore.startCruise()
    await startCruiseLoop()
  }
}

const exitDemo = () => {
  presentationStore.stopDemo()
  router.push('/screen')
}

const handleDemoPlayback = (playing) => {
  if (!isDemo.value) return
  if (playing) {
    presentationStore.startDemo()
    presentationStore.setDemoStage('timeline')
  } else {
    presentationStore.pauseDemo()
  }
}

const handleHotspotClick = async (payload) => {
  if (!payload) {
    activeHotspot.value = null
    weather.value = null
    return
  }
  activeHotspot.value = payload
  selectedFire.value = null
  selectedCountry.value = payload.major_country || ''
  await loadWeatherForCoordinates(payload.center_latitude ?? payload.latitude, payload.center_longitude ?? payload.longitude)
  mapRef.value?.flyToHotspot(payload, filters.area_label === 'world' ? 4200000 : 2600000)
}

const handleSelectHotspot = async (payload) => {
  await handleHotspotClick(payload)
}

const handleFireClick = async (payload) => {
  selectedFire.value = payload
  activeHotspot.value = null
  selectedCountry.value = payload?.country_name || ''
  if (!payload) {
    weather.value = null
    return
  }
  await loadWeatherForCoordinates(payload.latitude, payload.longitude)
}

const handleCountrySelect = (payload) => {
  selectedCountry.value = payload?.name || ''
}

const applyFilters = async () => {
  await loadScreenData({ force: true })
}

const resetFilters = async () => {
  filters.timePreset = '7d'
  filters.customRange = []
  filters.area_label = 'world'
  filters.source_product = ''
  filters.satellite = ''
  await loadScreenData({ force: true })
}

watch(currentIndex, () => {
  selectedFire.value = null
  activeHotspot.value = null
  weather.value = null
})

watch(
  () => filters.timePreset,
  (value) => {
    if (value === '1d') {
      filters.timePreset = '7d'
    }
  },
  { immediate: true },
)

watch(
  () => rankings.countryTop.length,
  async () => {
    await restartRankScroll()
  },
)

watch(rankScrollSignature, async () => {
  await restartRankScroll()
})

watch(focusScrollSignature, async () => {
  await restartFocusScroll()
})

watch(
  () => [demoFlowActive.value, trendAxisDates.value.length],
  () => {
    startFlowLoop()
  },
  { immediate: true },
)

onMounted(async () => {
  await loadFilterOptions()
  await loadScreenData()
  clockTimer = window.setInterval(() => {
    nowText.value = dayjs().format('YYYY-MM-DD HH:mm:ss')
  }, 1000)

  if (isDemo.value) {
    presentationStore.startDemo()
    presentationStore.startCruise()
  } else if (presentationStore.autoStartCruise) {
    presentationStore.startCruise()
  }
})

watch(isDemo, async (value) => {
  if (value) {
    presentationStore.startDemo()
    presentationStore.startCruise()
  } else {
    presentationStore.stopDemo()
    if (presentationStore.autoStartCruise) {
      presentationStore.startCruise()
    } else {
      presentationStore.pauseCruise()
    }
  }
  await restartCruiseLoop()
})

onBeforeUnmount(() => {
  clearTimers()
  presentationStore.pauseCruise()
  presentationStore.pauseDemo()
})
</script>

<style scoped>
.screen-page {
  position: relative;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) 204px;
  gap: 6px;
  width: 100%;
  height: 100vh;
  padding: 6px;
  overflow: hidden;
}

.screen-header,
.screen-card {
  border: 1px solid rgba(99, 195, 255, 0.16);
  background: var(--bg-panel);
  box-shadow: inset 0 0 0 1px rgba(99, 195, 255, 0.05), 0 18px 32px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(18px);
}

.screen-header {
  display: grid;
  grid-template-columns: minmax(280px, auto) minmax(0, 1fr);
  align-items: start;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 24px;
}

.header-controls {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 332px;
  gap: 10px;
  min-width: 0;
}

.header-filters {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
  padding: 8px 10px;
  border-radius: 20px;
  border: 1px solid rgba(99, 195, 255, 0.12);
  background: rgba(7, 22, 39, 0.38);
}

.control-caption,
.field-label,
.sub-panel-header span:first-child {
  color: rgba(201, 230, 255, 0.82);
  letter-spacing: 0.02em;
}

.control-caption {
  font-size: 12px;
}

.filter-group {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.header-flags {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
}

.chip-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.filter-cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.filter-cell--compact {
  min-width: 180px;
}

.filter-cell--wide {
  grid-column: span 2;
}

.field-label {
  font-size: 11px;
}

.header-title h1 {
  margin: 0 0 4px;
  font-size: 19px;
}

.chip {
  padding: 3px 10px;
  border-radius: 999px;
  border: 1px solid rgba(99, 195, 255, 0.14);
  background: rgba(17, 40, 64, 0.44);
  color: var(--text-secondary);
  font-size: 12px;
}

.strong-chip {
  color: var(--text-primary);
}

.muted {
  color: var(--text-secondary);
  font-size: 12px;
}

.screen-grid {
  display: grid;
  grid-template-columns: minmax(280px, 0.94fr) minmax(0, 4.8fr) minmax(300px, 1.05fr);
  gap: 6px;
  min-height: 0;
}

.side-column {
  display: grid;
  gap: 8px;
  min-height: 0;
  overflow: hidden;
}

.left-column {
  grid-template-rows: minmax(0, 1fr);
}

.right-column {
  grid-template-rows: minmax(0, 1fr);
}

.center-column {
  position: relative;
  isolation: isolate;
  min-height: 0;
  padding: 8px;
  border-radius: 24px;
  overflow: hidden;
}

.screen-card {
  border-radius: 24px;
  padding: 10px;
  min-height: 0;
  overflow: hidden;
}

.action-group {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  align-content: start;
}

.action-btn {
  min-height: 38px;
  margin: 0;
  border-radius: 16px;
  border-color: rgba(99, 195, 255, 0.2);
  color: #07131d;
  font-weight: 600;
}

.action-btn:hover {
  filter: brightness(1.04);
}

.action-btn--apply {
  background: linear-gradient(135deg, #68d6ff, #3d8dff);
}

.action-btn--reset {
  background: linear-gradient(135deg, #6cecc4, #2fb48f);
}

.action-btn--cruise {
  background: linear-gradient(135deg, #ffd46c, #ff9a4d);
}

.action-btn--view {
  background: linear-gradient(135deg, #88e7ff, #4bb9e6);
}

.action-btn--back {
  background: linear-gradient(135deg, #96c7ff, #6b8dff);
}

.action-btn--demo {
  background: linear-gradient(135deg, #ff9f87, #ff6f7c);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}

.panel-header h3,
.trend-title h3 {
  margin: 0;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.detail-item {
  padding: 12px;
  border-radius: 18px;
  background: var(--bg-elevated);
  border: 1px solid rgba(99, 195, 255, 0.12);
}

.detail-item span {
  color: var(--text-secondary);
}

.detail-item strong {
  display: block;
  margin-top: 6px;
}

.detail-item--focus strong {
  font-size: 18px;
}

.card-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 160px;
  border-radius: 18px;
  border: 1px dashed rgba(99, 195, 255, 0.16);
  background: rgba(10, 27, 43, 0.3);
  color: var(--text-secondary);
}

.card-state.subtle {
  min-height: 96px;
}

.bottom-grid {
  min-height: 0;
}

.trend-card {
  display: flex;
  flex-direction: column;
}

.trend-panel-header {
  margin-bottom: 6px;
}

.trend-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.focus-panel {
  min-height: 0;
}

.focus-panel :deep(.panel-body.scrollable) {
  scrollbar-width: thin;
  scrollbar-color: rgba(104, 214, 255, 0.58) rgba(8, 25, 40, 0.32);
}

.focus-panel :deep(.panel-body.scrollable::-webkit-scrollbar) {
  width: 6px;
}

.focus-panel :deep(.panel-body.scrollable::-webkit-scrollbar-track) {
  background: rgba(8, 25, 40, 0.26);
  border-radius: 999px;
}

.focus-panel :deep(.panel-body.scrollable::-webkit-scrollbar-thumb) {
  background: linear-gradient(180deg, rgba(104, 214, 255, 0.9), rgba(77, 141, 255, 0.76));
  border-radius: 999px;
}

.focus-caption {
  margin-bottom: 12px;
  color: var(--text-secondary);
  font-size: 13px;
}

.focus-grid {
  margin-bottom: 12px;
}

.focus-weather {
  padding-top: 12px;
  border-top: 1px solid rgba(99, 195, 255, 0.1);
}

.sub-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}

.weather-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.weather-item {
  padding: 12px;
  border-radius: 16px;
  background: rgba(9, 26, 46, 0.78);
  border: 1px solid rgba(99, 195, 255, 0.12);
}

.weather-item span {
  color: var(--text-secondary);
}

.weather-item strong {
  display: block;
  margin-top: 8px;
}

.trend-messages {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.trend-messages span {
  max-width: 420px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(17, 40, 64, 0.44);
  color: var(--text-secondary);
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.trend-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  min-height: 0;
}

.trend-pane {
  min-width: 0;
}

.trend-pane-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 4px;
}

.trend-pane-header strong {
  font-weight: 600;
}

.timeline-box {
  margin-top: 6px;
}

.rank-card {
  display: flex;
  flex-direction: column;
}

.stage-shell {
  position: relative;
}

.stage-shell > *:not(.stage-aura):not(.stage-scan):not(.stage-corners) {
  position: relative;
  z-index: 2;
}

.stage-aura,
.stage-scan,
.stage-corners {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.stage-aura {
  z-index: 0;
  inset: -8px;
  border-radius: 30px;
  border: 1px solid rgba(107, 214, 255, 0.22);
  box-shadow:
    0 0 0 1px rgba(96, 212, 255, 0.08) inset,
    0 0 28px rgba(59, 181, 255, 0.18),
    0 0 72px rgba(41, 120, 255, 0.12);
  animation: stagePulse 4.8s ease-in-out infinite;
}

.stage-scan {
  z-index: 1;
  inset: -24% -10%;
  background:
    radial-gradient(circle at 50% 50%, rgba(61, 208, 255, 0.1), transparent 46%),
    linear-gradient(110deg, transparent 18%, rgba(105, 225, 255, 0.12) 50%, transparent 82%);
  opacity: 0.72;
  animation: stageSweep 6.5s linear infinite;
}

.stage-corners {
  z-index: 3;
}

.stage-corner {
  position: absolute;
  width: 52px;
  height: 52px;
  border-color: rgba(126, 220, 255, 0.78);
  filter: drop-shadow(0 0 10px rgba(73, 197, 255, 0.28));
}

.stage-corner.top-left {
  top: 8px;
  left: 8px;
  border-top: 2px solid;
  border-left: 2px solid;
  border-top-left-radius: 16px;
}

.stage-corner.top-right {
  top: 8px;
  right: 8px;
  border-top: 2px solid;
  border-right: 2px solid;
  border-top-right-radius: 16px;
}

.stage-corner.bottom-left {
  bottom: 8px;
  left: 8px;
  border-bottom: 2px solid;
  border-left: 2px solid;
  border-bottom-left-radius: 16px;
}

.stage-corner.bottom-right {
  right: 8px;
  bottom: 8px;
  border-right: 2px solid;
  border-bottom: 2px solid;
  border-bottom-right-radius: 16px;
}

.rank-chart-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding-right: 4px;
  scrollbar-width: thin;
  scrollbar-color: rgba(104, 214, 255, 0.58) rgba(8, 25, 40, 0.32);
}

.rank-chart-scroll::-webkit-scrollbar {
  width: 6px;
}

.rank-chart-scroll::-webkit-scrollbar-track {
  background: rgba(8, 25, 40, 0.26);
  border-radius: 999px;
}

.rank-chart-scroll::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, rgba(104, 214, 255, 0.9), rgba(77, 141, 255, 0.76));
  border-radius: 999px;
}

@keyframes stagePulse {
  0%,
  100% {
    box-shadow:
      0 0 0 1px rgba(96, 212, 255, 0.08) inset,
      0 0 22px rgba(59, 181, 255, 0.16),
      0 0 60px rgba(41, 120, 255, 0.08);
    transform: scale(1);
  }
  50% {
    box-shadow:
      0 0 0 1px rgba(96, 212, 255, 0.12) inset,
      0 0 34px rgba(59, 181, 255, 0.2),
      0 0 86px rgba(41, 120, 255, 0.14);
    transform: scale(1.004);
  }
}

@keyframes stageSweep {
  0% {
    transform: translateX(-8%) translateY(-2%);
  }
  50% {
    transform: translateX(8%) translateY(2%);
  }
  100% {
    transform: translateX(-8%) translateY(-2%);
  }
}

.header-filters :deep(.el-input__wrapper),
.header-filters :deep(.el-select__wrapper),
.header-filters :deep(.el-segmented) {
  background: rgba(8, 24, 41, 0.86);
  box-shadow: inset 0 0 0 1px rgba(99, 195, 255, 0.1);
}

.header-filters :deep(.el-input__wrapper),
.header-filters :deep(.el-select__wrapper) {
  border-radius: 14px;
}

.header-filters :deep(.el-segmented) {
  padding: 4px;
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
    opacity: 0.8;
  }
  50% {
    transform: scale(1.15);
    opacity: 1;
  }
}

@media (max-width: 1600px) {
  .screen-grid {
    grid-template-columns: minmax(260px, 0.92fr) minmax(0, 4.2fr) minmax(280px, 1fr);
  }

  .header-controls {
    grid-template-columns: minmax(0, 1fr) 316px;
  }
}

@media (max-width: 1360px) {
  .screen-page {
    height: auto;
    min-height: 100vh;
    overflow: auto;
    grid-template-rows: auto auto auto;
  }

  .screen-grid {
    grid-template-columns: 1fr;
  }

  .screen-header {
    grid-template-columns: 1fr;
  }

  .header-controls {
    grid-template-columns: 1fr;
  }

  .action-group,
  .trend-grid,
  .filter-group {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
