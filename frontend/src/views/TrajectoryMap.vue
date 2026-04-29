<template>
  <div class="trajectory-page">
    <div class="main-card glass-panel">
      <div class="card-header">
        <span>机器人轨迹地图</span>
        <div class="header-actions">
          <el-button v-if="!isFullscreen" :icon="FullScreen" @click="toggleFullscreen" size="small" text>全屏</el-button>
          <el-button v-else :icon="Fold" @click="toggleFullscreen" size="small" text>退出全屏</el-button>
          <el-button :icon="Refresh" @click="loadTrajectory" :loading="loading" size="small" text>刷新</el-button>
        </div>
      </div>

      <div class="filter-bar">
        <div class="quick-select">
          <span class="quick-label">快捷选择：</span>
          <el-button-group>
            <el-button size="small" v-for="option in quickOptions" :key="option.value"
              :type="isQuickSelected(option) ? 'primary' : 'default'"
              @click="selectQuickTime(option)">
              {{ option.label }}
            </el-button>
          </el-button-group>
        </div>
        <el-form :inline="true" :model="queryForm" class="filter-form">
          <el-form-item label="开始时间">
            <el-date-picker
              v-model="queryForm.startTime"
              type="datetime"
              placeholder="选择开始时间"
              format="YYYY-MM-DD HH:mm:ss"
              value-format="YYYY-MM-DD HH:mm:ss"
              :disabled-date="disabledStartDate"
              :disabled-time="disabledStartTime"
              @change="onStartTimeChange"
              align="right"
            />
          </el-form-item>
          <el-form-item label="结束时间">
            <el-date-picker
              v-model="queryForm.endTime"
              type="datetime"
              placeholder="选择结束时间"
              format="YYYY-MM-DD HH:mm:ss"
              value-format="YYYY-MM-DD HH:mm:ss"
              :disabled-date="disabledEndDate"
              :disabled-time="disabledEndTime"
              @change="onEndTimeChange"
              align="right"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="loadTrajectory" :loading="loading" :disabled="!validateTimeRange()">
              查询轨迹
            </el-button>
          </el-form-item>
          <el-form-item>
            <el-button @click="resetQuery">重置</el-button>
          </el-form-item>
        </el-form>
        <div v-if="timeErrorMsg" class="time-error">
          <el-icon><Warning /></el-icon>
          {{ timeErrorMsg }}
        </div>
      </div>


      <div class="map-wrapper" :class="{ fullscreen: isFullscreen }">
        <div class="map-container" id="trajectory-map">
          <div v-if="loading" class="map-loading">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>加载中...</span>
          </div>
          <div v-if="!loading && filteredPoints.length === 0" class="map-empty">
            <div class="empty-content">
              <el-icon><Location /></el-icon>
              <p>{{ emptyMessage }}</p>
            </div>
          </div>

          <!-- 回放控件 -->
          <div v-if="filteredPoints.length > 0" class="playback-controls">
            <div class="playback-left">
              <el-button :type="isPlaying ? 'warning' : 'primary'" size="small" @click="togglePlayPause">
                <el-icon v-if="!isPlaying"><VideoPlay /></el-icon>
                <el-icon v-else><VideoPause /></el-icon>
                {{ isPlaying ? '暂停' : '回放' }}
              </el-button>
              <el-select v-model="playbackSpeed" size="small" style="width: 70px; margin-left: 8px" @change="updatePlaybackSpeed">
                <el-option label="0.5x" value="0.5"></el-option>
                <el-option label="1x" value="1"></el-option>
                <el-option label="2x" value="2"></el-option>
                <el-option label="4x" value="4"></el-option>
              </el-select>
            </div>
            <div class="playback-progress">
              <el-slider v-model="playbackProgress" :min="0" :max="100" @input="seekToProgress"></el-slider>
            </div>
            <span class="playback-time">{{ currentPlaybackTime }} / {{ totalDuration }}</span>
          </div>

          <!-- 图层切换 -->
          <div class="map-layer-switch">
            <el-radio-group v-model="currentLayer" size="small" @change="changeMapLayer">
              <el-radio-button value="normal">标准</el-radio-button>
              <el-radio-button value="satellite">卫星</el-radio-button>
            </el-radio-group>
          </div>

          <!-- 显示/隐藏轨迹点开关 -->
          <div class="point-toggle">
            <span>显示轨迹点</span>
            <el-switch v-model="showPoints" @change="togglePointsVisibility" />
          </div>
        </div>
      </div>

      <!-- 导出按钮 -->
      <div class="actions-bar" v-if="filteredPoints.length > 0">
        <el-button size="small" @click="exportTrajectoryJSON">导出 JSON</el-button>
        <el-button size="small" @click="exportTrajectoryCSV">导出 CSV</el-button>
        <el-button size="small" @click="exportMapImage">导出地图图片</el-button>
      </div>

      <!-- 提示信息 -->
      <div v-if="hasFilteredPoints" class="filter-info">
        <el-icon><InfoFilled /></el-icon>
        部分轨迹点因信号异常已过滤
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import {
  Loading,
  Warning,
  Refresh,
  FullScreen,
  Fold,
  Location,
  InfoFilled,
  VideoPlay,
  VideoPause
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getTrajectory } from '@/api/robot'
import html2canvas from 'html2canvas'

// 快捷时间选项
const quickOptions = [
  { label: '今天', value: 'today' },
  { label: '近1小时', value: '1h' },
  { label: '近2小时', value: '2h' },
  { label: '近12小时', value: '12h' }
]

const queryForm = ref({
  startTime: null,
  endTime: null
})

const loading = ref(false)
const points = ref([])
const filteredPoints = ref([])
const totalDistance = ref(0)
const avgSpeed = ref(0)
const maxSpeed = ref(0)
const workingDuration = ref('')
const movingDuration = ref('')
const timeErrorMsg = ref('')
const isFullscreen = ref(false)
const showPoints = ref(true)
const currentLayer = ref('normal')

// 回放相关
const isPlaying = ref(false)
const playbackSpeed = ref(1)
const playbackProgress = ref(0)
let playbackTimer = null
let playbackMarker = null
let polylineLayers = []
let pointMarkers = []
// 增量绘制：回放时逐步显示轨迹点和线段
let playbackPolylineLayers = []
let playbackPointMarkers = []
let lastPlaybackIndex = 0

let map = null
let startMarker = null
let endMarker = null
let tileLayer = null

const hasFilteredPoints = computed(() => points.value.length > filteredPoints.value.length)
const emptyMessage = computed(() => {
  if (points.value.length === 0) return '暂无轨迹数据，请选择时间范围后查询'
  if (filteredPoints.value.length === 0) return '所选时间段内无有效轨迹数据，请调整时间范围'
  return '暂无轨迹数据'
})

// 初始化默认时间 - 今天 0点到当前时间
function initDefaultTime() {
  const now = new Date()
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  queryForm.value.startTime = formatDateTime(todayStart)
  queryForm.value.endTime = formatDateTime(now)
}

