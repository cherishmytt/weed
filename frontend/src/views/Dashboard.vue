<template>
  <div class="dashboard-container">
    <section class="glass-panel core-status-card">
      <div class="panel-header">
        <span class="section-title">核心实时状态</span>
        <span class="live-badge"><span class="live-dot"></span>实时</span>
      </div>
      <div class="panel-body">
        <div class="core-status-grid">
          <!-- 上4 -->
          <div class="core-status-item status span-3">
            <div class="core-status-icon icon-blue">
              <el-icon class="icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 3 2 7.48 2 13s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.94-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg></el-icon>
            </div>
            <div class="core-status-info">
              <div class="core-status-label">机器人状态</div>
              <div class="core-status-value" :class="getStatusClass()">{{ dashboardData?.robotStatusText || '未知' }}</div>
            </div>
            <div class="card-glow glow-blue"></div>
          </div>

          <div class="core-status-item speed span-3">
            <div class="core-status-icon icon-blue">
              <el-icon class="icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M18.92 6.01C18.72 5.42 18.16 5 17.5 5h-11c-.66 0-1.21.42-1.42 1.01L3 12v8c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1h12v1c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-8l-2.08-5.99zM6.5 16c-.83 0-1.5-.67-1.5-1.5S5.67 13 6.5 13s1.5.67 1.5 1.5S7.33 16 6.5 16zm11 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zM5 11l1.5-4.5h11L19 11H5z"/></svg></el-icon>
            </div>
            <div class="core-status-info">
              <div class="core-status-label">推行速度</div>
              <div class="core-status-value">{{ currentStatus?.speed || 0 }} <span class="unit">m/s</span></div>
            </div>
            <div class="card-glow glow-blue"></div>
          </div>

          <div class="core-status-item gps span-3">
            <div class="core-status-icon icon-cyan">
              <el-icon class="icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg></el-icon>
            </div>
            <div class="core-status-info">
              <div class="core-status-label">坐标</div>
              <div class="core-status-value coord">{{ formatCoordinate(currentStatus?.latitude) }}, {{ formatCoordinate(currentStatus?.longitude) }}</div>
            </div>
            <div class="card-glow glow-cyan"></div>
          </div>

          <div class="core-status-item laser span-3">
            <div class="core-status-icon icon-green">
              <el-icon class="icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M13 10h-2v4h2v-4zm-1-7C6.48 3 2 7.48 2 13s4.48 10 10 10 10-4.48 10-10S17.52 3 12 3zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v2h-2V8z"/></svg></el-icon>
            </div>
            <div class="core-status-info">
              <div class="core-status-label">激光设备</div>
              <div class="core-status-value">
                <span class="core-status-tag" :class="currentStatus?.laserOn ? 'tag-success' : 'tag-info'">
                  <span class="tag-dot"></span>{{ currentStatus?.laserOn ? '已开启' : '已关闭' }}
                </span>
              </div>
            </div>
            <div class="card-glow glow-green"></div>
          </div>

          <!-- 下3 -->
          <div class="core-status-item battery span-4">
            <div class="core-status-icon icon-green">
              <el-icon class="icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M16 18H8V6h8v12zm0-14H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2z"/></svg></el-icon>
            </div>
            <div class="core-status-info">
              <div class="core-status-label">电池电量</div>
              <div class="core-status-value">{{ currentStatus?.battery || 0 }}<span class="unit">%</span></div>
              <div class="mini-bar">
                <div class="mini-bar-fill battery-fill" :style="{ width: (currentStatus?.battery || 0) + '%' }"></div>
              </div>
            </div>
            <div class="card-glow glow-green"></div>
          </div>

          <div class="core-status-item cpu span-4">
            <div class="core-status-icon icon-orange">
              <el-icon class="icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M4 5C4 3.34 5.34 2 7 2h10c1.66 0 3 1.34 3 3v14c0 1.66-1.34 3-3 3H7c-1.66 0-3-1.34-3-3V5zm16 0v14c0 .55-.45 1-1 1H7c-.55 0-1-.45-1-1V5c0-.55.45-1 1-1h10c.55 0 1 .45 1 1zm-3 9h-2v2h2v-2zm-4 0h-2v2h2v-2zm-4 0h-2v2h2v-2z"/></svg></el-icon>
            </div>
            <div class="core-status-info">
              <div class="core-status-label">CPU使用率</div>
              <div class="core-status-value">{{ currentStatus?.cpuUsage || 0 }}<span class="unit">%</span></div>
              <div class="mini-bar">
                <div class="mini-bar-fill cpu-fill" :style="{ width: (currentStatus?.cpuUsage || 0) + '%' }"></div>
              </div>
            </div>
            <div class="card-glow glow-orange"></div>
          </div>

          <div class="core-status-item temp span-4">
            <div class="core-status-icon icon-red">
              <el-icon class="icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M15 13V5a3 3 0 0 0-6 0v8a5 5 0 1 0 6 0z"/></svg></el-icon>
            </div>
            <div class="core-status-info">
              <div class="core-status-label">机身温度</div>
              <div class="core-status-value">{{ currentStatus?.temperature || 0 }}<span class="unit">℃</span></div>
              <div class="mini-bar">
                <div class="mini-bar-fill temp-fill" :style="{ width: Math.min((currentStatus?.temperature || 0) / 100 * 100, 100) + '%' }"></div>
              </div>
            </div>
            <div class="card-glow glow-red"></div>
          </div>
        </div>
      </div>
    </section>

    <section class="glass-panel device-params-card">
      <div class="panel-header">
        <span class="section-title">设备运行参数</span>
      </div>
      <div class="panel-body">
        <div ref="systemMetricsChart" class="system-chart-container"></div>
      </div>
    </section>

    <section class="glass-panel chart-card">
      <div class="panel-header">
        <span class="section-title">今日检测目标分布</span>
      </div>
      <div class="panel-body">
        <div class="detection-distribution">
          <div class="pie-container">
            <div ref="detectionPieChart" class="pie-chart"></div>
          </div>
          <div class="bar-container">
            <div class="bar-item">
              <div class="bar-header">
                <span class="bar-label"><span class="bar-dot dot-green"></span>作物</span>
                <span class="bar-value">{{ dashboardData?.cropTotalToday || 0 }}</span>
              </div>
              <div class="bar-progress">
                <div class="bar-fill crop-fill" :style="{ width: getCropPercentage() + '%' }"></div>
              </div>
            </div>
            <div class="bar-item">
              <div class="bar-header">
                <span class="bar-label"><span class="bar-dot dot-orange"></span>杂草</span>
                <span class="bar-value">{{ dashboardData?.weedTotalToday || 0 }}</span>
              </div>
              <div class="bar-progress">
                <div class="bar-fill weed-fill" :style="{ width: getWeedPercentage() + '%' }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="glass-panel stats-card">
      <div class="panel-header">
        <span class="section-title">今日作业统计</span>
      </div>
      <div class="panel-body">
        <div class="stats-grid">
          <div class="stats-item">
            <div class="stats-icon-wrap icon-blue-soft">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
            </div>
            <div class="stats-info">
              <div class="stats-label">今日总检测次数</div>
              <div class="stats-value">{{ dashboardData?.detectCountToday || 0 }}</div>
            </div>
          </div>
          <div class="stats-item">
            <div class="stats-icon-wrap icon-orange-soft">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>
            </div>
            <div class="stats-info">
              <div class="stats-label">杂草清除总量</div>
              <div class="stats-value">{{ dashboardData?.weedTotalToday || 0 }}</div>
            </div>
          </div>
          <div class="stats-item">
            <div class="stats-icon-wrap icon-green-soft">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M17 8C8 10 5.9 16.17 3.82 21H5.71c.26-.8.6-1.54.99-2.24A4.97 4.97 0 0 0 8 19c4 0 4-2 8-2s4 2 8 2v-2c0 0-2-1.38-4-2V8z"/></svg>
            </div>
            <div class="stats-info">
              <div class="stats-label">作物识别总量</div>
              <div class="stats-value">{{ dashboardData?.cropTotalToday || 0 }}</div>
            </div>
          </div>
          <div class="stats-item">
            <div class="stats-icon-wrap icon-red-soft">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M7 14l5-5 5 5z"/></svg>
            </div>
            <div class="stats-info">
              <div class="stats-label">今日激光作业次数</div>
              <div class="stats-value">{{ dashboardData?.laserFireToday || 0 }}<span class="stats-unit">次</span></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="glass-panel imu-card">
      <div class="panel-header">
        <span class="section-title">姿态 IMU</span>
      </div>
      <div class="panel-body">
        <div v-if="currentStatus?.imu" class="imu-content">
          <ImuAttitudeViewer :imu="currentStatus.imu" />
        </div>
        <div v-else class="no-data">
          暂无 IMU 数据
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import ImuAttitudeViewer from '@/components/ImuAttitudeViewer.vue'
import { getDashboardData } from '@/api/statistics'
import { getLatestStatus, getStatusHistory } from '@/api/robot'
import { getRobotStatusWs } from '@/utils/websocket'

