<template>
  <div class="map-page">
    <div class="map-stage">
      <CesiumMap
        ref="mapRef"
        :points="displayPoints"
        :hotspots="activeHotspots"
        :heatmap-points="currentDayPoints"
        :choropleth="choropleth"
        :selected-country="selectedCountry"
        :initial-view="areaViewKey"
        :show-countries="false"
        :show-fire-points="layers.showFirePoints"
        :cluster-fire-points="false"
        :show-hotspots="layers.showHotspots"
        :show-heatmap="layers.showHeatmap"
        @select-fire="handleSelectFire"
        @select-hotspot="handleSelectHotspot"
        @select-country="handleSelectCountry"
      />
    </div>

    <aside class="left-panel">
      <GlassPanel title="筛选" compact>
        <div class="stack">
          <el-segmented v-model="filters.timePreset" :options="timePresetOptions" />
          <el-date-picker
            v-if="filters.timePreset === 'custom'"
            v-model="filters.customRange"
            type="daterange"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
          />
          <div class="compact-row">
            <el-select v-model="filters.area_label" clearable placeholder="区域">
              <el-option v-for="item in areaOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
            <el-select v-model="filters.source_product" clearable placeholder="数据源">
              <el-option v-for="item in sourceProductOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </div>
          <div class="compact-row">
            <el-select v-model="filters.satellite" clearable placeholder="卫星">
              <el-option v-for="item in satelliteOptions" :key="item" :label="item" :value="item" />
            </el-select>
            <el-input v-model="filters.country_name" placeholder="国家" clearable />
          </div>
          <div class="toolbar-row">
            <div class="switch-row">
              <span>火点</span>
              <el-switch v-model="layers.showFirePoints" />
            </div>
            <div class="switch-row">
              <span>热点</span>
              <el-switch v-model="layers.showHotspots" />
            </div>
          </div>
          <div class="toolbar-row single-row">
            <div class="switch-row">
              <span>热力图</span>
              <el-switch v-model="layers.showHeatmap" />
            </div>
          </div>
          <div class="action-row">
            <el-button type="primary" @click="applyFilters">应用</el-button>
            <el-button @click="resetFilters">重置</el-button>
          </div>
        </div>
      </GlassPanel>

      <GlassPanel title="热点排行" compact scrollable class="grow-panel">
        <div class="hotspot-list">
          <button
            v-for="item in activeHotspots.slice(0, 8)"
            :key="item.id"
            class="hotspot-row"
            @click="focusHotspot(item)"
          >
            <div>
              <strong>{{ item.major_country || item.id }}</strong>
              <span>{{ item.fire_count }} 个火点</span>
            </div>
            <b>{{ item.max_frp }}</b>
          </button>
          <div v-if="!activeHotspots.length" class="empty-tip">当前日期暂无热点区域</div>
        </div>
      </GlassPanel>
    </aside>

    <aside class="right-panel">
      <GlassPanel title="统计" compact>
        <div class="summary-grid">
          <div class="summary-item">
            <span>当前火点</span>
            <strong>{{ displayPoints.length }}</strong>
          </div>
          <div class="summary-item">
            <span>热点数量</span>
            <strong>{{ activeHotspots.length }}</strong>
          </div>
          <div class="summary-item">
            <span>区域</span>
            <strong>{{ currentAreaLabel }}</strong>
          </div>
          <div class="summary-item">
            <span>数据源</span>
            <strong>{{ currentSourceLabel }}</strong>
          </div>
          <div class="summary-item">
            <span>时间刻度</span>
            <strong>{{ timelineOptions[currentIndex]?.shortLabel || '--' }}</strong>
          </div>
          <div class="summary-item">
            <span>国家</span>
            <strong>{{ selectedCountry || '全域' }}</strong>
          </div>
        </div>
      </GlassPanel>

      <GlassPanel v-if="selectedFire" title="火点详情" compact>
        <div class="detail-grid">
          <div class="detail-item"><span>国家</span><strong>{{ selectedFire.country_name || '未知' }}</strong></div>
          <div class="detail-item"><span>时间</span><strong>{{ formatDateTime(selectedFire.acq_datetime) }}</strong></div>
          <div class="detail-item"><span>数据源</span><strong>{{ sourceProductLabel(selectedFire.source_product) }}</strong></div>
          <div class="detail-item"><span>FRP</span><strong>{{ selectedFire.frp ?? '--' }}</strong></div>
          <div class="detail-item"><span>昼夜</span><strong>{{ selectedFire.daynight || '--' }}</strong></div>
          <div class="detail-item"><span>区域</span><strong>{{ areaLabel(selectedFire.area_label) }}</strong></div>
        </div>
        <div class="detail-actions">
          <el-button type="primary" size="small" @click="openSelectedFireDetail">查看详情页</el-button>
        </div>
      </GlassPanel>

      <WeatherCard title="天气" :weather="weather" :loading="weatherLoading" />
      <HotspotDetailPanel v-if="hotspotDetail" :hotspot="hotspotDetail" />

      <GlassPanel v-if="countryDetail" title="国家摘要" compact>
        <div class="summary-grid">
          <div class="summary-item"><span>火点总数</span><strong>{{ countryDetail.total_fire_points }}</strong></div>
          <div class="summary-item"><span>高置信度</span><strong>{{ countryDetail.high_confidence_fire_points }}</strong></div>
          <div class="summary-item"><span>夜间火点</span><strong>{{ countryDetail.night_fire_points }}</strong></div>
          <div class="summary-item"><span>最大 FRP</span><strong>{{ countryDetail.max_frp?.toFixed?.(2) || countryDetail.max_frp }}</strong></div>
        </div>
      </GlassPanel>
    </aside>

    <div class="timeline-dock">
      <TimePlayback
        v-model="currentIndex"
        :options="timelineOptions"
        :interval="3200"
        granularity="day"
        :show-granularity-toggle="false"
        :show-tick-labels="true"
        tick-label-mode="all"
      />
    </div>
  </div>