// 格式化时间为 YYYY-MM-DD HH:mm:ss
function formatDateTime(date) {
  const pad = n => n.toString().padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

// 快捷选择时间
function selectQuickTime(option) {
  const now = new Date()
  let start = new Date()
  switch (option.value) {
    case 'today':
      start = new Date(now.getFullYear(), now.getMonth(), now.getDate())
      break
    case '1h':
      start = new Date(now.getTime() - 60 * 60 * 1000)
      break
    case '2h':
      start = new Date(now.getTime() - 2 * 60 * 60 * 1000)
      break
    case '12h':
      start = new Date(now.getTime() - 12 * 60 * 60 * 1000)
      break
  }
  queryForm.value.startTime = formatDateTime(start)
  queryForm.value.endTime = formatDateTime(now)
  validateTimeRange()
}

// 判断是否选中快捷选项
function isQuickSelected(option) {
  if (!queryForm.value.startTime || !queryForm.value.endTime) return false
  const now = new Date()
  const start = new Date(queryForm.value.startTime)
  const end = new Date(queryForm.value.endTime)
  const endDiff = Math.abs(now.getTime() - end.getTime())
  if (option.value === 'today') {
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    return Math.abs(start.getTime() - todayStart.getTime()) < 1000 && endDiff < 60000
  }
  const expectedStart = new Date(now.getTime() - (parseInt(option.value) * 60 * 60 * 1000))
  return Math.abs(start.getTime() - expectedStart.getTime()) < 60000 && endDiff < 60000
}

// 禁用开始日期
function disabledStartDate(date) {
  if (!queryForm.value.endTime) return false
  const endDate = new Date(queryForm.value.endTime)
  return date.getTime() > endDate.getTime()
}

// 禁用结束日期
function disabledEndDate(date) {
  if (!queryForm.value.startTime) return false
  const startDate = new Date(queryForm.value.startTime)
  return date.getTime() < startDate.getTime()
}

// 禁用开始时间
function disabledStartTime(date) {
  if (!queryForm.value.endTime) return false
  if (!date || !queryForm.value.endTime) return false
  const endDate = new Date(queryForm.value.endTime)
  return date.getTime() > endDate.getTime()
}

// 禁用结束时间
function disabledEndTime(date) {
  if (!queryForm.value.startTime) return false
  const startDate = new Date(queryForm.value.startTime)
  return date.getTime() < startDate.getTime()
}

function onStartTimeChange() {
  validateTimeRange()
}

function onEndTimeChange() {
  validateTimeRange()
}

// 验证时间范围
function validateTimeRange() {
  timeErrorMsg.value = ''
  if (!queryForm.value.startTime || !queryForm.value.endTime) {
    timeErrorMsg.value = '请选择开始时间和结束时间'
    return false
  }
  const start = new Date(queryForm.value.startTime)
  const end = new Date(queryForm.value.endTime)
  if (end.getTime() <= start.getTime()) {
    timeErrorMsg.value = '结束时间不能早于或等于开始时间'
    return false
  }
  // 如果超过1天给出提示
  if (end.getTime() - start.getTime() > 24 * 60 * 60 * 1000) {
    timeErrorMsg.value = '提示：当前时间范围超过1天，查询数据量可能较大'
  }
  return true
}

// 全屏切换
function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value
  setTimeout(() => {
    if (map) {
      map.invalidateSize()
      if (filteredPoints.value.length > 0) {
        fitMapToTrajectory()
      }
    }
  }, 300)
}

// 按下ESC键退出全屏
function handleKeyDown(event) {
  if (event.key === 'Escape' && isFullscreen.value) {
    toggleFullscreen()
  }
}

async function loadTrajectory() {
  if (!validateTimeRange()) {
    return
  }
  loading.value = true
  try {
    const res = await getTrajectory(queryForm.value.startTime, queryForm.value.endTime)
    if (res.code === 200) {
      points.value = res.data.points || []
      filterOutliers()
      updateMap()
      calculateStats()
      stopPlayback()
    }
  } finally {
    loading.value = false
  }
}

function resetQuery() {
  initDefaultTime()
  points.value = []
  filteredPoints.value = []
  clearMap()
  totalDistance.value = 0
  avgSpeed.value = 0
  maxSpeed.value = 0
  workingDuration.value = ''
  movingDuration.value = ''
  timeErrorMsg.value = ''
  stopPlayback()
}

// 过滤异常漂移点
function filterOutliers() {
  if (points.value.length < 2) {
    filteredPoints.value = [...points.value]
    return
  }
  // 简单过滤：如果速度超过合理值（比如 30 km/h）认为是异常点
  // 机器人一般走很慢，30 km/h 已经留了很大余量
  const result = []
  let lastValid = null

  for (let i = 0; i < points.value.length; i++) {
    const p = points.value[i]
    // 确保点存在且坐标有效
    if (!p || typeof p.lat === 'undefined' || typeof p.lng === 'undefined') {
      continue
    }
    // 确保坐标是有效数字
    let lat = Number(p.lat)
    let lng = Number(p.lng)
    if (isNaN(lat) || isNaN(lng) || !isFinite(lat) || !isFinite(lng)) {
      continue
    }

    // 自动纠正经纬度顺序：
    // 纬度 (lat) 范围：中国大约 18° ~ 54°
    // 经度 (lng) 范围：中国大约 73° ~ 135°
    // 如果明显不对，直接交换
    if (lat > lng && lat >= 70 && lat <= 140 && lng >= 10 && lng <= 60) {
      // lat 更大（在经度范围），lng 更小（在纬度范围）→ 说明字段反了，交换
      [lat, lng] = [lng, lat]
      console.warn(`Auto-corrected lat/lng order for point ${i}: (${p.lat}, ${p.lng}) → (${lat}, ${lng})`)
    }
    // 如果超出范围，再尝试一次交换
    else if (lat < 10 || lat > 60 || lng < 70 || lng > 140) {
      const newLat = Number(p.lng)
      const newLng = Number(p.lat)
      if (newLat >= 10 && newLat <= 60 && newLng >= 70 && newLng <= 140) {
        lat = newLat
        lng = newLng
        console.warn(`Swapped lat/lng for point ${i}: (${Number(p.lat)}, ${Number(p.lng)}) → (${lat}, ${lng})`)
      } else {
        continue
      }
    }

    // 创建修正后的点
    const fixedPoint = { ...p, lat, lng }

    if (result.length === 0) {
      result.push(fixedPoint)
      lastValid = fixedPoint
      continue
    }

    const dist = haversineDistance(lastValid.lat, lastValid.lng, fixedPoint.lat, fixedPoint.lng)
    const timeDiff = (new Date(fixedPoint.time).getTime() - new Date(lastValid.time).getTime()) / 3600000
    if (timeDiff <= 0) {
      // 时间相同或倒退，保留点但不更新 lastValid（避免速度计算问题）
      result.push(fixedPoint)
      continue
    }
    const speed = dist / timeDiff
    // 速度超过 60 km/h 才认为是异常漂移（放宽阈值减少过滤）
    if (speed < 60) {
      result.push(fixedPoint)
      lastValid = fixedPoint
    } else {
      // 超速异常点依然保留在轨迹中，只是不更新lastValid避免下一次误判
      result.push(fixedPoint)
      console.warn(`GPS jump detected, speed: ${speed.toFixed(1)} km/h (kept point but not used as reference)`)
    }
  }
  filteredPoints.value = result
}

