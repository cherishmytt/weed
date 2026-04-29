<template>
  <div class="page-shell fire-detail-page">
    <GlassPanel compact>
      <div class="page-head">
        <div class="head-left">
          <el-button class="ghost-btn" @click="router.back()">
            <el-icon><ArrowLeft /></el-icon>
            <span>返回</span>
          </el-button>
          <div class="head-title">
            <h2>火点详情</h2>
            <span v-if="firePoint">#{{ firePoint.id }} · {{ firePoint.country_name || '未知区域' }} · {{ formatDateTime(firePoint.acq_datetime) }}</span>
          </div>
        </div>
      </div>
    </GlassPanel>

    <transition name="fade-slide">
      <div v-if="loading" class="loading-banner">
        <span class="loading-dot"></span>
        <strong>火点详情加载中</strong>
        <small>正在获取火点信息、相关火点和天气数据</small>
      </div>
    </transition>

    <section class="detail-grid">
      <GlassPanel title="火点属性" scrollable>
        <div v-if="firePoint" class="meta-grid">
          <div class="meta-item"><span>纬度</span><strong>{{ firePoint.latitude }}</strong></div>
          <div class="meta-item"><span>经度</span><strong>{{ firePoint.longitude }}</strong></div>
          <div class="meta-item"><span>采集日期</span><strong>{{ firePoint.acq_date }}</strong></div>
          <div class="meta-item"><span>采集时间</span><strong>{{ firePoint.acq_time }}</strong></div>
          <div class="meta-item"><span>采集时间戳</span><strong>{{ formatDateTime(firePoint.acq_datetime) }}</strong></div>
          <div class="meta-item"><span>卫星</span><strong>{{ firePoint.satellite || '--' }}</strong></div>
          <div class="meta-item"><span>传感器</span><strong>{{ firePoint.instrument || '--' }}</strong></div>
          <div class="meta-item"><span>置信度</span><strong>{{ firePoint.confidence || '--' }}</strong></div>
          <div class="meta-item"><span>FRP</span><strong>{{ firePoint.frp ?? '--' }}</strong></div>
          <div class="meta-item"><span>昼夜</span><strong>{{ firePoint.daynight || '--' }}</strong></div>
          <div class="meta-item"><span>数据源</span><strong>{{ sourceProductLabel(firePoint.source_product) }}</strong></div>
          <div class="meta-item"><span>区域</span><strong>{{ areaLabel(firePoint.area_label) }}</strong></div>
          <div class="meta-item"><span>国家</span><strong>{{ firePoint.country_name || '--' }}</strong></div>
          <div class="meta-item wide"><span>来源文件</span><strong>{{ firePoint.source_file || '--' }}</strong></div>
        </div>
        <el-empty v-else description="未找到火点记录" />
      </GlassPanel>

      <GlassPanel title="地图定位" class="map-panel">
        <div class="map-frame">
          <CesiumMap
            ref="mapRef"
            :points="mapPoints"
            :hotspots="[]"
            :choropleth="[]"
            :show-countries="false"
            :show-hotspots="false"
            :cluster-fire-points="false"
            :initial-view="areaViewKey"
            @ready="handleMapReady"
          />
        </div>
      </GlassPanel>

      <div class="side-column">
        <WeatherCard title="天气" :weather="weather" :loading="weatherLoading" :empty-text="weatherError || '暂无天气数据'" />

        <GlassPanel title="上下文摘要">
          <div class="summary-grid">
            <div class="summary-item">
              <span>同国家近 7 天</span>
              <strong>{{ formatNumber(related.summary?.country_recent_total) }}</strong>
            </div>
            <div class="summary-item">
              <span>同国家最大 FRP</span>
              <strong>{{ formatMetric(related.summary?.country_recent_max_frp) }}</strong>
            </div>
            <div class="summary-item">
              <span>同国家平均 FRP</span>
              <strong>{{ formatMetric(related.summary?.country_recent_avg_frp) }}</strong>
            </div>
            <div class="summary-item">
              <span>同时间段火点</span>
              <strong>{{ formatNumber(related.summary?.same_period_count) }}</strong>
            </div>
            <div class="summary-item wide">
              <span>同时间段涉及国家</span>
              <strong>{{ formatNumber(related.summary?.same_period_country_count) }}</strong>
            </div>
          </div>
        </GlassPanel>
      </div>
    </section>

    <section class="related-grid">
      <GlassPanel title="附近相关火点" scrollable>
        <el-table :data="related.nearby_points || []" height="280">
          <el-table-column prop="acq_datetime" label="时间" min-width="160">
            <template #default="{ row }">{{ formatDateTime(row.acq_datetime) }}</template>
          </el-table-column>
          <el-table-column prop="country_name" label="国家" min-width="110" />
          <el-table-column prop="frp" label="FRP" width="90" />
          <el-table-column label="操作" width="90">
            <template #default="{ row }">
              <el-button link type="primary" @click="openFire(row.id)">查看</el-button>
            </template>
          </el-table-column>
        </el-table>
      </GlassPanel>

      <GlassPanel title="同国家近期火点" scrollable>
        <el-table :data="related.same_country_points || []" height="280">
          <el-table-column prop="acq_datetime" label="时间" min-width="160">
            <template #default="{ row }">{{ formatDateTime(row.acq_datetime) }}</template>
          </el-table-column>
          <el-table-column prop="source_product" label="数据源" min-width="140">
            <template #default="{ row }">{{ sourceProductLabel(row.source_product) }}</template>
          </el-table-column>
          <el-table-column prop="frp" label="FRP" width="90" />
          <el-table-column label="操作" width="90">
            <template #default="{ row }">
              <el-button link type="primary" @click="openFire(row.id)">查看</el-button>
            </template>
          </el-table-column>
        </el-table>
      </GlassPanel>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { fireApi, weatherApi } from '@/api/service'