const router = useRouter()
const dashboardData = ref(null)
const currentStatus = ref(null)
const systemMetricsChart = ref(null)
const detectionPieChart = ref(null)
let systemChart = null
let detectionPie = null
let isUnmounted = false
const maxDataPoints = 50
let ws = null

const chartData = {
  battery: [],
  cpu: [],
  temp: []
}

function formatCoordinate(val) {
  if (val == null) return '-'
  return Number(val).toFixed(6)
}

function getCropPercentage() {
  const crop = dashboardData.value?.cropTotalToday || 0
  const weed = dashboardData.value?.weedTotalToday || 0
  const total = crop + weed
  return total > 0 ? (crop / total) * 100 : 0
}

function getWeedPercentage() {
  const crop = dashboardData.value?.cropTotalToday || 0
  const weed = dashboardData.value?.weedTotalToday || 0
  const total = crop + weed
  return total > 0 ? (weed / total) * 100 : 0
}

function getStatusClass() {
  const status = dashboardData.value?.robotStatusText || ''
  if (status.includes('运行') || status.includes('作业')) {
    return 'status-running'
  } else if (status.includes('故障')) {
    return 'status-error'
  } else if (status.includes('待机')) {
    return 'status-idle'
  }
  return ''
}

async function loadDashboardData() {
  const res = await getDashboardData()
  if (res.code === 200) {
    dashboardData.value = res.data
  }
}

