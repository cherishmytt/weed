<template>
  <div class="page-shell overview-page">
    <section class="stat-grid">
      <StatCard label="累计火点" :value="formatNumber(overview.total_fire_points)" :loading="overviewLoading" icon="DataLine" />
      <StatCard label="今日火点" :value="formatNumber(overview.today_fire_points)" :loading="overviewLoading" icon="Sunny" />
      <StatCard label="高置信度火点" :value="formatNumber(overview.high_confidence_fire_points)" :loading="overviewLoading" icon="WarningFilled" />
      <StatCard label="最后更新" :value="formatDateTime(overview.latest_update, 'MM-DD HH:mm')" :loading="overviewLoading" icon="Clock" />
    </section>

    <section class="overview-grid">
      <GlassPanel ref="summaryPanelRef" title="监测摘要" scrollable :style="sharedPanelStyle" :loading="overviewLoading" loading-text="摘要加载中">
        <div ref="summaryContentRef" class="summary-grid">
          <article v-for="item in summaries" :key="item.title">
            <span>{{ item.title }}</span>
            <strong>{{ item.value }}</strong>
          </article>
        </div>
      </GlassPanel>

      <GlassPanel ref="hotspotPanelRef" title="热点国家" scrollable :style="sharedPanelStyle" :loading="overviewLoading" loading-text="热点国家加载中">
        <div ref="hotspotContentRef" class="feature-list">
          <article v-for="item in topCountries" :key="item.name">
            <h4>{{ item.name }}</h4>
            <p>{{ formatNumber(item.value) }} 个火点</p>
          </article>
          <article v-if="!topCountries.length">
            <h4>暂无热点国家</h4>
            <p>当前筛选条件下暂无统计结果</p>
          </article>
        </div>
      </GlassPanel>

      <GlassPanel ref="statusPanelRef" title="系统状态" scrollable :style="sharedPanelStyle" :loading="overviewLoading" loading-text="系统状态加载中">
        <div ref="statusContentRef" class="feature-list">
          <article v-for="item in statusItems" :key="item.title">
            <h4>{{ item.title }}</h4>
            <p>{{ item.value }}</p>
          </article>
        </div>
      </GlassPanel>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import GlassPanel from '@/components/GlassPanel.vue'
import StatCard from '@/components/StatCard.vue'
import { useOverviewStore } from '@/stores/overview'
import { formatDateTime, formatNumber } from '@/utils/format'

const overviewStore = useOverviewStore()
const summaryPanelRef = ref(null)
const hotspotPanelRef = ref(null)
const statusPanelRef = ref(null)
const summaryContentRef = ref(null)
const hotspotContentRef = ref(null)
const statusContentRef = ref(null)
const sharedPanelHeight = ref(0)
let panelResizeObserver = null

const emptyOverview = {
  total_fire_points: 0,
  today_fire_points: 0,
  high_confidence_fire_points: 0,
  night_fire_points: 0,
  max_frp: 0,
  latest_update: '',
}

const overview = computed(() => overviewStore.overview || emptyOverview)
const topCountries = computed(() => overviewStore.topCountries || [])
const overviewLoading = computed(() => overviewStore.loading && !overviewStore.hasData)

const summaries = computed(() => [
  { title: '累计火点', value: formatNumber(overview.value.total_fire_points) },
  { title: '今日火点', value: formatNumber(overview.value.today_fire_points) },
  { title: '高置信度火点', value: formatNumber(overview.value.high_confidence_fire_points) },
  { title: '夜间火点', value: formatNumber(overview.value.night_fire_points) },
  {
    title: '夜间占比',
    value:
      overview.value.total_fire_points > 0
        ? `${((overview.value.night_fire_points / overview.value.total_fire_points) * 100).toFixed(1)}%`
        : '--',
  },
  { title: '最大 FRP', value: overview.value.max_frp ? overview.value.max_frp.toFixed(2) : '--' },
  { title: '热点国家数', value: formatNumber(topCountries.value.length) },
  { title: '最后更新', value: formatDateTime(overview.value.latest_update, 'MM-DD HH:mm') },
])

const statusItems = computed(() => [
  { title: '数据更新', value: formatDateTime(overview.value.latest_update) },
  { title: '今日火点', value: formatNumber(overview.value.today_fire_points) },
  { title: '高置信度', value: formatNumber(overview.value.high_confidence_fire_points) },
  { title: '缓存状态', value: overviewStore.isFresh ? '已缓存' : '待刷新' },
])

const sharedPanelStyle = computed(() =>
  sharedPanelHeight.value > 0 ? { height: `${sharedPanelHeight.value}px` } : null,
)

const syncPanelHeights = async () => {
  sharedPanelHeight.value = 0
  await nextTick()
  const headers = [summaryPanelRef, hotspotPanelRef, statusPanelRef]
    .map((panelRef) => panelRef?.value?.$el?.querySelector?.('.panel-header')?.offsetHeight || 0)
    .filter((value) => value > 0)
  const headerBlock = headers.length ? Math.max(...headers) : 22
  const chromeHeight = 18 + 18 + 16 + headerBlock
  const heights = [summaryContentRef, hotspotContentRef, statusContentRef]
    .map((contentRef) => contentRef?.value?.scrollHeight || 0)
    .filter((value) => value > 0)

  if (!heights.length) return
  sharedPanelHeight.value = Math.max(Math.min(...heights) + chromeHeight, 240)
}

const observeElement = (element) => {
  if (element) {
    panelResizeObserver.observe(element)
  }
}

const syncPanelObservers = () => {
  panelResizeObserver?.disconnect()
  ;[
    summaryContentRef.value,
    hotspotContentRef.value,
    statusContentRef.value,
    summaryPanelRef.value?.$el,
    hotspotPanelRef.value?.$el,
    statusPanelRef.value?.$el,
  ]
    .filter(Boolean)
    .forEach(observeElement)
}

onMounted(async () => {
  overviewStore.load().catch(() => {})
  await nextTick()
  panelResizeObserver = new ResizeObserver(() => {
    syncPanelHeights().catch(() => {})
  })
  syncPanelObservers()
  await syncPanelHeights()
})

watch([summaries, topCountries, statusItems], () => {
  syncPanelObservers()
  syncPanelHeights().catch(() => {})
}, { deep: true })

onBeforeUnmount(() => {
  panelResizeObserver?.disconnect()
})
</script>

<style scoped>
.overview-page {
  display: grid;
  grid-template-rows: auto auto;
  height: 100%;
  min-height: 0;
  overflow-y: auto;
  padding-right: 4px;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  min-height: 0;
}

.overview-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr 1fr;
  gap: 18px;
  min-height: 0;
  align-items: start;
}

.feature-list {
  display: grid;
  gap: 14px;
  align-content: start;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.summary-grid article,
.feature-list article {
  padding: 18px;
  border-radius: 18px;
  border: 1px solid var(--line-soft);
  background: var(--bg-elevated);
}

.summary-grid span {
  color: var(--text-secondary);
}

.summary-grid strong {
  display: block;
  margin-top: 10px;
  font-size: 26px;
}

.feature-list h4 {
  margin: 0 0 10px;
}

.feature-list p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.8;
}

.overview-grid :deep(.panel) {
  height: 100%;
}

.overview-grid :deep(.panel-body) {
  height: calc(100% - 38px);
  overflow: auto;
}

@media (max-width: 1100px) {
  .stat-grid,
  .overview-grid {
    grid-template-columns: 1fr;
  }

  .overview-page {
    overflow: auto;
  }
}
</style>