import CesiumMap from '@/components/CesiumMap.vue'
import GlassPanel from '@/components/GlassPanel.vue'
import WeatherCard from '@/components/WeatherCard.vue'
import { AREA_PRESETS, SOURCE_PRODUCT_PRESETS, resolveAreaView } from '@/utils/fireDataConfig'
import { formatDateTime, formatNumber } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const mapRef = ref()
const firePoint = ref(null)
const related = ref({
  nearby_points: [],
  same_country_points: [],
  summary: {},
})
const weather = ref(null)
const weatherLoading = ref(false)
const weatherError = ref('')
const loading = ref(false)

const areaLabel = (value) => AREA_PRESETS[value]?.label || value || '--'
const sourceProductLabel = (value) => SOURCE_PRODUCT_PRESETS[value]?.label || value || '--'
const formatMetric = (value) => {
  const numeric = Number(value)
  return Number.isFinite(numeric) ? numeric.toFixed(2) : '--'
}

const areaViewKey = computed(() => resolveAreaView(firePoint.value?.area_label))
const mapPoints = computed(() => {
  const current = firePoint.value ? [firePoint.value] : []
  const nearby = (related.value.nearby_points || []).slice(0, 20)
  const unique = new Map()
  ;[...current, ...nearby].forEach((item) => {
    if (item?.id) unique.set(item.id, item)
  })
  return Array.from(unique.values())
})

const focusCurrentPoint = () => {
  if (!firePoint.value) return
  mapRef.value?.flyToCoordinates({
    longitude: firePoint.value.longitude,
    latitude: firePoint.value.latitude,
    height: firePoint.value.area_label === 'world' ? 2200000 : 1200000,
    duration: 1.8,
  })
}

const handleMapReady = () => {
  focusCurrentPoint()
}

const loadWeather = async () => {
  if (!firePoint.value) return
  weatherLoading.value = true
  weatherError.value = ''
  try {
    weather.value = await weatherApi.point(
      {
        latitude: firePoint.value.latitude,
        longitude: firePoint.value.longitude,
      },
      { silent: true },
    )
  } catch {
    weather.value = null
    weatherError.value = '天气服务暂不可用'
  } finally {
    weatherLoading.value = false
  }
}

const loadPage = async (fireId) => {
  loading.value = true
  try {
    const [detail, relatedPayload] = await Promise.all([fireApi.detail(fireId), fireApi.related(fireId)])
    firePoint.value = detail
    related.value = relatedPayload
    await loadWeather()
    focusCurrentPoint()
  } finally {
    loading.value = false
  }
}

const openFire = (id) => {
  if (!id) return
  router.push(`/fire-detail/${id}`)
}

onMounted(async () => {
  await loadPage(route.params.id)
})

watch(
  () => route.params.id,
  async (value, oldValue) => {
    if (!value || value === oldValue) return
    await loadPage(value)
  },
)
</script>

<style scoped>
.fire-detail-page {
  position: relative;
  padding-bottom: 8px;
}

.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.head-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.head-title h2 {
  margin: 0 0 6px;
}

.head-title span {
  color: var(--text-secondary);
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

.loading-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent-cyan), var(--accent-orange));
  box-shadow: 0 0 0 8px rgba(89, 214, 255, 0.08);
  animation: loadingPulse 1.2s ease-in-out infinite;
}

.detail-grid {
  display: grid;
  grid-template-columns: 360px minmax(0, 1fr) 320px;
  gap: 16px;
  min-height: 0;
}

.meta-grid,
.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.meta-item,
.summary-item {
  padding: 12px 14px;
  border-radius: 16px;
  border: 1px solid var(--line-soft);
  background: var(--bg-elevated);
}

.meta-item span,
.summary-item span {
  color: var(--text-secondary);
}

.meta-item strong,
.summary-item strong {
  display: block;
  margin-top: 8px;
}

.wide {
  grid-column: 1 / -1;
}

.map-panel,
.map-frame {
  height: 100%;
  min-height: 540px;
}

.map-frame {
  overflow: hidden;
  border-radius: 22px;
}

.side-column {
  display: grid;
  gap: 16px;
}

.related-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
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

@media (max-width: 1400px) {
  .detail-grid,
  .related-grid {
    grid-template-columns: 1fr;
  }
}
</style>