async function loadLatestStatus() {
  const res = await getLatestStatus()
  if (res.code === 200 && res.data) {
    currentStatus.value = res.data
  }
}

function initSystemMetricsChart() {
  if (!systemMetricsChart.value) return

  systemChart = echarts.init(systemMetricsChart.value)

  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(5, 17, 29, 0.95)',
      borderColor: 'rgba(89, 214, 255, 0.2)',
      borderRadius: 12,
      padding: [12, 16],
      textStyle: { color: '#eaf5ff', fontSize: 13 },
      axisPointer: { type: 'cross', lineStyle: { color: 'rgba(89, 214, 255, 0.3)' } }
    },
    legend: {
      data: ['电量 (%)', 'CPU使用率 (%)', '温度 (℃)'],
      top: 8,
      left: 'center',
      textStyle: { color: '#a0c8e8', fontSize: 12, fontWeight: 500 },
      itemWidth: 16,
      itemHeight: 8,
      itemGap: 24
    },
    grid: { left: 40, right: 40, top: 50, bottom: 20 },
    xAxis: { type: 'category', data: [], show: false },
    yAxis: [
      {
        type: 'value',
        min: 0,
        max: 100,
        position: 'left',
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#6b8cae', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)', type: 'dashed' } }
      },
      {
        type: 'value',
        min: 0,
        max: 100,
        position: 'right',
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#6b8cae', fontSize: 11 },
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: '电量 (%)',
        type: 'line',
        data: chartData.battery,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 3, cap: 'round', color: '#39d398' },
        areaStyle: {
          color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [{ offset: 0, color: 'rgba(57,211,152,0.35)' }, { offset: 1, color: 'rgba(57,211,152,0)' }] }
        }
      },
      {
        name: 'CPU使用率 (%)',
        type: 'line',
        data: chartData.cpu,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 3, cap: 'round', color: '#ff8d43' },
        areaStyle: {
          color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [{ offset: 0, color: 'rgba(255,141,67,0.35)' }, { offset: 1, color: 'rgba(255,141,67,0)' }] }
        }
      },
      {
        name: '温度 (℃)',
        type: 'line',
        yAxisIndex: 1,
        data: [],
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 3, cap: 'round', color: '#ff5d5d' },
        areaStyle: {
          color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [{ offset: 0, color: 'rgba(255,93,93,0.35)' }, { offset: 1, color: 'rgba(255,93,93,0)' }] }
        }
      }
    ]
  }

  systemChart.setOption(option)
}