// 计算各项统计数据
function calculateStats() {
  if (filteredPoints.value.length < 2) {
    totalDistance.value = 0
    avgSpeed.value = 0
    maxSpeed.value = 0
    workingDuration.value = '0s'
    movingDuration.value = '0s'
    return
  }
  let distance = 0
  let totalSpeed = 0
  maxSpeed.value = 0
  let workingSeconds = 0
  let movingSeconds = 0

  for (let i = 1; i < filteredPoints.value.length; i++) {
    const p1 = filteredPoints.value[i - 1]
    const p2 = filteredPoints.value[i]
    const dist = haversineDistance(p1.lat, p1.lng, p2.lat, p2.lng)
    distance += dist

    const timeDiffHours = (new Date(p2.time).getTime() - new Date(p1.time).getTime()) / 3600000
    if (timeDiffHours > 0) {
      const speed = dist / timeDiffHours
      totalSpeed += speed
      if (speed > maxSpeed.value) {
        maxSpeed.value = speed
      }
    }

    // 统计激光工作状态，假设数据中有 isWorking 字段
    const p1Time = new Date(p1.time).getTime()
    const p2Time = new Date(p2.time).getTime()
    const segmentSeconds = (p2Time - p1Time) / 1000
    if (p1.isWorking || p1.laserOn) {
      workingSeconds += segmentSeconds
    } else {
      movingSeconds += segmentSeconds
    }
  }

  totalDistance.value = distance
  avgSpeed.value = totalSpeed / (filteredPoints.value.length - 1)

  // 格式化时长
  workingDuration.value = formatDuration(workingSeconds)
  movingDuration.value = formatDuration(movingSeconds)
}

