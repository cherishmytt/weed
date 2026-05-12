<template>
  <div class="status-history-container">
  <div class="main-card glass-panel">
    <div class="card-header">
      <div class="header-title">
        <span>机器人状态历史记录</span>
        <span v-if="selectedRows.length > 0" class="selected-count">(已选择 {{ selectedRows.length }} 条)</span>
      </div>
      <div class="header-actions">
        <el-button type="primary" size="small" @click="viewBatchTrajectory" v-if="selectedRows.length > 0">
          <el-icon><Location /></el-icon>
          批量查看轨迹
        </el-button>
        <el-button type="success" size="small" @click="exportSelected">
          <el-icon><Download /></el-icon>
          导出选中
        </el-button>
        <el-button type="primary" size="small" @click="exportCurrentFiltered" :loading="exporting">
          <el-icon><Download /></el-icon>
          导出全部
        </el-button>
        <el-button type="danger" size="small" @click="confirmBatchDelete">
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
      </div>
    </div>

    <!-- 搜索筛选区域 -->
    <div class="filter-area">
      <!-- 快捷时间选项 -->
      <div class="quick-time">
        <span class="label">快捷筛选：</span>
        <el-button-group>
          <el-button size="small" :type="quickTime === 'today' ? 'primary' : ''" @click="setQuickTime('today')">今天</el-button>
          <el-button size="small" :type="quickTime === 'yesterday' ? 'primary' : ''" @click="setQuickTime('yesterday')">昨天</el-button>
          <el-button size="small" :type="quickTime === '7days' ? 'primary' : ''" @click="setQuickTime('7days')">近7天</el-button>
          <el-button size="small" :type="quickTime === '30days' ? 'primary' : ''" @click="setQuickTime('30days')">近30天</el-button>
        </el-button-group>
      </div>

      <el-row :gutter="16" class="filter-row">
        <el-col :span="8">
          <el-date-picker
            v-model="timeRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%;"
          />
        </el-col>
        <el-col :span="6">
          <el-select v-model="laserStatus" placeholder="激光状态" clearable style="width: 100%;">
            <el-option label="全部" value="" />
            <el-option label="开启" value="true" />
            <el-option label="关闭" value="false" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="exceptionFilters" placeholder="异常筛选" multiple style="width: 100%;">
            <el-option label="电量＜80%" value="lowBattery" />
            <el-option label="温度＞50℃" value="highTemp" />
            <el-option label="CPU＞70%" value="highCpu" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <div class="filter-buttons">
            <el-button type="primary" @click="handleQuery" :loading="loading">
              <el-icon><Search /></el-icon>
              查询
            </el-button>
            <el-button @click="handleReset">
              <el-icon><RefreshLeft /></el-icon>
              重置
            </el-button>
          </div>
        </el-col>
      </el-row>

      <el-row :gutter="16" class="filter-row">
        <el-col :span="12">
          <el-input v-model="keyword" placeholder="关键词搜索（经纬度）" clearable style="width: 100%;">
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
      </el-row>
    </div>

    <!-- 表格 -->
    <div class="table-container">
      <el-table
        ref="tableRef"
        :data="tableData"
        border
        stripe
        v-loading="loading"
        :show-empty="false"
        @sort-change="handleSortChange"
        @selection-change="handleSelectionChange"
        :default-sort="{ prop: 'reportedAt', order: 'descending' }"
        :sort-method="() => 0"
        fit
        style="width: 100%;"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="reportedAt" label="上报时间" width="180" sortable />
        <el-table-column prop="battery" label="电量 (%)" sortable>
          <template #default="{ row }">
            <span :class="getBatteryClass(row.battery)">
              {{ row.battery }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="temperature" label="温度 ℃" sortable>
          <template #default="{ row }">
            <span :class="getTemperatureClass(row.temperature)">
              {{ row.temperature }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="cpuUsage" label="CPU使用率 %" sortable>
          <template #default="{ row }">
            <span :class="getCpuClass(row.cpuUsage)">
              {{ row.cpuUsage }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="speed" label="速度 m/s" sortable>
          <template #default="{ row }">
            {{ row.speed?.toFixed(2) || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="laserOn" label="激光状态">
          <template #default="{ row }">
            <el-tag :type="row.laserOn ? 'success' : 'info'">
              {{ row.laserOn ? '开启' : '关闭' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="longitude" label="经度" />
        <el-table-column prop="latitude" label="纬度" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button type="primary" text size="small" @click="viewLocationOnMap(row)">
              <el-icon><Location /></el-icon>
              查看位置
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
    <div class="pagination-wrapper">
      <el-pagination
        :current-page="currentPage"
        :page-size="pageSize"
        :page-sizes="[20, 50, 100, 200]"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        layout="total, sizes, prev, pager, next, jumper"
      />
    </div>

    <!-- 位置查看弹窗 - 内嵌地图 -->
    <el-dialog
      v-model="locationDialogVisible"
      title="位置查看"
      width="800px"
      :close-on-click-modal="false"
      center
      teleport="body"
    >
      <div v-if="currentLocation" class="location-info">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="上报时间">{{ currentLocation.reportedAt }}</el-descriptions-item>
          <el-descriptions-item label="坐标">{{ currentLocation.latitude }}, {{ currentLocation.longitude }}</el-descriptions-item>
          <el-descriptions-item label="电量">
            <span :class="getBatteryClass(currentLocation.battery)">{{ currentLocation.battery }}%</span>
          </el-descriptions-item>
          <el-descriptions-item label="温度">
            <span :class="getTemperatureClass(currentLocation.temperature)">{{ currentLocation.temperature }}℃</span>
          </el-descriptions-item>
          <el-descriptions-item label="CPU使用率">
            <span :class="getCpuClass(currentLocation.cpuUsage)">{{ currentLocation.cpuUsage }}%</span>
          </el-descriptions-item>
          <el-descriptions-item label="激光状态">
            <el-tag :type="currentLocation.laserOn ? 'success' : 'info'">{{ currentLocation.laserOn ? '开启' : '关闭' }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <div id="status-location-map" class="location-map"></div>
    </el-dialog>

    <!-- 批量查看轨迹弹窗 -->
    <el-dialog
      v-model="batchTrajectoryVisible"
      title="批量查看轨迹"
      width="800px"
      :close-on-click-modal="false"
      center
    >
      <div id="batch-trajectory-map" class="location-map"></div>
    </el-dialog>
  </div>
</div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Download, Location, Delete, Search, RefreshLeft, List } from '@element-plus/icons-vue'
import { getStatusHistory, exportStatusHistory, deleteStatusBatch } from '@/api/robot'
import { ElMessage } from 'element-plus'

const router = useRouter()
const loading = ref(false)
const exporting = ref(false)
const tableData = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const isFirstLoad = ref(true)

const tableRef = ref(null)
const selectedRows = ref([])

const quickTime = ref('')
const timeRange = ref([])
const exceptionFilters = ref([])
const laserStatus = ref('')

const sortProp = ref('reportedAt')
const sortOrder = ref('descending')

const locationDialogVisible = ref(false)
const batchTrajectoryVisible = ref(false)
const currentLocation = ref(null)
let locationMap = null
let batchMap = null
let locationMarker = null
let trajectoryLayer = null

const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

function initDefaultTime() {
  const end = new Date()
  const start = new Date(end.getTime() - 24 * 60 * 60 * 1000)
  timeRange.value = [formatDate(start), formatDate(end)]
}

function formatDate(date) {
  const d = new Date(date)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  const seconds = String(d.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

function setQuickTime(type) {
  const now = new Date()
  let start, end

  switch (type) {
    case 'today':
      start = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0)
      end = now
      break
    case 'yesterday':
      start = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1, 0, 0, 0)
      end = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1, 23, 59, 59)
      break
    case '7days':
      start = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
      end = now
      break
    case '30days':
      start = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
      end = now
      break
    default:
      return
  }

  quickTime.value = type
  timeRange.value = [formatDate(start), formatDate(end)]
}

function disabledDate(time) {
  if (!timeRange.value || !timeRange.value[0]) return false
  return false
}

function getBatteryClass(battery) {
  if (battery < 50) return 'text-red'
  if (battery < 80) return 'text-orange'
  return ''
}

function getTemperatureClass(temp) {
  if (temp >= 50) return 'text-red'
  if (temp >= 45) return 'text-orange'
  return ''
}

function getCpuClass(cpu) {
  if (cpu >= 70) return 'text-red'
  if (cpu >= 50) return 'text-orange'
  return ''
}

function buildQueryParams() {
  const params = {
    page: currentPage.value,
    size: pageSize.value,
    keyword: keyword.value || null,
    laserOn: laserStatus.value !== '' ? (laserStatus.value === 'true') : null,
    sortBy: sortProp.value,
    sortOrder: sortOrder.value
  }

  if (timeRange.value && timeRange.value.length === 2) {
    params.startTime = timeRange.value[0]
    params.endTime = timeRange.value[1]
  }

  if (exceptionFilters.value.includes('lowBattery')) {
    params.maxBattery = 80
  }
  if (exceptionFilters.value.includes('highTemp')) {
    params.minTemperature = 50
  }
  if (exceptionFilters.value.includes('highCpu')) {
    params.minCpu = 70
  }

  return params
}

async function handleQuery() {
  loading.value = true
  try {
    const params = buildQueryParams()
    const res = await getStatusHistory(params)
    if (res.code === 200) {
      tableData.value = res.data.list
      total.value = res.data.total
      if (!isFirstLoad.value) {
        ElMessage.success(`查询完成，共找到 ${res.data.total} 条记录`)
      } else {
        isFirstLoad.value = false
      }
    }
  } catch (error) {
    if (!isFirstLoad.value) {
      ElMessage.error('查询失败，请稍后重试')
    } else {
      isFirstLoad.value = false
    }
  } finally {
    loading.value = false
  }
}

function handleReset() {
  quickTime.value = ''
  timeRange.value = []
  exceptionFilters.value = []
  laserStatus.value = ''
  keyword.value = ''
  currentPage.value = 1
  initDefaultTime()
  handleQuery()
}

function handleSizeChange(size) {
  pageSize.value = size
  currentPage.value = 1
  handleQuery()
}

function handleCurrentChange(page) {
  currentPage.value = page
  handleQuery()
}

function handleSortChange({ column, prop, order }) {
  sortProp.value = prop
  sortOrder.value = order || 'descending'
  currentPage.value = 1
  handleQuery()
}

async function exportCurrentFiltered() {
  exporting.value = true
  try {
    const params = buildQueryParams()
    params.page = 1
    params.size = 10000
    const res = await exportStatusHistory(params)
    if (res.code === 200) {
      generateCsv(res.data)
    }
  } finally {
    exporting.value = false
  }
}

function generateCsv(data, filename = 'robot-status') {
  const headers = [
    'ID,上报时间,电量,温度,CPU使用率,速度,激光状态,纬度,经度'
  ]
  const rows = data.map(item => [
    item.id,
    `"${item.reportedAt}"`,
    item.battery,
    item.temperature,
    item.cpuUsage,
    item.speed,
    item.laserOn ? '开启' : '关闭',
    item.latitude,
    item.longitude
  ])
  const csv = [headers, ...rows.map(r => r.join(','))].join('\n')
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  const timestamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')
  link.download = `${filename}-${timestamp}.csv`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

async function exportSelected() {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请先选择要导出的记录')
    return
  }

  exporting.value = true
  try {
    const ids = selectedRows.value.map(row => row.id)
    const res = await exportStatusHistory({ ids })
    if (res.code === 200) {
      generateCsv(res.data, 'robot-status-selected')
      ElMessage.success(`成功导出 ${selectedRows.value.length} 条记录`)
    }
  } finally {
    exporting.value = false
  }
}

function handleSelectionChange(rows) {
  selectedRows.value = rows
}

function clearSelection() {
  if (tableRef.value) {
    tableRef.value.clearSelection()
  }
}

function viewBatchTrajectory() {
  if (selectedRows.value.length === 0) {
    return
  }
  batchTrajectoryVisible.value = true
  setTimeout(() => {
    initBatchTrajectoryMap()
  }, 200)
}

async function confirmBatchDelete() {
  if (selectedRows.value.length === 0) {
    return
  }

  const confirmResult = window.confirm(`确定要删除选中的 ${selectedRows.value.length} 条记录吗？此操作不可恢复。`)
  if (!confirmResult) {
    return
  }

  loading.value = true
  try {
    const ids = selectedRows.value.map(row => row.id)
    const res = await deleteStatusBatch(ids)
    if (res.code === 200) {
      clearSelection()
      handleQuery()
    }
  } finally {
    loading.value = false
  }
}

function viewLocationOnMap(row) {
  currentLocation.value = row
  locationDialogVisible.value = true
  setTimeout(() => {
    initLocationMap()
  }, 200)
}

function initLocationMap() {
  if (!window.L) {
    setTimeout(initLocationMap, 200)
    return
  }

  if (locationMap) {
    locationMap.remove()
  }

  const lat = currentLocation.value.latitude
  const lng = currentLocation.value.longitude

  locationMap = L.map('status-location-map').setView([lat, lng], 18)

  L.tileLayer('https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}', {
    attribution: '&copy; <a href="https://www.amap.com/">高德地图</a>',
    subdomains: ['1', '2', '3', '4'],
    maxZoom: 18
  }).addTo(locationMap)

  const iconHtml = `
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24">
      <circle cx="12" cy="12" r="10" fill="#409eff" stroke="white" stroke-width="2"/>
      <text x="12" y="17" text-anchor="middle" fill="white" font-weight="bold" font-size="12">P</text>
    </svg>
  `
  const icon = L.divIcon({
    html: iconHtml,
    className: 'custom-marker',
    iconSize: [24, 24],
    iconAnchor: [12, 12]
  })

  locationMarker = L.marker([lat, lng], { icon }).addTo(locationMap)

  const popupContent = `
    <div>
      <div><strong>时间:</strong> ${currentLocation.value.reportedAt}</div>
      <div><strong>电量:</strong> ${currentLocation.value.battery}%</div>
      <div><strong>温度:</strong> ${currentLocation.value.temperature}℃</div>
    </div>
  `
  locationMarker.bindPopup(popupContent)

  setTimeout(() => {
    locationMap.invalidateSize()
  }, 100)
}

function initBatchTrajectoryMap() {
  if (!window.L) {
    setTimeout(initBatchTrajectoryMap, 200)
    return
  }

  if (batchMap) {
    batchMap.remove()
  }

  const points = selectedRows.value.map(row => [row.latitude, row.longitude]).filter(p => p[0] && p[1])

  if (points.length === 0) {
    return
  }

  batchMap = L.map('batch-trajectory-map').setView(points[0], 17)

  L.tileLayer('https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}', {
    attribution: '&copy; <a href="https://www.amap.com/">高德地图</a>',
    subdomains: ['1', '2', '3', '4'],
    maxZoom: 18
  }).addTo(batchMap)

  if (points.length > 1) {
    trajectoryLayer = L.polyline(points, {
      color: '#409eff',
      weight: 3,
      opacity: 0.8,
      smoothFactor: 1
    }).addTo(batchMap)

    const bounds = trajectoryLayer.getBounds()
    batchMap.fitBounds(bounds, { padding: [50, 50] })
  } else {
    batchMap.setView(points[0], 18)
  }

  const startIcon = L.divIcon({
    html: `
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24">
        <circle cx="12" cy="12" r="10" fill="#39d398" stroke="white" stroke-width="2"/>
        <text x="12" y="17" text-anchor="middle" fill="white" font-weight="bold" font-size="10">S</text>
      </svg>
    `,
    className: 'custom-marker',
    iconSize: [24, 24],
    iconAnchor: [12, 12]
  })

  const endIcon = L.divIcon({
    html: `
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24">
        <circle cx="12" cy="12" r="10" fill="#ff5d5d" stroke="white" stroke-width="2"/>
        <text x="12" y="17" text-anchor="middle" fill="white" font-weight="bold" font-size="10">E</text>
      </svg>
    `,
    className: 'custom-marker',
    iconSize: [24, 24],
    iconAnchor: [12, 12]
  })

  L.marker(points[0], { icon: startIcon }).addTo(batchMap)
    .bindPopup(`<div><strong>起点:</strong> ${selectedRows.value[0].reportedAt}</div>`)

  if (points.length > 1) {
    L.marker(points[points.length - 1], { icon: endIcon }).addTo(batchMap)
      .bindPopup(`<div><strong>终点:</strong> ${selectedRows.value[selectedRows.value.length - 1].reportedAt}</div>`)
  }

  setTimeout(() => {
    batchMap.invalidateSize()
  }, 100)
}

onMounted(() => {
  initDefaultTime()
  handleQuery()

  if (!document.querySelector('link[href*="leaflet.css"]')) {
    const link = document.createElement('link')
    link.rel = 'stylesheet'
    link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'
    document.head.appendChild(link)
  }
  if (!document.querySelector('script[src*="leaflet.js"]')) {
    const script = document.createElement('script')
    script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
    document.head.appendChild(script)
  }
})
</script>

<style scoped>
.status-history-container {
  min-height: 100%;
}

.main-card {
  padding: 28px;
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--line-soft);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 22px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.5px;
}

.selected-count {
  font-weight: normal;
  font-size: 14px;
  color: var(--text-secondary);
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.filter-area {
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.quick-time {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.quick-time .label {
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
}

.quick-time :deep(.el-button) {
  background: rgba(255, 255, 255, 0.05) !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
  color: var(--text-primary) !important;
}

.quick-time :deep(.el-button:hover) {
  background: rgba(255, 255, 255, 0.1) !important;
  border-color: var(--primary-color) !important;
  color: var(--text-primary) !important;
}

.quick-time :deep(.el-button--primary) {
  background: rgba(64, 158, 255, 0.3) !important;
  border-color: rgba(64, 158, 255, 0.5) !important;
  color: white !important;
  backdrop-filter: blur(10px) !important;
}

.quick-time :deep(.el-button--primary:hover) {
  background: rgba(64, 158, 255, 0.4) !important;
  border-color: rgba(64, 158, 255, 0.6) !important;
  color: white !important;
}

.filter-row {
  margin-bottom: 16px;
}

.filter-row:last-child {
  margin-bottom: 0;
}

.filter-buttons {
  display: flex;
  gap: 10px;
  justify-content: flex-start;
  height: 32px;
  align-items: flex-end;
}

.table-container {
  min-height: 450px;
  margin-bottom: 0;
  position: relative;
  padding: 20px;
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  border: 1px solid var(--line-soft);
}

.pagination-wrapper {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
  padding-top: 16px;
  border-top: 1px solid var(--line-soft);
}

.location-info {
  margin-bottom: 16px;
}

.location-map {
  height: 350px;
  width: 100%;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--bg-input);
}

.text-orange {
  color: var(--accent-orange);
  font-weight: 600;
}

.text-red {
  color: var(--accent-red);
  font-weight: 600;
}

@media (max-width: 1400px) {
  .filter-row {
    gap: 20px;
  }
}

@media (max-width: 900px) {
  .filter-row {
    gap: 12px;
  }

  .filter-group label {
    min-width: 50px;
  }

  .card-header h2 {
    font-size: 18px;
  }
}

@media (max-width: 640px) {
  .filter-row {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-group {
    justify-content: flex-start;
  }

  .filter-row:last-child {
    flex-direction: row;
    justify-content: center;
  }

  .status-history-container {
    padding: 12px;
  }

  .main-card {
    padding: 16px;
  }
}

</style>


<style>
#status-location-map .leaflet-container,
#batch-trajectory-map .leaflet-container {
  z-index: 1;
}

.custom-marker {
  background: none;
  border: none;
}
</style>