function initDetectionPieChart() {
  if (!detectionPieChart.value) return

  detectionPie = echarts.init(detectionPieChart.value)

  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(5, 17, 29, 0.95)',
      borderColor: 'rgba(89, 214, 255, 0.2)',
      borderRadius: 12,
      padding: [12, 16],
      textStyle: { color: '#eaf5ff', fontSize: 13 },
      formatter: (params) => `<div style="font-weight:600;margin-bottom:4px;">${params.name}</div><div>数量: ${params.value}</div><div>占比: ${params.percent}%</div>`
    },
    series: [
      {
        name: '检测目标分布',
        type: 'pie',
        radius: ['55%', '75%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 0, borderColor: 'transparent', borderWidth: 0, shadowBlur: 15, shadowColor: 'rgba(89,214,255,0.3)' },
        label: { show: false },
        labelLine: { show: false },
        emphasis: { scale: true, scaleSize: 8, itemStyle: { shadowBlur: 25, shadowColor: 'rgba(89,214,255,0.5)' } },
        data: [
          { value: dashboardData.value?.cropTotalToday || 0, name: '作物', itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [{ offset: 0, color: '#39d398' }, { offset: 1, color: '#2ab88a' }] }, shadowColor: 'rgba(57,211,152,0.4)' } },
          { value: dashboardData.value?.weedTotalToday || 0, name: '杂草', itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [{ offset: 0, color: '#ff8d43' }, { offset: 1, color: '#e67a3c' }] }, shadowColor: 'rgba(255,141,67,0.4)' } }
        ]
      },
      {
        name: '中心文字',
        type: 'pie',
        radius: ['0%', '50%'],
        center: ['50%', '50%'],
        label: {
          show: true,
          position: 'center',
          formatter: () => {
            const total = (dashboardData.value?.cropTotalToday || 0) + (dashboardData.value?.weedTotalToday || 0)
            return `\n{total|${total}}\n{label|总数}`
          },
          rich: {
            total: { fontSize: 28, fontWeight: 'bold', color: '#eaf5ff', lineHeight: 36 },
            label: { fontSize: 12, color: '#6b8cae', lineHeight: 20 }
          }
        },
        labelLine: { show: false },
        data: [{ value: 1, itemStyle: { color: 'transparent' } }]
      }
    ]
  }

  detectionPie.setOption(option)
}

