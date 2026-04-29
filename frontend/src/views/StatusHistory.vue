<template>
  <div class="status-history-container">
  <div class="main-card glass-panel">
    <div class="card-header">
      <h2>机器人状态历史记录</h2>
      <div class="header-actions">
        <el-button type="primary" @click="exportCurrentFiltered" :loading="exporting">
          <el-icon><Download /></el-icon>
          导出CSV
        </el-button>
      </div>
    </div>

    <!-- 筛选区域 -->
    <div class="filter-bar">
      <!-- 快捷时间选择 -->
      <div class="filter-row">
        <div class="filter-group">
          <label>快捷筛选</label>
          <el-radio-group v-model="quickTime" size="small" @change="handleQuickTimeChange">
            <el-radio-button label="today">今天</el-radio-button>
            <el-radio-button label="yesterday">昨天</el-radio-button>
            <el-radio-button label="7days">近7天</el-radio-button>
            <el-radio-button label="30days">近30天</el-radio-button>
          </el-radio-group>
        </div>
      </div>

      <!-- 时间范围 + 其他筛选 -->
      <div class="filter-row">
        <div class="filter-group">
          <label>时间范围</label>
          <el-date-picker
            v-model="timeRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
            :disabled-date="disabledDate"
            style="width: 360px;"
          />
        </div>

        <div class="filter-group">
          <label>异常筛选</label>
          <el-checkbox-group v-model="exceptionFilters" size="small">
            <el-checkbox-button label="lowBattery">电量＜80%</el-checkbox-button>
            <el-checkbox-button label="highTemp">温度＞50℃</el-checkbox-button>
            <el-checkbox-button label="highCpu">CPU＞70%</el-checkbox-button>
          </el-checkbox-group>
        </div>

        <div class="filter-group">
          <label>激光状态</label>
          <el-select v-model="laserStatus" clearable placeholder="全部" style="width: 120px;">
            <el-option label="全部" value="" />
            <el-option label="开启" value="true" />
            <el-option label="关闭" value="false" />
          </el-select>
        </div>
      </div>

      <div class="filter-row">
        <div class="filter-group">
          <label>关键词搜索</label>
          <el-input v-model="keyword" placeholder="搜索经纬度" clearable style="width: 200px;" />
        </div>
        <div class="filter-group filter-actions">
          <el-button type="primary" @click="handleQuery" :loading="loading">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </div>
      </div>
    </div>

    <!-- 数据概览统计卡片 -->
    <div class="overview-container" v-if="tableData.length > 0">
      <div class="overview-card">
        <div class="overview-item glass-panel">
          <div class="value">{{ stats.totalRecords }}</div>
          <div class="label">总记录数</div>
        </div>
        <div class="overview-item glass-panel">
          <div class="value">{{ stats.maxTemp }}<span class="unit">℃</span></div>
          <div class="label">最高温度</div>
        </div>
        <div class="overview-item glass-panel">
          <div class="value">{{ stats.avgTemp }}<span class="unit">℃</span></div>
          <div class="label">平均温度</div>
        </div>
        <div class="overview-item glass-panel">
          <div class="value">{{ stats.avgCpu }}<span class="unit">%</span></div>
          <div class="label">平均CPU</div>
        </div>
        <div class="overview-item glass-panel">
          <div class="value">{{ stats.maxCpu }}<span class="unit">%</span></div>
          <div class="label">最高CPU</div>
        </div>
        <div class="overview-item glass-panel">
          <div class="value text-red" v-if="stats.minBattery">{{ stats.minBattery }}<span class="unit">%</span></div>
          <div class="value" v-else>--</div>
          <div class="label">最低电量</div>
        </div>
        <div class="overview-item glass-panel">
          <div class="value">{{ stats.avgSpeed }}<span class="unit">m/s</span></div>
          <div class="label">平均速度</div>
        </div>
        <div class="overview-item glass-panel">
          <div class="value">{{ stats.laserOnCount }}</div>
          <div class="label">激光开启次数</div>
        </div>
      </div>
    </div>

    <!-- 表格 -->
    <div class="table-container">
      <el-table
        :data="tableData"
        border
        stripe
        v-loading="loading"
        height="500"
        @sort-change="handleSortChange"
        :default-sort="{ prop: 'reportedAt', order: 'descending' }"
        :sort-method="() => 0"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column prop="reportedAt" label="上报时间" width="180" sortable />
        <el-table-column prop="battery" label="电量 (%)" width="100" sortable>
          <template #default="{ row }">
            <span :class="getBatteryClass(row.battery)">
              {{ row.battery }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="temperature" label="温度 ℃" width="100" sortable>
          <template #default="{ row }">
            <span :class="getTemperatureClass(row.temperature)">
              {{ row.temperature }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="cpuUsage" label="CPU使用率 %" width="120" sortable>
          <template #default="{ row }">
            <span :class="getCpuClass(row.cpuUsage)">
              {{ row.cpuUsage }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="speed" label="速度 m/s" width="100" sortable>
          <template #default="{ row }">
            {{ row.speed?.toFixed(2) || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="laserOn" label="激光状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.laserOn ? 'success' : 'info'">
              {{ row.laserOn ? '开启' : '关闭' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="longitude" label="经度" width="120" />
        <el-table-column prop="latitude" label="纬度" width="120" />
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" text size="small" @click="viewLocationOnMap(row)">
              <el-icon><Location /></el-icon>
              查看位置
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 空状态 -->
      <el-empty v-if="!loading && tableData.length === 0" description="暂无符合条件的状态记录" />
    </div>

    <!-- 分页 -->
    <div class="pagination-wrapper">
      <div class="pagination-info" v-if="total > 0">
        共 {{ total }} 条记录，当前第 {{ currentPage }} 页 / 共 {{ totalPages }} 页
      </div>
      <el-pagination
        :current-page="currentPage"
        :page-size="pageSize"
        :page-sizes="[20, 50, 100, 200]"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        layout="total, sizes, prev, pager, next, jumper"
        background
      />
    </div>

    <!-- 位置查看弹窗 - 内嵌地图 -->
    <el-dialog
      v-model="locationDialogVisible"
      title="位置查看"
      width="800px"
      :close-on-click-modal="false"
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
    >
      <div id="batch-trajectory-map" class="location-map"></div>
    </el-dialog>
  </div>
</div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Download, Location } from '@element-plus/icons-vue'
import { getStatusHistory, exportStatusHistory } from '@/api/robot'

const router = useRouter()
const loading = ref(false)
const exporting = ref(false)
const tableData = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const keyword = ref('')

// 筛选条件
const quickTime = ref('')
const timeRange = ref([])
const exceptionFilters = ref([])
const laserStatus = ref('')

// 排序参数
const sortProp = ref('reportedAt')
const sortOrder = ref('descending')

// 统计数据
const stats = ref({
  totalRecords: 0,
  maxTemp: 0,
  avgTemp: 0,
  minBattery: 100,
  avgCpu: 0,
  maxCpu: 0,
  avgSpeed: 0,
  laserOnCount: 0
})

// 弹窗相关
const locationDialogVisible = ref(false)
const batchTrajectoryVisible = ref(false)
const currentLocation = ref(null)
let locationMap = null
let batchMap = null
let locationMarker = null
let trajectoryLayer = null

const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

// 初始化默认时间 - 最近24小时
function initDefaultTime() {
  const end = new Date()
  const start = new Date(end.getTime() - 24 * 60 * 60 * 1000)
  timeRange.value = [formatDate(start), formatDate(end)]
}

// 格式化时间
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

// 快捷时间选择
function handleQuickTimeChange() {
  const now = new Date()
  let start, end

  switch (quickTime.value) {
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

  timeRange.value = [formatDate(start), formatDate(end)]
}

// 禁用日期验证
function disabledDate(time) {
  if (!timeRange.value || !timeRange.value[0]) return false
  return false
}

// 获取电量样式类
function getBatteryClass(battery) {
  if (battery < 50) return 'text-red'
  if (battery < 80) return 'text-orange'
  return ''
}

// 获取温度样式类
function getTemperatureClass(temp) {
  if (temp >= 50) return 'text-red'
  if (temp >= 45) return 'text-orange'
  return ''
}

// 获取CPU样式类
function getCpuClass(cpu) {
  if (cpu >= 70) return 'text-red'
  if (cpu >= 50) return 'text-orange'
  return ''
}

// 计算统计数据
function calculateStats(data) {
  if (!data || data.length === 0) {
    stats.value = {
      totalRecords: 0,
      maxTemp: 0,
      avgTemp: 0,
      minBattery: 100,
      avgCpu: 0,
      maxCpu: 0,
      avgSpeed: 0,
      laserOnCount: 0
    }
    return
  }

  let sumTemp = 0
  let maxTemp = -Infinity
  let sumCpu = 0
  let maxCpu = -Infinity
  let minBattery = Infinity
  let sumSpeed = 0
  let laserOnCount = 0
  let validSpeedCount = 0

  data.forEach(item => {
    // 温度
    if (item.temperature != null) {
      sumTemp += item.temperature
      if (item.temperature > maxTemp) maxTemp = item.temperature
    }
    // CPU
    if (item.cpuUsage != null) {
      sumCpu += item.cpuUsage
      if (item.cpuUsage > maxCpu) maxCpu = item.cpuUsage
    }
    // 电量
    if (item.battery != null && item.battery < minBattery) {
      minBattery = item.battery
    }
    // 速度
    if (item.speed != null && !isNaN(item.speed)) {
      sumSpeed += item.speed
      validSpeedCount++
    }
    // 激光开启计数
    if (item.laserOn) {
      laserOnCount++
    }
  })

  stats.value = {
    totalRecords: data.length,
    maxTemp: maxTemp !== -Infinity ? Number(maxTemp.toFixed(1)) : 0,
    avgTemp: data.length > 0 ? Number((sumTemp / data.length).toFixed(1)) : 0,
    minBattery: minBattery !== Infinity ? Number(minBattery.toFixed(1)) : null,
    avgCpu: data.length > 0 ? Number((sumCpu / data.length).toFixed(1)) : 0,
    maxCpu: maxCpu !== -Infinity ? Number(maxCpu.toFixed(1)) : 0,
    avgSpeed: validSpeedCount > 0 ? Number((sumSpeed / validSpeedCount).toFixed(2)) : 0,
    laserOnCount
  }
}

// 构建筛选参数
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

  // 异常筛选
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

// 查询数据
async function handleQuery() {
  loading.value = true
  try {
    const params = buildQueryParams()
    const res = await getStatusHistory(params)
    if (res.code === 200) {
      tableData.value = res.data.list
      total.value = res.data.total
      // 使用后端基于所有数据计算的统计信息
      if (res.data.stats) {
        stats.value = res.data.stats
      } else {
        calculateStats(res.data.list)
      }
    }
  } finally {
    loading.value = false
  }
}

// 重置筛选
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

// 排序变化 - 后端排序，对所有数据排序
function handleSortChange({ column, prop, order }) {
  sortProp.value = prop
  sortOrder.value = order || 'descending' // null 表示取消排序，默认降序
  currentPage.value = 1 // 排序变化后回到第一页
  handleQuery()
}

// 导出当前筛选结果
async function exportCurrentFiltered() {
  exporting.value = true
  try {
    const params = buildQueryParams()
    // 获取所有符合条件的数据用于导出
    params.page = 1
    params.size = 10000 // 最多导出一万条
    const res = await exportStatusHistory(params)
    if (res.code === 200) {
      generateCsv(res.data)
    }
  } finally {
    exporting.value = false
  }
}

// 生成并下载CSV
function generateCsv(data) {
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
  link.download = `robot-status-${timestamp}.csv`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

// 在地图上查看位置
function viewLocationOnMap(row) {
  currentLocation.value = row
  locationDialogVisible.value = true
  // 延迟初始化地图，确保DOM已渲染
  setTimeout(() => {
    initLocationMap()
  }, 200)
}

// 初始化位置查看地图
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

  // 添加高德瓦片
  L.tileLayer('https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}', {
    attribution: '&copy; <a href="https://www.amap.com/">高德地图</a>',
    subdomains: ['1', '2', '3', '4'],
    maxZoom: 18
  }).addTo(locationMap)

  // 添加标记
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

  // 让地图自适应大小
  setTimeout(() => {
    locationMap.invalidateSize()
  }, 100)
}

onMounted(() => {
  initDefaultTime()
  handleQuery()

  // 加载 Leaflet CSS 和 JS
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
  padding: 20px;
  min-height: 100vh;
  background: var(--app-background);
}

.main-card {
  padding: 24px;
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.card-header h2 {
  margin-top: 0;
  margin-bottom: 0;
  font-size: 20px;
  color: var(--text-primary);
  letter-spacing: -0.3px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.filter-bar {
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--line-soft);
}

.filter-row {
  display: flex;
  gap: 24px;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.filter-row:last-child {
  margin-bottom: 0;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-group label {
  white-space: nowrap;
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 500;
}

.filter-actions {
  margin-left: auto;
}

/* 统计概览 */
.overview-container {
  margin-bottom: 24px;
}

.overview-card {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 16px;
}

.overview-item {
  padding: 20px 12px;
  border-radius: var(--radius-md);
  text-align: center;
  transition: all 0.2s ease;
}

.overview-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-panel);
}

.overview-item .value {
  font-size: 26px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.2;
  letter-spacing: -0.5px;
}

.overview-item .value .unit {
  font-size: 14px;
  font-weight: normal;
  color: var(--text-secondary);
}

.overview-item .label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 8px;
}

.table-container {
  min-height: 500px;
  margin-bottom: 20px;
  position: relative;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 20px;
  border-top: 1px solid var(--line-soft);
}

.pagination-info {
  color: var(--text-secondary);
  font-size: 14px;
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

/* 异常文字颜色 */
.text-orange {
  color: var(--accent-orange);
  font-weight: 600;
}

.text-red {
  color: var(--accent-red);
  font-weight: 600;
}

/* 重置按钮样式 */
.filter-actions :deep(.el-button:not(.el-button--primary)) {
  background: rgba(255, 255, 255, 0.05) !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
  color: var(--text-primary) !important;
}

.filter-actions :deep(.el-button:not(.el-button--primary):hover) {
  background: rgba(255, 255, 255, 0.1) !important;
  border-color: var(--primary-color) !important;
  color: var(--text-primary) !important;
}

@media (max-width: 1600px) {
  .overview-card {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 900px) {
  .overview-card {
    grid-template-columns: repeat(2, 1fr);
  }
  .filter-row {
    gap: 12px;
  }
}

/* 分页组件样式 */
.pagination-wrapper :deep(.el-pagination) {
  .el-pagination__prev, .el-pagination__next, .el-pagination__sizes, .el-pagination__jump {
    .el-button {
      background: white !important;
      border-color: #dcdfe6 !important;
      color: #606266 !important;
    }
  }
  .el-pagination__sizes {
    .el-select .el-input {
      .el-input__inner {
        background: white !important;
        border-color: #dcdfe6 !important;
        color: #606266 !important;
      }
    }
  }
  .el-pagination__jump {
    input {
      background: white !important;
      border-color: #dcdfe6 !important;
      color: #606266 !important;
    }
  }
}
</style>


<style>
/* Leaflet 样式 */
#status-location-map .leaflet-container,
#batch-trajectory-map .leaflet-container {
  z-index: 1;
}

.custom-marker {
  background: none;
  border: none;
}
</style>