</template>

<script setup>
import dayjs from 'dayjs'
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { analysisApi, fireApi, weatherApi } from '@/api/service'
import CesiumMap from '@/components/CesiumMap.vue'
import GlassPanel from '@/components/GlassPanel.vue'
import HotspotDetailPanel from '@/components/HotspotDetailPanel.vue'
import TimePlayback from '@/components/TimePlayback.vue'
import WeatherCard from '@/components/WeatherCard.vue'
import {
  AREA_PRESETS,
  SOURCE_PRODUCT_PRESETS,
  TIME_PRESET_OPTIONS,
  buildDateParams,
  normalizeOptionList,
  resolveAreaView,
} from '@/utils/fireDataConfig'
import { formatDateTime } from '@/utils/format'

const MAP_FETCH_LIMITS = {
  world: { '7d': 3200, '30d': 3800, custom: 3200 },
  default: { '7d': 2600, '30d': 3200, custom: 2600 },
}

const MAP_DISPLAY_LIMIT = 1400
const HOTSPOT_GRID_SIZE = 1.6
const HOTSPOT_LIMIT = 12

const buildLocalHotspots = (points, areaLabel, limit = HOTSPOT_LIMIT) => {
  const buckets = new Map()
  points.forEach((item) => {
    const latitude = Number(item.latitude)
    const longitude = Number(item.longitude)
    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return

    const latIndex = Math.floor((latitude + 90) / HOTSPOT_GRID_SIZE)
    const lonIndex = Math.floor((longitude + 180) / HOTSPOT_GRID_SIZE)
    const key = `${latIndex}:${lonIndex}`
    if (!buckets.has(key)) {
      buckets.set(key, {
        id: `local:${dayjs(item.acq_datetime).format('YYYYMMDD')}:${latIndex}:${lonIndex}`,
        rowIds: [],
        latitudeSum: 0,
        longitudeSum: 0,
        fireCount: 0,
        frpSum: 0,
        frpCount: 0,
        maxFrp: 0,
        countries: new Map(),
        timeStart: item.acq_datetime,
        timeEnd: item.acq_datetime,
        area_label: areaLabel,
        source_product: item.source_product || '',
      })
    }

    const bucket = buckets.get(key)
    bucket.rowIds.push(item.id)
    bucket.latitudeSum += latitude
    bucket.longitudeSum += longitude
    bucket.fireCount += 1
    if (Number.isFinite(Number(item.frp))) {
      bucket.frpSum += Number(item.frp)
      bucket.frpCount += 1
      bucket.maxFrp = Math.max(bucket.maxFrp, Number(item.frp))
    }
    if (item.country_name) {
      bucket.countries.set(item.country_name, (bucket.countries.get(item.country_name) || 0) + 1)
    }
    bucket.timeStart = bucket.timeStart < item.acq_datetime ? bucket.timeStart : item.acq_datetime
    bucket.timeEnd = bucket.timeEnd > item.acq_datetime ? bucket.timeEnd : item.acq_datetime
  })

  return Array.from(buckets.values())
    .filter((item) => item.fireCount >= 4)
    .map((item) => ({
      id: item.id,
      center_latitude: Number((item.latitudeSum / item.fireCount).toFixed(4)),
      center_longitude: Number((item.longitudeSum / item.fireCount).toFixed(4)),
      fire_count: item.fireCount,
      avg_frp: item.frpCount ? Number((item.frpSum / item.frpCount).toFixed(2)) : 0,
      max_frp: Number(item.maxFrp.toFixed(2)),
      major_country:
        Array.from(item.countries.entries()).sort((a, b) => b[1] - a[1])[0]?.[0] || null,
      time_start: item.timeStart,
      time_end: item.timeEnd,
      area_label: item.area_label,
      source_product: item.source_product,
      sample_fire_ids: item.rowIds.slice(0, 12),
    }))
    .sort((a, b) => (b.fire_count - a.fire_count) || (b.max_frp - a.max_frp))
    .slice(0, limit)
}