function updateDetectionPieChart() {
  if (isUnmounted || !detectionPie || !dashboardData.value) return
  const cropValue = dashboardData.value?.cropTotalToday || 0
  const weedValue = dashboardData.value?.weedTotalToday || 0
  const total = cropValue + weedValue
  detectionPie.setOption({
    series: [
      { data: [
        { value: cropValue, name: '作物', itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [{ offset: 0, color: '#39d398' }, { offset: 1, color: '#2ab88a' }] }, shadowColor: 'rgba(57,211,152,0.4)' } },
        { value: weedValue, name: '杂草', itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [{ offset: 0, color: '#ff8d43' }, { offset: 1, color: '#e67a3c' }] }, shadowColor: 'rgba(255,141,67,0.4)' } }
      ]},
      { label: { formatter: () => `\n{total|${total}}\n{label|总数}` } }
    ]
  })
}

function updateSystemMetricsChart() {
  if (isUnmounted || !systemChart || !currentStatus.value) return
  chartData.battery.push(currentStatus.value.battery || 0)
  chartData.cpu.push(currentStatus.value.cpuUsage || 0)
  chartData.temp.push(currentStatus.value.temperature || 0)
  if (chartData.battery.length > maxDataPoints) chartData.battery.shift()
  if (chartData.cpu.length > maxDataPoints) chartData.cpu.shift()
  if (chartData.temp.length > maxDataPoints) chartData.temp.shift()
  const xData = Array.from({ length: chartData.battery.length }, (_, i) => '' + i)
  systemChart.setOption({ xAxis: { data: xData }, series: [{ data: chartData.battery }, { data: chartData.cpu }, { data: chartData.temp }] })
}

function formatDateTimeForApi(date) {
  const pad = n => n.toString().padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

async function loadRecentHistory() {
  try {
    const endTime = new Date()
    const startTime = new Date()
    startTime.setHours(0, 0, 0, 0)
    const res = await getStatusHistory({ startTime: formatDateTimeForApi(startTime), endTime: formatDateTimeForApi(endTime), page: 1, size: 30 })
    if (res.code === 200 && res.data?.list) {
      const recentList = res.data.list.slice(-maxDataPoints)
      chartData.battery = []
      chartData.cpu = []
      chartData.temp = []
      recentList.forEach(item => {
        chartData.battery.push(item.battery || 0)
        chartData.cpu.push(item.cpuUsage || 0)
        chartData.temp.push(item.temperature || 0)
      })
      if (!isUnmounted && systemChart) {
        const xData = Array.from({ length: chartData.battery.length }, (_, i) => '' + i)
        systemChart.setOption({ xAxis: { data: xData }, series: [{ data: chartData.battery }, { data: chartData.cpu }, { data: chartData.temp }] })
      }
    }
  } catch (e) {
    console.warn('加载历史数据失败', e)
  }
}

function handleResize() {
  if (isUnmounted) return
  systemChart?.resize()
  detectionPie?.resize()
}

onMounted(async () => {
  await loadDashboardData()
  await loadLatestStatus()
  await nextTick()
  initSystemMetricsChart()
  initDetectionPieChart()
  await loadRecentHistory()
  updateSystemMetricsChart()
  updateDetectionPieChart()

  ws = getRobotStatusWs()
  ws._statusUpdateCallback = (data) => {
    if (isUnmounted) return
    currentStatus.value = data
    loadDashboardData().then(() => { updateDetectionPieChart() })
    updateSystemMetricsChart()
  }
  ws.on('STATUS_UPDATE', ws._statusUpdateCallback)
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  isUnmounted = true
  if (ws) {
    ws._statusUpdateCallback && ws.off('STATUS_UPDATE', ws._statusUpdateCallback)
    ws.close()
    ws = null
  }
  systemChart?.dispose()
  systemChart = null
  detectionPie?.dispose()
  detectionPie = null
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
/* ── 布局 ─────────────────────────────────── */
.dashboard-container {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  min-height: 100%;
}

.core-status-card {
  grid-column: span 2;
}

/* 12列虚拟网格：上4(各span3) 下3(各span4) */
.core-status-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 14px;
}

.core-status-item.span-3 { grid-column: span 3; }
.core-status-item.span-4 { grid-column: span 4; }

/* ── 面板基础 ─────────────────────────────── */
.glass-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  padding: 14px 18px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 20px;
  margin-bottom: 12px;
}

.section-title {
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 0.03em;
  color: var(--text-primary);
}

.panel-body {
  flex: 1;
  min-height: 0;
}

/* 实时角标 */
.live-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #39d398;
  font-weight: 600;
  letter-spacing: 0.04em;
}