// 格式化时长
function formatDuration(seconds) {
  if (seconds < 60) return `${Math.round(seconds)}s`
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`
  const minutes = Math.round((seconds % 3600) / 60)
  return `${Math.floor(seconds / 3600)}h ${minutes}m`
}

// Haversine formula to calculate distance between two coordinates in km
function haversineDistance(lat1, lon1, lat2, lon2) {
  const R = 6371 // Earth radius in km
  const dLat = toRad(lat2 - lat1)
  const dLon = toRad(lon2 - lon1)
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return R * c
}

function toRad(deg) {
  return deg * Math.PI / 180
}

// 转换为 Leaflet 经纬度数组 (Leaflet 使用 纬度,经度 顺序)
function toLatLng(p) {
  const lat = Number(p.lat)
  const lng = Number(p.lng)
  if (isNaN(lat) || isNaN(lng) || !isFinite(lat) || !isFinite(lng)) {
    return null
  }
  return [lat, lng]
}

// 根据状态获取颜色
function getSegmentColor(point) {
  // 根据激光工作状态返回不同颜色
  // 绿色: 激光工作中, 蓝色: 移动中, 红色: 故障/报警
  if (point.isFault || point.alarm) {
    return '#f56c6c'
  }
  if (point.isWorking || point.laserOn) {
    return '#67c23a'
  }
  return '#409eff'
}

// 自适应到轨迹范围
function fitMapToTrajectory() {
  // 1. 地图不存在 / 无轨迹点 直接返回
  if (!map || !filteredPoints.value || filteredPoints.value.length === 0) return

  // 2. 严格过滤 有效坐标（必须是数字，不能是 NaN）
  const validPoints = filteredPoints.value.filter(p => {
    const lat = Number(p.lat)
    const lng = Number(p.lng)
    return !isNaN(lat) && !isNaN(lng) && isFinite(lat) && isFinite(lng)
  })

  // 3. 无有效坐标直接返回
  if (validPoints.length === 0) return

  // 4. Leaflet 自适应边界
  const bounds = L.latLngBounds(validPoints.map(p => toLatLng(p)).filter(ll => ll !== null))

  // 5. 安全调用 - 减小padding提高放大倍数，让轨迹更清晰
  try {
    map.fitBounds(bounds, { padding: [10, 10], maxZoom: 22, minZoom: 18 })
  } catch (e) {
    console.warn('Fit bounds failed', e)
  }
}

function updateMap() {
  if (!window.L) {
    setTimeout(updateMap, 200)
    return
  }

  clearMap()

  if (filteredPoints.value.length === 0) return

  // 创建分段折线，每段根据状态着色
  polylineLayers = []
  if (filteredPoints.value.length < 2) return
  
  // 优化：将连续相同颜色的线段合并为一条折线
  let currentPath = []
  let currentColor = null
  
  for (let i = 0; i < filteredPoints.value.length; i++) {
    const p = filteredPoints.value[i]
    const point = toLatLng(p)
    
    // 跳过无效点
    if (!point) continue
    
    if (i === 0) {
      // 第一个点，开始新路径
      currentPath.push(point)
      currentColor = getSegmentColor(p)
    } else {
      const prevPoint = toLatLng(filteredPoints.value[i - 1])
      if (!prevPoint) continue
      
      const color = getSegmentColor(filteredPoints.value[i - 1])
      
      if (color === currentColor) {
        // 颜色相同，继续添加到当前路径
        currentPath.push(point)
      } else {
        // 颜色不同，创建当前路径的折线并开始新路径
        if (currentPath.length > 1) {
          const polyline = L.polyline(currentPath, {
            color: currentColor,
            weight: 4,
            opacity: 0.85
          })
          polyline.addTo(map)
          polylineLayers.push(polyline)
        }
        currentPath = [prevPoint, point]
        currentColor = color
      }
    }
  }
  
  // 添加最后一条路径
  if (currentPath.length > 1) {
    const polyline = L.polyline(currentPath, {
      color: currentColor,
      weight: 4,
      opacity: 0.85
    })
    polyline.addTo(map)
    polylineLayers.push(polyline)
  }

  // 添加所有轨迹点（可显示隐藏）
  if (showPoints.value) {
    addPointMarkers()
  }

  // 添加起点和终点标记
  const startPoint = filteredPoints.value[0]
  const endPoint = filteredPoints.value[filteredPoints.value.length - 1]
  const startPosition = toLatLng(startPoint)
  const endPosition = toLatLng(endPoint)

  // 创建起点图标 SVG
  const startIconHtml = `
    <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36">
      <circle cx="18" cy="18" r="16" fill="#67c23a" stroke="white" stroke-width="3"/>
      <text x="18" y="24" text-anchor="middle" fill="white" font-weight="bold" font-size="16">S</text>
    </svg>
  `
  const startIcon = L.divIcon({
    html: startIconHtml,
    className: 'custom-marker',
    iconSize: [36, 36],
    iconAnchor: [18, 36]
  })

  // 创建终点图标 SVG
  const endIconHtml = `
    <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36">
      <circle cx="18" cy="18" r="16" fill="#f56c6c" stroke="white" stroke-width="3"/>
      <text x="18" y="24" text-anchor="middle" fill="white" font-weight="bold" font-size="16">E</text>
    </svg>
  `
  const endIcon = L.divIcon({
    html: endIconHtml,
    className: 'custom-marker',
    iconSize: [36, 36],
    iconAnchor: [18, 36]
  })

  if (startPosition) {
    startMarker = L.marker(startPosition, { icon: startIcon })
    startMarker.addTo(map)
    const popupContent = `
      <div class="custom-popup">
        <div class="popup-title">起点</div>
        <div class="popup-row"><span>时间:</span> ${startPoint.time}</div>
        <div class="popup-row"><span>坐标:</span> ${startPoint.lat.toFixed(6)}, ${startPoint.lng.toFixed(6)}</div>
        ${startPoint.speed ? `<div class="popup-row"><span>速度:</span> ${startPoint.speed.toFixed(1)} km/h</div>` : ''}
        ${startPoint.isWorking !== undefined ? `<div class="popup-row"><span>激光:</span> ${startPoint.isWorking ? '工作中' : '停止'}</div>` : ''}
      </div>
    `
    startMarker.bindPopup(popupContent)
  }

  if (endPosition) {
    endMarker = L.marker(endPosition, { icon: endIcon })
    endMarker.addTo(map)
    const popupContent = `
      <div class="custom-popup">
        <div class="popup-title">终点</div>
        <div class="popup-row"><span>时间:</span> ${endPoint.time}</div>
        <div class="popup-row"><span>坐标:</span> ${endPoint.lat.toFixed(6)}, ${endPoint.lng.toFixed(6)}</div>
        ${endPoint.speed ? `<div class="popup-row"><span>速度:</span> ${endPoint.speed.toFixed(1)} km/h</div>` : ''}
        ${endPoint.isWorking !== undefined ? `<div class="popup-row"><span>激光:</span> ${endPoint.isWorking ? '工作中' : '停止'}</div>` : ''}
      </div>
    `
    endMarker.bindPopup(popupContent)
  }

  // 自适应缩放 - 延迟确保渲染完成
  setTimeout(() => {
    fitMapToTrajectory()
  }, 100)
}

// 添加轨迹点标记
function addPointMarkers() {
  pointMarkers = []
  // 根据缩放级别调整显示密度
  const zoom = map.getZoom()
  const totalPoints = filteredPoints.value.length
  
  // 动态调整显示密度，确保标记数量不会太多
  let skipRatio = 1
  if (totalPoints > 1000) {
    skipRatio = Math.max(1, Math.floor(totalPoints / 500))
  } else if (totalPoints > 500) {
    skipRatio = Math.max(1, Math.floor(totalPoints / 250))
  } else if (totalPoints > 200) {
    skipRatio = Math.max(1, Math.floor(totalPoints / 100))
  }
  
  // 缩放级别越低，显示的点越少
  if (zoom < 12) {
    skipRatio *= 2
  } else if (zoom < 14) {
    skipRatio *= 1.5
  }
  
  skipRatio = Math.floor(skipRatio)

  filteredPoints.value.forEach((p, i) => {
    if (i % skipRatio !== 0) return

    const position = toLatLng(p)
    if (!position) return

    const color = getSegmentColor(p)
    const iconHtml = `
      <svg xmlns="http://www.w3.org/2000/svg" width="8" height="8">
        <circle cx="4" cy="4" r="3" fill="${color}" stroke="white" stroke-width="1"/>
      </svg>
    `
    const icon = L.divIcon({
      html: iconHtml,
      className: 'custom-point-marker',
      iconSize: [8, 8],
      iconAnchor: [4, 4]
    })

    const marker = L.marker(position, { icon: icon })
    const popupContent = `
      <div class="custom-popup">
        <div class="popup-row"><span>时间:</span> ${p.time}</div>
        <div class="popup-row"><span>坐标:</span> ${p.lat.toFixed(6)}, ${p.lng.toFixed(6)}</div>
        ${p.speed ? `<div class="popup-row"><span>速度:</span> ${p.speed.toFixed(1)} km/h</div>` : ''}
        ${p.isWorking !== undefined ? `<div class="popup-row"><span>激光:</span> ${p.isWorking ? '工作中' : '停止'}</div>` : ''}
      </div>
    `
    marker.bindPopup(popupContent)
    marker.addTo(map)
    pointMarkers.push(marker)
  })

  // 根据缩放级别更新密度
  if (!window.zoomHandlerAdded) {
    window.zoomHandlerAdded = true
    map.on('zoomend', () => {
      // 防抖处理，避免频繁更新
      if (window.zoomTimeout) {
        clearTimeout(window.zoomTimeout)
      }
      window.zoomTimeout = setTimeout(() => {
        clearPointMarkers()
        if (showPoints.value) {
          addPointMarkers()
        }
      }, 300)
    })
  }
}

function clearPointMarkers() {
  if (pointMarkers && pointMarkers.length > 0) {
    pointMarkers.forEach(m => map.removeLayer(m))
    pointMarkers = []
  }
}

function clearMap() {
  if (polylineLayers && polylineLayers.length > 0) {
    polylineLayers.forEach(p => map.removeLayer(p))
    polylineLayers = []
  }
  // 清除增量绘制的回放图层
  clearPlaybackLayers()
  if (startMarker) {
    map.removeLayer(startMarker)
    startMarker = null
  }
  if (endMarker) {
    map.removeLayer(endMarker)
    endMarker = null
  }
  clearPointMarkers()
  if (playbackMarker) {
    map.removeLayer(playbackMarker)
    playbackMarker = null
  }
}

// 清除回放增量绘制图层
function clearPlaybackLayers() {
  if (playbackPolylineLayers && playbackPolylineLayers.length > 0) {
    playbackPolylineLayers.forEach(p => map.removeLayer(p))
    playbackPolylineLayers = []
  }
  if (playbackPointMarkers && playbackPointMarkers.length > 0) {
    playbackPointMarkers.forEach(m => map.removeLayer(m))
    playbackPointMarkers = []
  }
  lastPlaybackIndex = 0
}

// 添加起点和终点标记（用于回放停止后）
function addStartEndMarkers() {
  if (!map || filteredPoints.value.length === 0) return

  // 清除已有的起点终点标记
  if (startMarker) {
    map.removeLayer(startMarker)
    startMarker = null
  }
  if (endMarker) {
    map.removeLayer(endMarker)
    endMarker = null
  }

  const startPoint = filteredPoints.value[0]
  const endPoint = filteredPoints.value[filteredPoints.value.length - 1]
  const startPosition = toLatLng(startPoint)
  const endPosition = toLatLng(endPoint)

  // 创建起点图标 SVG
  const startIconHtml = `
    <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36">
      <circle cx="18" cy="18" r="16" fill="#67c23a" stroke="white" stroke-width="3"/>
      <text x="18" y="24" text-anchor="middle" fill="white" font-weight="bold" font-size="16">S</text>
    </svg>
  `
  const startIcon = L.divIcon({
    html: startIconHtml,
    className: 'custom-marker',
    iconSize: [36, 36],
    iconAnchor: [18, 36]
  })

  // 创建终点图标 SVG
  const endIconHtml = `
    <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36">
      <circle cx="18" cy="18" r="16" fill="#f56c6c" stroke="white" stroke-width="3"/>
      <text x="18" y="24" text-anchor="middle" fill="white" font-weight="bold" font-size="16">E</text>
    </svg>
  `
  const endIcon = L.divIcon({
    html: endIconHtml,
    className: 'custom-marker',
    iconSize: [36, 36],
    iconAnchor: [18, 36]
  })

  if (startPosition) {
    startMarker = L.marker(startPosition, { icon: startIcon })
    startMarker.addTo(map)
    const popupContent = `
      <div class="custom-popup">
        <div class="popup-title">起点</div>
        <div class="popup-row"><span>时间:</span> ${startPoint.time}</div>
        <div class="popup-row"><span>坐标:</span> ${startPoint.lat.toFixed(6)}, ${startPoint.lng.toFixed(6)}</div>
        ${startPoint.speed ? `<div class="popup-row"><span>速度:</span> ${startPoint.speed.toFixed(1)} km/h</div>` : ''}
        ${startPoint.isWorking !== undefined ? `<div class="popup-row"><span>激光:</span> ${startPoint.isWorking ? '工作中' : '停止'}</div>` : ''}
      </div>
    `
    startMarker.bindPopup(popupContent)
  }

  if (endPosition) {
    endMarker = L.marker(endPosition, { icon: endIcon })
    endMarker.addTo(map)
    const popupContent = `
      <div class="custom-popup">
        <div class="popup-title">终点</div>
        <div class="popup-row"><span>时间:</span> ${endPoint.time}</div>
        <div class="popup-row"><span>坐标:</span> ${endPoint.lat.toFixed(6)}, ${endPoint.lng.toFixed(6)}</div>
        ${endPoint.speed ? `<div class="popup-row"><span>速度:</span> ${endPoint.speed.toFixed(1)} km/h</div>` : ''}
        ${endPoint.isWorking !== undefined ? `<div class="popup-row"><span>激光:</span> ${endPoint.isWorking ? '工作中' : '停止'}</div>` : ''}
      </div>
    `
    endMarker.bindPopup(popupContent)
  }
}

// 切换地图图层
function changeMapLayer() {
  if (!window.L || !map || !tileLayer) return

  map.removeLayer(tileLayer)

  if (currentLayer.value === 'satellite') {
    // 高德地图卫星影像
    tileLayer = L.tileLayer('https://webst0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=6&x={x}&y={y}&z={z}', {
      attribution: '&copy; <a href="https://www.amap.com/">高德地图</a>',
      subdomains: ['1', '2', '3', '4'],
      maxNativeZoom: 18,  // 关键：瓦片服务的实际最大级别
      maxZoom: 22         // 允许地图缩放控件的上限，超出部分会自动拉伸
    })
  } else {
    // 高德地图标准图层
    tileLayer = L.tileLayer('https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}', {
      attribution: '&copy; <a href="https://www.amap.com/">高德地图</a>',
      subdomains: ['1', '2', '3', '4'],
      maxNativeZoom: 18,  // 关键：瓦片服务的实际最大级别
      maxZoom: 22         // 允许地图缩放控件的上限，超出部分会自动拉伸
    })
  }

  tileLayer.addTo(map)
}

function updateMapSize() {
  if (map) {
    map.invalidateSize()
  }
}

// ==================== 轨迹回放 ====================
const totalDuration = computed(() => {
  if (filteredPoints.value.length < 2) return '0s'
  const start = new Date(filteredPoints.value[0].time).getTime()
  const end = new Date(filteredPoints.value[filteredPoints.value.length - 1].time).getTime()
  return formatDuration((end - start) / 1000)
})

const currentPlaybackTime = computed(() => {
  if (filteredPoints.value.length < 2) return '0s'
  const index = Math.floor((playbackProgress.value / 100) * (filteredPoints.value.length - 1))
  return filteredPoints.value[Math.max(0, index)].time || ''
})

function togglePlayPause() {
  if (isPlaying.value) {
    pausePlayback()
  } else {
    if (playbackProgress.value >= 100) {
      // 播放结束，重新开始
      playbackProgress.value = 0
      startPlayback()
    } else if (lastPlaybackIndex === 0 && playbackProgress.value === 0) {
      // 从头开始播放
      startPlayback()
    } else {
      // 从暂停处继续
      resumePlayback()
    }
  }
}

function startPlayback() {
  if (filteredPoints.value.length < 2) return

  isPlaying.value = true

  // 开始回放时：清除原有完整轨迹，准备增量绘制
  if (polylineLayers && polylineLayers.length > 0) {
    polylineLayers.forEach(p => map.removeLayer(p))
    polylineLayers = []
  }
  clearPointMarkers()
  clearPlaybackLayers()
  lastPlaybackIndex = 0

  // 创建播放标记
  if (!playbackMarker) {
    const robotIconHtml = `
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24">
        <circle cx="12" cy="12" r="10" fill="#e6a23c" stroke="white" stroke-width="2"/>
        <text x="12" y="17" text-anchor="middle" fill="white" font-weight="bold" font-size="12">R</text>
      </svg>
    `
    const robotIcon = L.divIcon({
      html: robotIconHtml,
      className: 'custom-marker',
      iconSize: [24, 24],
      iconAnchor: [12, 12]
    })
    playbackMarker = L.marker(toLatLng(filteredPoints.value[0]), { icon: robotIcon, zIndexOffset: 1000 })
    playbackMarker.addTo(map)
  }

  // 计算当前进度对应的起始索引
  const startIndex = Math.floor((playbackProgress.value / 100) * (filteredPoints.value.length - 1))
  lastPlaybackIndex = 0

  // 如果从非0进度开始，先绘制到当前位置
  if (startIndex > 0) {
    updateIncrementalDrawing(0, startIndex)
  } else if (showPoints.value) {
    // 添加第一个点
    addPlaybackPoint(0)
  }

  // 更新播放标记位置
  updatePlaybackPosition()

  // 开始播放定时器 - 逐点依次出现
  const step = () => {
    if (!isPlaying.value) return
    const prevIndex = lastPlaybackIndex

    // 已经到终点了，结束播放
    if (prevIndex >= filteredPoints.value.length - 1) {
      playbackProgress.value = 100
      stopPlayback()
      return
    }

    // 每次只前进一个点，逐次出现路线
    const targetIndex = prevIndex + 1

    // 更新进度百分比
    playbackProgress.value = (targetIndex / (filteredPoints.value.length - 1)) * 100

    // 增量绘制这一个点和对应的线段
    updateIncrementalDrawing(prevIndex, targetIndex)
    updatePlaybackPosition()

    // 根据速度计算下一帧间隔，速度越快间隔越小
    const interval = 100 / parseFloat(playbackSpeed.value)
    playbackTimer = setTimeout(step, interval)
  }
  // 按照速度决定启动间隔
  const interval = 100 / parseFloat(playbackSpeed.value)
  playbackTimer = setTimeout(step, interval)
}

function pausePlayback() {
  isPlaying.value = false
  if (playbackTimer) {
    clearTimeout(playbackTimer)
    playbackTimer = null
  }
}

// 从暂停处继续播放
function resumePlayback() {
  if (filteredPoints.value.length < 2) return

  isPlaying.value = true

  // 确保播放标记存在
  if (!playbackMarker) {
    const robotIconHtml = `
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24">
        <circle cx="12" cy="12" r="10" fill="#e6a23c" stroke="white" stroke-width="2"/>
        <text x="12" y="17" text-anchor="middle" fill="white" font-weight="bold" font-size="12">R</text>
      </svg>
    `
    const robotIcon = L.divIcon({
      html: robotIconHtml,
      className: 'custom-marker',
      iconSize: [24, 24],
      iconAnchor: [12, 12]
    })
    const currentPoint = filteredPoints.value[Math.max(0, lastPlaybackIndex)]
    playbackMarker = L.marker(toLatLng(currentPoint), { icon: robotIcon, zIndexOffset: 1000 })
    playbackMarker.addTo(map)
  }

  // 继续播放定时器 - 逐点依次出现
  const step = () => {
    if (!isPlaying.value) return
    const prevIndex = lastPlaybackIndex

    // 已经到终点了，结束播放
    if (prevIndex >= filteredPoints.value.length - 1) {
      playbackProgress.value = 100
      stopPlayback()
      return
    }

    // 每次只前进一个点，逐次出现路线
    const targetIndex = prevIndex + 1

    // 更新进度百分比
    playbackProgress.value = (targetIndex / (filteredPoints.value.length - 1)) * 100

    // 增量绘制这一个点和对应的线段
    updateIncrementalDrawing(prevIndex, targetIndex)
    updatePlaybackPosition()

    // 根据速度计算下一帧间隔，速度越快间隔越小
    const interval = 100 / parseFloat(playbackSpeed.value)
    playbackTimer = setTimeout(step, interval)
  }
  // 按照速度决定启动间隔
  const interval = 100 / parseFloat(playbackSpeed.value)
  playbackTimer = setTimeout(step, interval)
}

// 重新绘制完整优化后的轨迹
function redrawFullTrajectory() {
  polylineLayers = []
  if (filteredPoints.value.length < 2) return

  // 重新使用优化绘制：连续相同颜色合并
  let currentPath = []
  let currentColor = null

  for (let i = 0; i < filteredPoints.value.length; i++) {
    const p = filteredPoints.value[i]
    const point = toLatLng(p)
    if (!point) continue

    if (i === 0) {
      currentPath.push(point)
      currentColor = getSegmentColor(p)
    } else {
      const prevPoint = toLatLng(filteredPoints.value[i - 1])
      if (!prevPoint) continue

      const color = getSegmentColor(filteredPoints.value[i - 1])
      if (color === currentColor) {
        currentPath.push(point)
      } else {
        if (currentPath.length > 1) {
          const polyline = L.polyline(currentPath, {
            color: currentColor,
            weight: 4,
            opacity: 0.85
          })
          polyline.addTo(map)
          polylineLayers.push(polyline)
        }
        currentPath = [prevPoint, point]
        currentColor = color
      }
    }
  }

  if (currentPath.length > 1) {
    const polyline = L.polyline(currentPath, {
      color: currentColor,
      weight: 4,
      opacity: 0.85
    })
    polyline.addTo(map)
    polylineLayers.push(polyline)
  }

  // 重新添加轨迹点标记
  if (showPoints.value) {
    addPointMarkers()
  }
}

// 切换轨迹点显示需要同时处理回放增量点
function togglePointsVisibility() {
  if (isPlaying.value || lastPlaybackIndex > 0) {
    // 回放中或回放暂停后，只处理增量点
    if (playbackPointMarkers && playbackPointMarkers.length > 0) {
      playbackPointMarkers.forEach(m => {
        if (showPoints.value) {
          if (!map.hasLayer(m)) map.addLayer(m)
        } else {
          if (map.hasLayer(m)) map.removeLayer(m)
        }
      })
    }
  } else {
    // 正常状态，处理完整点
    clearPointMarkers()
    if (showPoints.value) {
      addPointMarkers()
    }
  }
}

function stopPlayback() {
  isPlaying.value = false
  if (playbackTimer) {
    clearTimeout(playbackTimer)
    playbackTimer = null
  }
  // 只清除播放标记
  if (playbackMarker) {
    map.removeLayer(playbackMarker)
    playbackMarker = null
  }
  // 如果有回放轨迹（playbackPolylineLayers 不为空），则保留它，清除普通轨迹图层
  if (playbackPolylineLayers && playbackPolylineLayers.length > 0) {
    // 保留 playbackPolylineLayers 和 playbackPointMarkers，轨迹保持逐步出现的状态
    // 清除普通轨迹图层（回放时已隐藏）
    if (polylineLayers && polylineLayers.length > 0) {
      polylineLayers.forEach(p => map.removeLayer(p))
      polylineLayers = []
    }
  } else {
    // 如果没有回放轨迹（playbackPolylineLayers 为空），则保留普通轨迹图层
    // 只清除回放相关的图层（如果有）
    clearPlaybackLayers()
  }
  // 重新添加起点和终点标记（因为回放时可能隐藏了）
  addStartEndMarkers()
  // 重置进度
  playbackProgress.value = 0
  lastPlaybackIndex = 0
}

// 增量绘制：从 fromIndex 到 toIndex 添加点和线段
function updateIncrementalDrawing(fromIndex, toIndex) {
  if (fromIndex >= toIndex) return

  for (let i = fromIndex; i < toIndex; i++) {
    // 添加线段 i -> i+1
    const p1 = filteredPoints.value[i]
    const p2 = filteredPoints.value[i + 1]
    const pos1 = toLatLng(p1)
    const pos2 = toLatLng(p2)
    if (pos1 && pos2) {
      const color = getSegmentColor(p1)
      const polyline = L.polyline([pos1, pos2], {
        color: color,
        weight: 4,
        opacity: 0.85
      })
      polyline.addTo(map)
      playbackPolylineLayers.push(polyline)
    }
    // 添加轨迹点（如果开启显示）
    if (showPoints.value && i + 1 <= toIndex) {
      addPlaybackPoint(i + 1)
    }
  }
  lastPlaybackIndex = toIndex
}

// 添加单个回放轨迹点
function addPlaybackPoint(index) {
  const p = filteredPoints.value[index]
  const position = toLatLng(p)
  if (!position) return

  // 根据缩放级别调整显示密度，和 addPointMarkers 保持一致
  const zoom = map.getZoom()
  const totalPoints = filteredPoints.value.length
  let skipRatio = 1
  if (totalPoints > 1000) {
    skipRatio = Math.max(1, Math.floor(totalPoints / 500))
  } else if (totalPoints > 500) {
    skipRatio = Math.max(1, Math.floor(totalPoints / 250))
  } else if (totalPoints > 200) {
    skipRatio = Math.max(1, Math.floor(totalPoints / 100))
  }
  if (zoom < 12) {
    skipRatio *= 2
  } else if (zoom < 14) {
    skipRatio *= 1.5
  }
  skipRatio = Math.floor(skipRatio)

  if (index % skipRatio !== 0) return

  const color = getSegmentColor(p)
  const iconHtml = `
    <svg xmlns="http://www.w3.org/2000/svg" width="8" height="8">
      <circle cx="4" cy="4" r="3" fill="${color}" stroke="white" stroke-width="1"/>
    </svg>
  `
  const icon = L.divIcon({
    html: iconHtml,
    className: 'custom-point-marker',
    iconSize: [8, 8],
    iconAnchor: [4, 4]
  })

  const marker = L.marker(position, { icon: icon })
  const popupContent = `
    <div class="custom-popup">
      <div class="popup-row"><span>时间:</span> ${p.time}</div>
      <div class="popup-row"><span>坐标:</span> ${p.lat.toFixed(6)}, ${p.lng.toFixed(6)}</div>
      ${p.speed ? `<div class="popup-row"><span>速度:</span> ${p.speed.toFixed(1)} km/h</div>` : ''}
      ${p.isWorking !== undefined ? `<div class="popup-row"><span>激光:</span> ${p.isWorking ? '工作中' : '停止'}</div>` : ''}
    </div>
  `
  marker.bindPopup(popupContent)
  marker.addTo(map)
  playbackPointMarkers.push(marker)
}

function updatePlaybackPosition() {
  if (!playbackMarker || filteredPoints.value.length === 0) return
  const index = Math.floor((playbackProgress.value / 100) * (filteredPoints.value.length - 1))
  const point = filteredPoints.value[Math.max(0, index)]
  const position = toLatLng(point)
  if (position) {
    playbackMarker.setLatLng(position)
  }
}

function seekToProgress() {
  // 如果在回放模式（已经开始增量绘制）
  if (isPlaying.value || lastPlaybackIndex > 0 || playbackMarker !== null) {
    const targetIndex = Math.floor((playbackProgress.value / 100) * (filteredPoints.value.length - 1))
    if (targetIndex > lastPlaybackIndex) {
      // 需要向前绘制，添加新增的部分
      updateIncrementalDrawing(lastPlaybackIndex, targetIndex)
    } else if (targetIndex < lastPlaybackIndex) {
      // 需要向后跳转，清除现有增量重新绘制
      clearPlaybackLayers()
      updateIncrementalDrawing(0, targetIndex)
    }
  }
  updatePlaybackPosition()
}

function updatePlaybackSpeed() {
  // 速度已通过 v-model 绑定
}

// ==================== 导出功能 ====================
function exportTrajectoryJSON() {
  const dataStr = JSON.stringify(filteredPoints.value, null, 2)
  const blob = new Blob([dataStr], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `trajectory_${new Date().toISOString().slice(0, 10)}.json`
  a.click()
  URL.revokeObjectURL(url)
}

function exportTrajectoryCSV() {
  const headers = ['time,lat,lng,speed,isWorking']
  const rows = filteredPoints.value.map(p => {
    return `${p.time},${p.lat},${p.lng},${p.speed || ''},${p.isWorking || ''}`
  })
  const csv = [headers, ...rows].join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `trajectory_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

async function exportMapImage() {
  const mapContainer = document.getElementById('trajectory-map')
  if (!mapContainer) {
    ElMessage.error('找不到地图容器')
    return
  }

  try {
    // 使用 html2canvas 捕获地图容器
    const canvas = await html2canvas(mapContainer, {
      useCORS: true,
      allowTaint: true,
      backgroundColor: '#ffffff',
      scale: 2 // 提高清晰度
    })

    // 转换为 blob 并下载
    canvas.toBlob((blob) => {
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.download = `trajectory-map-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.png`
      a.href = url
      a.click()
      URL.revokeObjectURL(url)
      ElMessage.success('地图图片导出成功')
    }, 'image/png', 0.95)
  } catch (error) {
    console.error('导出地图图片失败:', error)
    ElMessage.error('导出失败: ' + error.message)
  }
}

onMounted(() => {
  // 初始化默认时间
  initDefaultTime()
  // 加载 Leaflet CSS
  if (!document.querySelector('link[href*="leaflet.css"]')) {
    const link = document.createElement('link')
    link.rel = 'stylesheet'
    link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'
    document.head.appendChild(link)
  }
  // 加载 Leaflet JS API
  if (!document.querySelector('script[src*="leaflet.js"]')) {
    const script = document.createElement('script')
    script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
    script.onload = initMap
    document.head.appendChild(script)
  } else {
    if (window.L) {
      initMap()
    } else {
      setTimeout(initMap, 200)
    }
  }

  window.addEventListener('resize', updateMapSize)
  document.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateMapSize)
  document.removeEventListener('keydown', handleKeyDown)
  stopPlayback()
  if (map) {
    map.remove()
    map = null
  }
})