const mapRef = ref()
const router = useRouter()
const timelineSeries = ref([])
const currentDayPoints = ref([])
const dayPointCache = new Map()
const preferredTimelineDate = ref('')
const suppressTimelineWatcher = ref(false)
const timelineSelectionVersion = ref(0)
const hotspotDetail = ref(null)
const selectedFire = ref(null)
const selectedCountry = ref('')
const countryDetail = ref(null)
const weather = ref(null)
const weatherLoading = ref(false)
const latestReference = ref(dayjs())
const filterOptions = ref({
  area_labels: [],
  source_products: [],
  satellites: [],
})

const currentIndex = ref(0)
const filters = reactive({
  timePreset: '7d',
  customRange: [],
  area_label: 'seasia',
  source_product: '',
  satellite: '',
  country_name: '',
})

const layers = reactive({
  showFirePoints: true,
  showHotspots: true,
  showHeatmap: false,
})

const choropleth = ref([])
let mapLoadRequestId = 0
let pointLoadRequestId = 0

const timePresetOptions = TIME_PRESET_OPTIONS.filter((item) => item.value !== '1d')
const areaOptions = computed(() => normalizeOptionList(filterOptions.value.area_labels, AREA_PRESETS))
const sourceProductOptions = computed(() => normalizeOptionList(filterOptions.value.source_products, SOURCE_PRODUCT_PRESETS))
const satelliteOptions = computed(() => filterOptions.value.satellites || [])
const areaViewKey = computed(() => resolveAreaView(filters.area_label))
const currentAreaLabel = computed(() => AREA_PRESETS[filters.area_label]?.label || filters.area_label || '全域')
const currentSourceLabel = computed(() => SOURCE_PRODUCT_PRESETS[filters.source_product]?.label || filters.source_product || '全部')

