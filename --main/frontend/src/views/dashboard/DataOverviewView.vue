<template>
  <div class="page-shell data-overview-page">
    <transition name="fade-slide">
      <div v-if="loading" class="loading-banner">
        <span class="loading-dot"></span>
        <strong>正在刷新数据展示</strong>
        <small>卡片、图表和热点摘要会一起联动更新</small>
      </div>
    </transition>

    <GlassPanel compact title="筛选">
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
        <div class="filter-actions">
          <el-button type="primary" @click="loadPageData">应用</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </div>
      </div>
    </GlassPanel>

    <section class="stat-grid">
      <StatCard label="火点总数" :value="formatNumber(overview.total_fire_points)" :loading="loading" icon="DataAnalysis" />
      <StatCard label="高置信度火点" :value="formatNumber(overview.high_confidence_fire_points)" :loading="loading" icon="WarningFilled" />
      <StatCard label="夜间火点" :value="formatNumber(overview.night_fire_points)" :loading="loading" icon="MoonNight" />
      <StatCard label="最大 FRP" :value="formatMetric(overview.max_frp)" :loading="loading" icon="Lightning" />
    </section>

    <section class="main-grid">
      <GlassPanel :title="trendTitle" :loading="loading" loading-text="趋势加载中">
        <BaseChart :option="trendOption" :height="320" :loading="loading" loading-text="趋势加载中" />
      </GlassPanel>
      <GlassPanel title="国家火点 Top10" :loading="loading" loading-text="排行加载中">
        <BaseChart :option="countryTopOption" :height="320" :loading="loading" loading-text="排行加载中" />
      </GlassPanel>
    </section>

    <section class="structure-grid">
      <GlassPanel title="数据源占比" :loading="loading" loading-text="占比加载中">
        <BaseChart :option="sourceProductOption" :height="300" :loading="loading" loading-text="占比加载中" />
      </GlassPanel>
      <GlassPanel title="昼夜占比" :loading="loading" loading-text="占比加载中">
        <BaseChart :option="daynightOption" :height="300" :loading="loading" loading-text="占比加载中" />
      </GlassPanel>
      <GlassPanel title="FRP 分布" :loading="loading" loading-text="FRP 分布加载中">
        <BaseChart :option="frpOption" :height="300" :loading="loading" loading-text="FRP 分布加载中" />
      </GlassPanel>
    </section>

    <section class="supplement-grid">
      <GlassPanel title="热点区域摘要" scrollable :loading="loading" loading-text="热点摘要加载中">
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

      <GlassPanel title="当前结果摘要" :loading="loading" loading-text="摘要加载中">
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
import { computed, onMounted, reactive, ref } from 'vue'

import { analysisApi, fireApi, hotspotApi } from '@/api/service'
import BaseChart from '@/components/BaseChart.vue'
import GlassPanel from '@/components/GlassPanel.vue'
import StatCard from '@/components/StatCard.vue'
import { useUiStore } from '@/stores/ui'
import { AREA_PRESETS, SOURCE_PRODUCT_PRESETS, TIME_PRESET_OPTIONS, buildDateParams, normalizeOptionList } from '@/utils/fireDataConfig'
import { formatDateTime, formatNumber } from '@/utils/format'

const uiStore = useUiStore()

const filters = reactive({
  timePreset: '7d',
  customRange: [],
  area_label: 'world',
  source_product: '',
})

const filterOptions = ref({
  area_labels: [],
  source_products: [],
  date_max: null,
})

const latestReference = ref(dayjs())
const loading = ref(false)

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
const frpDistribution = ref([])
const hotspots = ref([])

const timePresetOptions = TIME_PRESET_OPTIONS
const areaOptions = computed(() => normalizeOptionList(filterOptions.value.area_labels, AREA_PRESETS))
const sourceProductOptions = computed(() =>
  [{ value: '', label: '全部数据源' }, ...normalizeOptionList(filterOptions.value.source_products, SOURCE_PRODUCT_PRESETS)],
)

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
}))

const trendTitle = computed(() => `火点趋势（${dateParams.value.days}天）`)

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
  accentGreen: themeToken('--accent-green', '#39d398'),
  gridLine: uiStore.themeMode === 'light' ? 'rgba(37, 102, 186, 0.1)' : 'rgba(99,195,255,0.08)',
  axisLine: uiStore.themeMode === 'light' ? 'rgba(37, 102, 186, 0.16)' : 'rgba(99,195,255,0.18)',
}))

const formatMetric = (value) => {
  const numeric = Number(value)
  return Number.isFinite(numeric) ? numeric.toFixed(2) : '--'
}

const formatSourceProduct = (value) => SOURCE_PRODUCT_PRESETS[value]?.label || value || '未标注'
const formatDaynight = (value) => (value === 'D' ? '白天' : value === 'N' ? '夜间' : value || '未知')

const pieOption = (data, colors) => ({
  backgroundColor: 'transparent',
  color: colors,
  tooltip: {
    trigger: 'item',
    formatter: (params) => `${params.name}<br/>${formatNumber(params.value)} 条`,
  },
  legend: {
    bottom: 0,
    textStyle: { color: chartPalette.value.textSecondary },
    itemWidth: 12,
    itemHeight: 12,
  },
  series: [
    {
      type: 'pie',
      radius: ['42%', '72%'],
      center: ['50%', '46%'],
      label: { color: chartPalette.value.textPrimary, formatter: '{b}' },
      data,
      emphasis: {
        scale: true,
        scaleSize: 8,
      },
    },
  ],
})