function initMap() {
  if (!document.getElementById('trajectory-map')) return

  // 默认中心设为北京，如果有轨迹会自动缩放
  map = L.map('trajectory-map', {
    center: [39.9087, 116.3975],
    zoom: 13,
    zoomControl: true,
    minZoom: 1,
    maxZoom: 18 // 改成18，不能超过瓦片实际最大级别
  })

  // 添加瓦片图层 - 使用国内可访问的瓦片
  if (currentLayer.value === 'satellite') {
    // 高德地图卫星影像
    tileLayer = L.tileLayer('https://webst0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=6&x={x}&y={y}&z={z}', {
      attribution: '&copy; <a href="https://www.amap.com/">高德地图</a>',
      subdomains: ['1', '2', '3', '4'],
      maxNativeZoom: 18,  // 关键：瓦片服务的实际最大级别
      maxZoom: 22         // 允许地图缩放控件的上限，超出部分会自动拉伸
    })
  } else {
    // 高德地图标准图层
    tileLayer = L.tileLayer('https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}', {
      attribution: '&copy; <a href="https://www.amap.com/">高德地图</a>',
      subdomains: ['1', '2', '3', '4'],
      maxNativeZoom: 18,  // 关键：瓦片服务的实际最大级别
      maxZoom: 22         // 允许地图缩放控件的上限，超出部分会自动拉伸
    })
  }
  tileLayer.addTo(map)

  // 如果已经有数据，更新地图
  setTimeout(() => {
    if (points.value.length > 0) {
      filterOutliers()
      updateMap()
      calculateStats()
    }
  }, 100)
}
</script>