.live-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #39d398;
  box-shadow: 0 0 0 0 rgba(57, 211, 152, 0.6);
  animation: pulse-dot 1.6s infinite;
}

@keyframes pulse-dot {
  0%   { box-shadow: 0 0 0 0 rgba(57,211,152,0.6); }
  70%  { box-shadow: 0 0 0 7px rgba(57,211,152,0); }
  100% { box-shadow: 0 0 0 0 rgba(57,211,152,0); }
}

/* ── 状态卡片 ─────────────────────────────── */
.core-status-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  border: 1px solid var(--line-soft);
  overflow: hidden;
  transition: transform 0.24s ease, box-shadow 0.24s ease, border-color 0.24s ease;
}

.core-status-item:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.28);
  border-color: var(--line-strong);
}

/* 卡片光晕背景 */
.card-glow {
  position: absolute;
  right: -20px;
  bottom: -20px;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  opacity: 0.12;
  pointer-events: none;
  filter: blur(20px);
  transition: opacity 0.24s ease;
}

.core-status-item:hover .card-glow { opacity: 0.22; }

.glow-blue   { background: #59d6ff; }
.glow-cyan   { background: #00e5ff; }
.glow-green  { background: #39d398; }
.glow-orange { background: #ff8d43; }
.glow-red    { background: #ff5d5d; }

/* ── 图标 ─────────────────────────────────── */
.core-status-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
}

.icon-blue   { background: linear-gradient(135deg, #3b82f6, #59d6ff); color: #fff; }
.icon-cyan   { background: linear-gradient(135deg, #00c8e6, #00e5ff); color: #fff; }
.icon-green  { background: linear-gradient(135deg, #28b87a, #39d398); color: #fff; }
.icon-orange { background: linear-gradient(135deg, #d4722f, #ff8d43); color: #fff; }
.icon-red    { background: linear-gradient(135deg, #d94545, #ff5d5d); color: #fff; }

.icon { width: 24px; height: 24px; }

/* ── 文本信息 ─────────────────────────────── */
.core-status-info { flex: 1; min-width: 0; }

.core-status-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 5px;
  letter-spacing: 0.02em;
}

.core-status-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.core-status-value.coord {
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.01em;
  white-space: normal;
  line-height: 1.4;
}

.unit {
  font-size: 13px;
  font-weight: 400;
  color: var(--text-secondary);
  margin-left: 2px;
}

/* ── 迷你进度条 ──────────────────────────── */
.mini-bar {
  height: 4px;
  background: rgba(255,255,255,0.07);
  border-radius: 999px;
  margin-top: 8px;
  overflow: hidden;
}

.mini-bar-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.4s ease;
}

.battery-fill { background: linear-gradient(90deg, #28b87a, #39d398); }
.cpu-fill     { background: linear-gradient(90deg, #d4722f, #ff8d43); }
.temp-fill    { background: linear-gradient(90deg, #d94545, #ff5d5d); }

/* ── 状态标签 ─────────────────────────────── */
.core-status-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.tag-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.tag-success { background: rgba(57,211,152,0.15); color: #39d398; }
.tag-success .tag-dot { background: #39d398; box-shadow: 0 0 5px #39d398; }
.tag-info    { background: rgba(89,214,255,0.15); color: #59d6ff; }
.tag-info .tag-dot    { background: #59d6ff; }

.status-running { color: #39d398; }
.status-error   { color: #ff5d5d; }
.status-idle    { color: #59d6ff; }

/* ── 作业统计 ─────────────────────────────── */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: 0;
  padding: 0;
  height: 100%;
}

.stats-item {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 16px;
  padding: 16px 20px;
  background: transparent;
  border-radius: 0;
  border: none;
  transition: background 0.24s ease;
}

.stats-item:hover {
  background: rgba(89, 214, 255, 0.06);
}

.stats-icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.icon-blue-soft   { background: rgba(59,130,246,0.15); color: #59d6ff; }
.icon-orange-soft { background: rgba(255,141,67,0.15); color: #ff8d43; }
.icon-green-soft  { background: rgba(57,211,152,0.15); color: #39d398; }
.icon-red-soft    { background: rgba(255,93,93,0.15);  color: #ff5d5d; }

.stats-info {
  display: flex;
  flex-direction: column;
  justify-content: center;
  flex: 1;
}

.stats-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.stats-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
}

.stats-unit {
  font-size: 16px;
  font-weight: 400;
  color: var(--text-secondary);
  margin-left: 6px;
}

/* ── IMU ──────────────────────────────────── */
.imu-content {
  display: flex;
  justify-content: space-between;
  align-items: stretch;
  padding: 0;
  background: transparent;
  border-radius: 0;
  border: none;
  min-height: 200px;
}

.stats-card,
.imu-card {
  min-height: 280px;
}

.no-data {
  text-align: center;
  padding: 32px;
  color: var(--text-tertiary);
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  border: 1px solid var(--line-soft);
}

/* ── 图表 ─────────────────────────────────── */
.system-chart-container {
  width: 100%;
  height: 280px;
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: 12px;
  border: 1px solid var(--line-soft);
  box-sizing: border-box;
}

/* ── 饼图分布 ─────────────────────────────── */
.detection-distribution {
  display: flex;
  gap: 20px;
  align-items: center;
  justify-content: center;
  padding-top: 30px;
}

.pie-container { flex: 1; min-width: 160px; }
.pie-chart { width: 100%; height: 220px; }

.bar-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.bar-item { display: flex; flex-direction: column; gap: 8px; }

.bar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.bar-label {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 14px;
  color: var(--text-secondary);
}

.bar-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.dot-green  { background: #39d398; box-shadow: 0 0 6px rgba(57,211,152,0.6); }
.dot-orange { background: #ff8d43; box-shadow: 0 0 6px rgba(255,141,67,0.6); }

.bar-value {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
}

.bar-progress {
  height: 8px;
  background: var(--bg-input);
  border-radius: 999px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.4s ease;
}

.bar-fill.crop-fill { background: linear-gradient(90deg, #28b87a, #39d398); }
.bar-fill.weed-fill { background: linear-gradient(90deg, #d4722f, #ff8d43); }

/* ── 响应式 ───────────────────────────────── */
@media (max-width: 1100px) {
  .core-status-item.span-3 { grid-column: span 6; }
  .core-status-item.span-4 { grid-column: span 6; }
}

@media (max-width: 768px) {
  .dashboard-container { gap: 12px; }

  .core-status-grid { grid-template-columns: repeat(2, 1fr); gap: 12px; }
  .core-status-item.span-3,
  .core-status-item.span-4 { grid-column: span 1; }

  .core-status-item { padding: 12px; }
  .core-status-icon { width: 42px; height: 42px; font-size: 20px; }
  .core-status-value { font-size: 17px; }

  .stats-grid { grid-template-columns: repeat(2, 1fr); gap: 12px; }
  .stats-item { padding: 14px; }

  .detection-distribution { flex-direction: column; gap: 16px; }
  .pie-chart { height: 180px; }
  .system-chart-container { height: 240px; }
}

@media (max-width: 480px) {
  .core-status-grid { grid-template-columns: 1fr; }
  .stats-grid { grid-template-columns: 1fr; }
  .glass-panel { padding: 14px 16px; }
}
</style>