const dateParams = computed(() =>
  buildDateParams({
    preset: filters.timePreset,
    customRange: filters.customRange,
    latestReference: latestReference.value,
  }),
)

const queryParams = computed(() => ({
  start_date: dateParams.value.start_date,
  end_date: dateParams.value.end_date,
  area_label: filters.area_label || undefined,
  source_product: filters.source_product || undefined,
  satellite: filters.satellite || undefined,
  country_name: filters.country_name || selectedCountry.value || undefined,
}))

const timelineOptions = computed(() => {
  return timelineSeries.value.map((item) => ({
    value: item.date,
    label: `${item.date} · ${item.value} 个火点`,
    shortLabel: dayjs(item.date).format('MM-DD'),
  }))
})

const displayPoints = computed(() => currentDayPoints.value.slice(0, MAP_DISPLAY_LIMIT))
const activeHotspots = computed(() => buildLocalHotspots(currentDayPoints.value, filters.area_label))

const areaLabel = (value) => AREA_PRESETS[value]?.label || value || '--'
const sourceProductLabel = (value) => SOURCE_PRODUCT_PRESETS[value]?.label || value || '--'

const loadFilterOptions = async () => {
  filterOptions.value = await fireApi.filterOptions()
  latestReference.value = filterOptions.value.date_max ? dayjs(filterOptions.value.date_max) : dayjs()
}

const resolveFetchLimit = () => {
  const group = filters.area_label === 'world' ? MAP_FETCH_LIMITS.world : MAP_FETCH_LIMITS.default
  return group[filters.timePreset] || group.custom
}

const buildDayCacheKey = (dateText) =>
  [
    dateText,
    filters.area_label || '',
    filters.source_product || '',
    filters.satellite || '',
    filters.country_name || selectedCountry.value || '',
  ].join('|')

const loadChoropleth = async () => {
  choropleth.value = await analysisApi.countryChoropleth({
    metric: 'count',
    ...queryParams.value,
  })
}

const loadPointsForDate = async (dateText, { force = false } = {}) => {
  if (!dateText) {
    currentDayPoints.value = []
    return
  }

  const cacheKey = buildDayCacheKey(dateText)
  if (!force && dayPointCache.has(cacheKey)) {
    currentDayPoints.value = dayPointCache.get(cacheKey)
    return
  }

  const requestId = ++pointLoadRequestId
  const payload = await fireApi.range({
    start: dayjs(dateText).startOf('day').toISOString(),
    end: dayjs(dateText).endOf('day').toISOString(),
    limit: resolveFetchLimit(),
    ...queryParams.value,
  })
  if (requestId !== pointLoadRequestId) return
  dayPointCache.set(cacheKey, payload || [])
  currentDayPoints.value = payload || []
}

const focusTimelineViewport = async () => {
  await nextTick()
  const hotspot = activeHotspots.value[0]
  if (hotspot) {
    mapRef.value?.flyToHotspot(hotspot, filters.area_label === 'world' ? 4200000 : 2400000)
    return
  }

  if (!currentDayPoints.value.length) return

  const validPoints = currentDayPoints.value
    .map((item) => ({
      longitude: Number(item.longitude),
      latitude: Number(item.latitude),
      frp: Number(item.frp || 0),
    }))
    .filter((item) => Number.isFinite(item.longitude) && Number.isFinite(item.latitude))

  if (!validPoints.length) return

  const focusCandidates = validPoints
    .sort((a, b) => b.frp - a.frp)
    .slice(0, Math.min(validPoints.length, 120))
  const centerLon = focusCandidates.reduce((sum, item) => sum + item.longitude, 0) / focusCandidates.length
  const centerLat = focusCandidates.reduce((sum, item) => sum + item.latitude, 0) / focusCandidates.length

  mapRef.value?.flyToCoordinates({
    longitude: centerLon,
    latitude: centerLat,
    height: filters.area_label === 'world' ? 5200000 : 2600000,
    duration: 1.85,
  })
}