<style scoped>
.trajectory-page {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-height: 100vh;
  background: var(--app-background);
}

.main-card {
  padding: 24px;
  border-radius: 16px;
  overflow: hidden;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  background: rgba(255, 255, 255, 0.05);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 20px;
  color: var(--text-primary);
  letter-spacing: -0.3px;
  margin-bottom: 24px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.header-actions {
  display: flex;
  gap: 8px;
}

.filter-bar {
  margin-bottom: 20px;
}

.quick-select {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.quick-select :deep(.el-button) {
  background: rgba(255, 255, 255, 0.05) !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
  color: var(--text-primary) !important;
}

.quick-select :deep(.el-button:hover) {
  background: rgba(255, 255, 255, 0.1) !important;
  border-color: var(--primary-color) !important;
  color: var(--text-primary) !important;
}

.quick-select :deep(.el-button--primary) {
  background: var(--primary-color) !important;
  border-color: var(--primary-color) !important;
  color: white !important;
}

.quick-select :deep(.el-button--primary:hover) {
  background: #66b1ff !important;
  border-color: #66b1ff !important;
  color: white !important;
}

.quick-label {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 500;
}

.time-error {
  margin-top: 8px;
  padding: 10px 14px;
  background-color: rgba(245, 108, 108, 0.1);
  border: 1px solid rgba(245, 108, 108, 0.2);
  border-radius: 12px;
  color: #f56c6c;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.filter-form :deep(.el-date-picker__input) {
  background: rgba(255, 255, 255, 0.05) !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
  color: var(--text-primary) !important;
}

.filter-form :deep(.el-date-picker__input:focus) {
  border-color: var(--primary-color) !important;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2) !important;
}

.filter-form :deep(.el-date-picker__icon) {
  color: var(--text-secondary) !important;
}

.filter-form :deep(.el-button--primary) {
  background: var(--primary-color) !important;
  border-color: var(--primary-color) !important;
  color: white !important;
}

.filter-form :deep(.el-button--primary:hover) {
  background: #66b1ff !important;
  border-color: #66b1ff !important;
  color: white !important;
}

.filtered-info {
  font-size: 13px;
  color: var(--accent-orange);
  margin-left: 4px;
}

.map-wrapper {
  position: relative;
}

.map-wrapper.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  background: white;
  padding: 20px;
}