const trendOption = computed(() => ({
  textStyle: { color: chartPalette.value.textPrimary },
  grid: { left: 44, right: 18, top: 28, bottom: 28 },
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
      symbolSize: 7,
      data: timeline.value.map((item) => item.value),
      lineStyle: { width: 3, color: chartPalette.value.accentCyan },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: `${chartPalette.value.accentCyan}66` },
          { offset: 1, color: `${chartPalette.value.accentCyan}0a` },
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
        color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
          { offset: 0, color: chartPalette.value.accentCyan },
          { offset: 1, color: chartPalette.value.accentBlue },
        ]),
        borderRadius: [0, 12, 12, 0],
      },
    },
  ],
}))

const sourceProductOption = computed(() =>
  pieOption(
    sourceProductPie.value.map((item) => ({
      name: formatSourceProduct(item.name),
      value: item.value,
    })),
    [chartPalette.value.accentCyan, chartPalette.value.accentOrange, chartPalette.value.accentBlue],
  ),
)

const daynightOption = computed(() =>
  pieOption(
    daynightPie.value.map((item) => ({
      name: formatDaynight(item.name),
      value: item.value,
    })),
    [chartPalette.value.accentOrange, chartPalette.value.accentBlue],
  ),
)

const frpOption = computed(() => ({
  textStyle: { color: chartPalette.value.textPrimary },
  grid: { left: 42, right: 18, top: 28, bottom: 28 },
  tooltip: { trigger: 'axis' },
  xAxis: {
    type: 'category',
    data: frpDistribution.value.map((item) => item.name),
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
      data: frpDistribution.value.map((item) => item.value),
      itemStyle: {
        color: chartPalette.value.accentOrange,
        borderRadius: [10, 10, 0, 0],
      },
    },
  ],
}))

const summaryItems = computed(() => [
  { label: '时间范围', value: `${dateParams.value.start_date} 至 ${dateParams.value.end_date}` },
  { label: '当前区域', value: AREA_PRESETS[filters.area_label]?.label || filters.area_label || '全部区域' },
  { label: '当前数据源', value: formatSourceProduct(filters.source_product || '全部') },
  { label: '最新更新时间', value: formatDateTime(overview.latest_update) },
  { label: '热点摘要数', value: formatNumber(hotspots.value.length) },
  { label: 'Top10 国家覆盖', value: formatNumber(countryTop.value.length) },
])

const loadFilterOptions = async () => {
  filterOptions.value = await fireApi.filterOptions()
  latestReference.value = filterOptions.value.date_max ? dayjs(filterOptions.value.date_max) : dayjs()
}

const loadPageData = async () => {
  loading.value = true
  try {
    const params = queryParams.value
    const [overviewData, timelineData, countryTopData, sourceProductData, daynightData, frpData, hotspotData] =
      await Promise.all([
        analysisApi.overview(params),
        analysisApi.timeline({ days: dateParams.value.days, ...params }),
        analysisApi.countryTop({ limit: 10, ...params }),
        analysisApi.sourceProductPie(params),
        analysisApi.daynightPie(params),
        analysisApi.frpDistribution(params),
        hotspotApi.top({ window: dateParams.value.window, limit: 8, ...params }),
      ])

    Object.assign(overview, overviewData)
    timeline.value = timelineData
    countryTop.value = countryTopData
    sourceProductPie.value = sourceProductData
    daynightPie.value = daynightData
    frpDistribution.value = frpData
    hotspots.value = hotspotData
  } finally {
    loading.value = false
  }
}

const resetFilters = async () => {
  filters.timePreset = '7d'
  filters.customRange = []
  filters.area_label = 'world'
  filters.source_product = ''
  await loadPageData()
}

onMounted(async () => {
  loading.value = true
  try {
    await loadFilterOptions()
    await loadPageData()
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.data-overview-page {
  position: relative;
  padding-bottom: 8px;
}

.loading-banner {
  position: sticky;
  top: 0;
  z-index: 12;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 16px;
  border: 1px solid var(--line-soft);
  background: linear-gradient(135deg, rgba(10, 31, 52, 0.96), rgba(12, 42, 68, 0.92));
  box-shadow: 0 18px 32px rgba(0, 0, 0, 0.2);
}

.loading-banner strong {
  font-size: 14px;
}

.loading-banner small {
  color: var(--text-secondary);
}

.loading-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent-cyan), var(--accent-orange));
  box-shadow: 0 0 0 8px rgba(89, 214, 255, 0.08);
  animation: loadingPulse 1.2s ease-in-out infinite;
}

.filters {
  display: grid;
  grid-template-columns: 1.4fr 1.2fr 1fr 1fr auto;
  gap: 12px;
}

.filter-actions {
  display: flex;
  gap: 10px;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.main-grid {
  display: grid;
  grid-template-columns: 1.35fr 1fr;
  gap: 16px;
}

.structure-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.supplement-grid {
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  gap: 16px;
}

.hotspot-list {
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

.summary-list {
  display: grid;
  gap: 12px;
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

@keyframes loadingPulse {
  0%,
  100% {
    transform: scale(0.9);
    opacity: 0.76;
  }
  50% {
    transform: scale(1.1);
    opacity: 1;
  }
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.22s ease;
}

.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

@media (max-width: 1280px) {
  .filters,
  .stat-grid,
  .main-grid,
  .structure-grid,
  .supplement-grid {
    grid-template-columns: 1fr;
  }

  .filter-actions {
    justify-content: flex-end;
  }
}
</style>