const loadMapData = async ({ preserveTimeline = true } = {}) => {
  const requestId = ++mapLoadRequestId
  const previousDate = preserveTimeline
    ? preferredTimelineDate.value || timelineOptions.value[currentIndex.value]?.value || ''
    : ''
  const selectionVersionAtStart = timelineSelectionVersion.value

  timelineSeries.value = await analysisApi.timeline({
    days: dateParams.value.days,
    ...queryParams.value,
  })
  if (requestId !== mapLoadRequestId) return

  const guardedDate = preserveTimeline && timelineSelectionVersion.value !== selectionVersionAtStart
    ? preferredTimelineDate.value
    : previousDate

  const resolvedIndex = guardedDate
    ? timelineOptions.value.findIndex((item) => item.value === guardedDate)
    : -1
  const nextIndex = resolvedIndex >= 0 ? resolvedIndex : Math.max(timelineOptions.value.length - 1, 0)
  const nextDate = timelineOptions.value[nextIndex]?.value || ''

  suppressTimelineWatcher.value = true
  currentIndex.value = nextIndex
  preferredTimelineDate.value = nextDate
  await nextTick()
  suppressTimelineWatcher.value = false
  await loadPointsForDate(nextDate, { force: requestId === mapLoadRequestId })
  if (requestId !== mapLoadRequestId) return

  await loadChoropleth()
}

const fetchCountryDetail = async (country) => {
  if (!country) {
    countryDetail.value = null
    return
  }
  countryDetail.value = await analysisApi.countryDetail({
    country,
    ...queryParams.value,
  })
}

const loadWeatherForCoordinates = async (latitude, longitude) => {
  if (!Number.isFinite(Number(latitude)) || !Number.isFinite(Number(longitude))) {
    weather.value = null
    return
  }
  weatherLoading.value = true
  try {
    weather.value = await weatherApi.point({
      latitude,
      longitude,
    })
  } finally {
    weatherLoading.value = false
  }
}

const handleSelectFire = async (payload) => {
  selectedFire.value = payload
  hotspotDetail.value = null
  if (!payload) {
    weather.value = null
    return
  }
  await loadWeatherForCoordinates(payload.latitude, payload.longitude)
}

const openSelectedFireDetail = () => {
  if (!selectedFire.value?.id) return
  router.push(`/fire-detail/${selectedFire.value.id}`)
}

const focusHotspot = async (payload) => {
  if (!payload) {
    hotspotDetail.value = null
    weather.value = null
    return
  }
  hotspotDetail.value = payload
  selectedFire.value = null
  await loadWeatherForCoordinates(payload.center_latitude, payload.center_longitude)
  mapRef.value?.flyToHotspot(payload, filters.area_label === 'world' ? 4200000 : 2600000)
}

const handleSelectHotspot = async (payload) => {
  if (!payload) {
    hotspotDetail.value = null
    weather.value = null
    return
  }
  await focusHotspot(payload)
}

const handleSelectCountry = async (payload) => {
  const nextCountry = payload?.name || ''
  if (nextCountry === selectedCountry.value) return
  selectedCountry.value = nextCountry
  filters.country_name = nextCountry
  await fetchCountryDetail(selectedCountry.value)
}

const applyFilters = async () => {
  selectedCountry.value = filters.country_name || ''
  countryDetail.value = null
  selectedFire.value = null
  hotspotDetail.value = null
  weather.value = null
  preferredTimelineDate.value = ''
  await loadMapData({ preserveTimeline: false })
  if (selectedCountry.value) {
    await fetchCountryDetail(selectedCountry.value)
  }
}

const resetFilters = async () => {
  filters.timePreset = '7d'
  filters.customRange = []
  filters.area_label = 'seasia'
  filters.source_product = ''
  filters.satellite = ''
  filters.country_name = ''
  selectedCountry.value = ''
  selectedFire.value = null
  hotspotDetail.value = null
  weather.value = null
  countryDetail.value = null
  preferredTimelineDate.value = ''
  await loadMapData({ preserveTimeline: false })
}