.map-container {
  height: 780px;
  width: 100%;
  position: relative;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  overflow: hidden;
  background: var(--app-background);
}

.map-wrapper.fullscreen .map-container {
  height: calc(100vh - 120px);
}

.map-loading, .map-empty {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  z-index: 10;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.empty-content svg {
  font-size: 48px;
}

/* 回放控件 */
.playback-controls {
  position: absolute;
  bottom: 20px;
  left: 20px;
  right: 20px;
  background: rgba(30, 30, 30, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 16px 20px;
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  gap: 16px;
  z-index: 1000;
  pointer-events: auto;
  color: white;
}

.playback-left {
  display: flex;
  align-items: center;
}

.playback-progress {
  flex: 1;
  margin: 0 16px;
}

.playback-time {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
  white-space: nowrap;
}

.playback-controls :deep(.el-button) {
  background: rgba(255, 255, 255, 0.2) !important;
  border-color: rgba(255, 255, 255, 0.3) !important;
  color: white !important;
}

.playback-controls :deep(.el-button:hover) {
  background: rgba(255, 255, 255, 0.3) !important;
  border-color: var(--primary-color) !important;
  color: white !important;
}

.playback-controls :deep(.el-select) {
  background: rgba(255, 255, 255, 0.1) !important;
  border-color: rgba(255, 255, 255, 0.2) !important;
  color: white !important;
}

.playback-controls :deep(.el-select__input) {
  color: white !important;
}

.playback-controls :deep(.el-select__caret) {
  color: rgba(255, 255, 255, 0.7) !important;
}

.playback-controls :deep(.el-slider__runway) {
  background-color: rgba(255, 255, 255, 0.5) !important;
  height: 8px !important;
}

.playback-controls :deep(.el-slider__bar) {
  background-color: var(--primary-color) !important;
  height: 8px !important;
}

.playback-controls :deep(.el-slider__button) {
  border-color: var(--primary-color) !important;
  width: 18px !important;
  height: 18px !important;
  margin-top: -5px !important;
  background-color: white !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2) !important;
}

/* 图层切换 */
.map-layer-switch {
  position: absolute;
  top: 12px;
  right: 12px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 6px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 10;
}

.map-layer-switch :deep(.el-radio-button__inner) {
  background: rgba(255, 255, 255, 0.1) !important;
  border-color: rgba(255, 255, 255, 0.2) !important;
  color: var(--text-secondary) !important;
}

.map-layer-switch :deep(.el-radio-button__orig-radio:checked + .el-radio-button__inner) {
  background: var(--primary-color) !important;
  border-color: var(--primary-color) !important;
  color: white !important;
}

/* 轨迹点开关 */
.point-toggle {
  position: absolute;
  top: 58px;
  right: 12px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 8px 12px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-secondary);
  z-index: 10;
}

.point-toggle :deep(.el-switch__core) {
  background-color: rgba(255, 255, 255, 0.2) !important;
}

.point-toggle :deep(.el-switch.is-checked .el-switch__core) {
  background-color: var(--primary-color) !important;
}

.actions-bar {
  margin-top: 16px;
  display: flex;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.actions-bar :deep(.el-button) {
  background: rgba(255, 255, 255, 0.05) !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
  color: var(--text-primary) !important;
}

.actions-bar :deep(.el-button:hover) {
  background: rgba(255, 255, 255, 0.1) !important;
  border-color: var(--primary-color) !important;
  color: var(--text-primary) !important;
}

.filter-info {
  margin-top: 16px;
  padding: 10px 14px;
  background-color: rgba(64, 158, 255, 0.1);
  border: 1px solid rgba(64, 158, 255, 0.2);
  border-radius: 12px;
  color: var(--primary-color);
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 重置按钮样式 */
.filter-form :deep(.el-button:not(.el-button--primary)) {
  background: rgba(255, 255, 255, 0.05) !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
  color: var(--text-primary) !important;
}

.filter-form :deep(.el-button:not(.el-button--primary):hover) {
  background: rgba(255, 255, 255, 0.1) !important;
  border-color: var(--primary-color) !important;
  color: var(--text-primary) !important;
}
</style>

<style>
/* Leaflet 样式修正 */
.leaflet-container {
  z-index: 1;
}

/* 自定义标记 */
.custom-marker {
  background: none;
  border: none;
}

.custom-point-marker {
  background: none;
  border: none;
}

/* 自定义弹出框样式调整 */
.custom-popup {
  padding: 8px;
  min-width: 180px;
}

.custom-popup .popup-title {
  font-weight: bold;
  font-size: 14px;
  margin-bottom: 6px;
  color: #303133;
}

.custom-popup .popup-row {
  font-size: 12px;
  margin: 4px 0;
}

.custom-popup .popup-row span {
  color: #606266;
}
</style>