watch(
  () => filters.area_label,
  () => {
    currentIndex.value = 0
  },
)

watch(currentIndex, async () => {
  if (suppressTimelineWatcher.value) return
  timelineSelectionVersion.value += 1
  const nextDate = timelineOptions.value[currentIndex.value]?.value
  if (!nextDate) return
  preferredTimelineDate.value = nextDate
  selectedFire.value = null
  hotspotDetail.value = null
  weather.value = null
  await loadPointsForDate(nextDate)
  await focusTimelineViewport()
})

onMounted(async () => {
  await loadFilterOptions()
  await loadMapData()
})
</script>

<style scoped>
.map-page {
  position: relative;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  border-radius: 26px;
}

.map-stage {
  position: absolute;
  inset: 0;
  overflow: hidden;
  border-radius: 26px;
}

.left-panel,
.right-panel {
  position: absolute;
  top: 12px;
  bottom: 76px;
  z-index: 4;
  width: clamp(232px, 16vw, 280px);
  display: flex;
  flex-direction: column;
  gap: 8px;
  pointer-events: auto;
  min-height: 0;
}

.left-panel {
  left: 12px;
  overflow: hidden;
}

.right-panel {
  right: 12px;
  overflow: auto;
  padding-right: 2px;
}

.left-panel > *,
.right-panel > * {
  flex: 0 0 auto;
  min-height: 0;
}

.left-panel > :deep(.panel),
.right-panel > :deep(.panel) {
  height: auto;
}

.grow-panel {
  flex: 1 1 0;
  min-height: 280px;
}

.timeline-dock {
  position: absolute;
  left: 50%;
  bottom: 10px;
  z-index: 5;
  width: min(620px, calc(100% - 560px));
  transform: translateX(-50%);
}

.stack {
  display: grid;
  gap: 8px;
}

.compact-row,
.toolbar-row,
.action-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  border-radius: 14px;
  background: var(--bg-panel-strong);
  border: 1px solid rgba(99, 195, 255, 0.12);
}

.single-row {
  grid-template-columns: minmax(0, 1fr);
}

.summary-grid,
.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.summary-item,
.detail-item {
  padding: 9px 11px;
  border-radius: 16px;
  background: var(--bg-panel-strong);
  border: 1px solid rgba(99, 195, 255, 0.12);
}

.summary-item span,
.detail-item span,
.empty-tip {
  color: var(--text-secondary);
}

.summary-item strong,
.detail-item strong {
  display: block;
  margin-top: 6px;
  font-size: 13px;
}

.detail-actions {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
}

.hotspot-list {
  display: grid;
  gap: 6px;
}

.hotspot-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  padding: 9px 11px;
  color: var(--text-primary);
  text-align: left;
  border-radius: 16px;
  border: 1px solid rgba(99, 195, 255, 0.1);
  background: var(--bg-panel-strong);
  cursor: pointer;
}

.hotspot-row span {
  display: block;
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 11px;
}

.hotspot-row b {
  color: var(--accent-orange);
}

.empty-tip {
  padding: 10px 12px;
}

.left-panel :deep(.panel),
.right-panel :deep(.panel) {
  padding: 12px 14px;
  background: linear-gradient(180deg, rgba(7, 22, 39, 0.5), rgba(5, 17, 29, 0.26));
  backdrop-filter: blur(14px);
}

.left-panel :deep(.panel-header),
.right-panel :deep(.panel-header) {
  margin-bottom: 10px;
}

.timeline-dock :deep(.timeline-wrap) {
  background: linear-gradient(180deg, rgba(7, 22, 39, 0.48), rgba(5, 17, 29, 0.22));
  backdrop-filter: blur(14px);
}

@media (max-width: 1280px) {
  .left-panel,
  .right-panel {
    width: 240px;
  }

  .timeline-dock {
    width: min(560px, calc(100% - 500px));
  }
}
</style>
