<template>
  <div class="dashboard-container">
    <!-- 板块 1：顶部【核心实时状态横幅】 -->
    <div class="core-status-card glass-panel">
      <div class="card-header">
        <span class="header-title">核心实时状态</span>
      </div>
      <div class="core-status-grid">
        <div class="core-status-item status">
          <div class="core-status-icon">
            <el-icon class="icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 3 2 7.48 2 13s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.94-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg></el-icon>
          </div>
          <div class="core-status-info">
            <div class="core-status-label">机器人状态</div>
            <div class="core-status-value" :class="getStatusClass()">{{ dashboardData?.robotStatusText || '未知' }}</div>
          </div>
        </div>
        
        <div class="core-status-item speed">
          <div class="core-status-icon">
            <el-icon class="icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M18.92 6.01C18.72 5.42 18.16 5 17.5 5h-11c-.66 0-1.21.42-1.42 1.01L3 12v8c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1h12v1c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-8l-2.08-5.99zM6.5 16c-.83 0-1.5-.67-1.5-1.5S5.67 13 6.5 13s1.5.67 1.5 1.5S7.33 16 6.5 16zm11 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zM5 11l1.5-4.5h11L19 11H5z"/></svg></el-icon>
          </div>
          <div class="core-status-info">
            <div class="core-status-label">推行速度</div>
            <div class="core-status-value">{{ currentStatus?.speed || 0 }} m/s</div>
          </div>
        </div>
        
        <div class="core-status-item gps">
          <div class="core-status-icon">
            <el-icon class="icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg></el-icon>
          </div>
          <div class="core-status-info">
            <div class="core-status-label">坐标</div>
            <div class="core-status-value">{{ formatCoordinate(currentStatus?.latitude) }}, {{ formatCoordinate(currentStatus?.longitude) }}</div>
          </div>
        </div>
        
        <div class="core-status-item laser">
          <div class="core-status-icon">
            <el-icon class="icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M13 10h-2v4h2v-4zm-1-7C6.48 3 2 7.48 2 13s4.48 10 10 10 10-4.48 10-10S17.52 3 12 3zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v2h-2V8z"/></svg></el-icon>
          </div>
          <div class="core-status-info">
            <div class="core-status-label">激光设备</div>
            <div class="core-status-value">
              <el-tag :type="currentStatus?.laserOn ? 'success' : 'info'" class="core-status-tag">
                {{ currentStatus?.laserOn ? '已开启' : '已关闭' }}
              </el-tag>
            </div>
          </div>
        </div>
        
        <div class="core-status-item battery">
          <div class="core-status-icon">
            <el-icon class="icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M16 18H8V6h8v12zm0-14H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2z"/></svg></el-icon>
          </div>
          <div class="core-status-info">
            <div class="core-status-label">电池电量</div>
            <div class="core-status-value">{{ currentStatus?.battery || 0 }}%</div>
          </div>
        </div>
        
        <div class="core-status-item cpu">
          <div class="core-status-icon">
            <el-icon class="icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M4 5C4 3.34 5.34 2 7 2h10c1.66 0 3 1.34 3 3v14c0 1.66-1.34 3-3 3H7c-1.66 0-3-1.34-3-3V5zm16 0v14c0 .55-.45 1-1 1H7c-.55 0-1-.45-1-1V5c0-.55.45-1 1-1h10c.55 0 1 .45 1 1zm-3 9h-2v2h2v-2zm-4 0h-2v2h2v-2zm-4 0h-2v2h2v-2z"/></svg></el-icon>
          </div>
          <div class="core-status-info">
            <div class="core-status-label">CPU使用率</div>
            <div class="core-status-value">{{ currentStatus?.cpuUsage || 0 }}%</div>
          </div>
        </div>
        
        <div class="core-status-item temp">
          <div class="core-status-icon">
            <el-icon class="icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M15 13V5a3 3 0 0 0-6 0v8a5 5 0 1 0 6 0z"/></svg></el-icon>
          </div>
          <div class="core-status-info">
            <div class="core-status-label">机身温度</div>
            <div class="core-status-value">{{ currentStatus?.temperature || 0 }}℃</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 板块 2：中上【今日作业统计区】 -->
    <el-row :gutter="24" class="content-row">
      <!-- 左侧：数据大盘指标卡片 -->
      <el-col :span="12">
        <div class="stats-card glass-panel">
          <div class="card-header">
            <span class="header-title">今日作业统计</span>
          </div>
          <div class="stats-grid">
            <div class="stats-item total">
              <div class="stats-info">
                <div class="stats-label">今日总检测次数</div>
                <div class="stats-value">{{ dashboardData?.detectCountToday || 0 }}</div>
              </div>
            </div>
            
            <div class="stats-item weed">
              <div class="stats-info">
                <div class="stats-label">杂草清除总量</div>
                <div class="stats-value">{{ dashboardData?.weedTotalToday || 0 }}</div>
              </div>
            </div>
            
            <div class="stats-item crop">
              <div class="stats-info">
                <div class="stats-label">作物识别总量</div>
                <div class="stats-value">{{ dashboardData?.cropTotalToday || 0 }}</div>
              </div>
            </div>
            
            <div class="stats-item laser">
              <div class="stats-info">
                <div class="stats-label">今日激光作业次数</div>
                <div class="stats-value">{{ dashboardData?.laserFireToday || 0 }}次</div>
              </div>
            </div>
          </div>
        </div>
      </el-col>

      <!-- 右侧：IMU 姿态专属区域 -->
      <el-col :span="12">
        <div class="imu-card glass-panel">
          <div class="card-header">
            <span class="header-title">姿态 IMU</span>
          </div>
          <div class="imu-content" v-if="currentStatus?.imu">
            <ImuAttitudeViewer :imu="currentStatus.imu" />
          </div>
          <div v-else class="no-imu-data">
            暂无 IMU 数据
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 板块 3：底部【图表区域】 -->
    <el-row :gutter="24" class="content-row">
      <!-- 左侧：系统参数趋势折线图 -->
      <el-col :span="12">
        <div class="device-params-card glass-panel">
          <div class="card-header">
            <span class="header-title">设备运行参数</span>
          </div>
          <div ref="systemMetricsChart" class="systemChart-container"></div>
          <!-- 当前数值卡片 -->
          <div class="current-values">
            <div class="value-card battery">
              <div class="value-label">电量</div>
              <div class="value-number">{{ currentStatus?.battery || 0 }}%</div>
            </div>
            <div class="value-card cpu">
              <div class="value-label">CPU使用率</div>
              <div class="value-number">{{ currentStatus?.cpuUsage || 0 }}%</div>
            </div>
            <div class="value-card temp">
              <div class="value-label">机身温度</div>
              <div class="value-number">{{ currentStatus?.temperature || 0 }}℃</div>
            </div>
          </div>
        </div>
      </el-col>

      <!-- 右侧：今日检测分布饼图 -->
      <el-col :span="12">
        <div class="chart-card glass-panel">
          <div class="card-header">
            <span class="header-title">今日检测目标分布</span>
          </div>
          <div class="detection-distribution">
            <div class="pie-container">
              <div ref="detectionPieChart" class="pie-chart"></div>
            </div>
            <div class="bar-container">
              <div class="bar-item crop">
                <div class="bar-label">作物</div>
                <div class="bar-value">{{ dashboardData?.cropTotalToday || 0 }}</div>
                <div class="bar-progress">
                  <div class="bar-fill crop-fill" :style="{ width: getCropPercentage() + '%' }"></div>
                </div>
              </div>
              <div class="bar-item weed">
                <div class="bar-label">杂草</div>
                <div class="bar-value">{{ dashboardData?.weedTotalToday || 0 }}</div>
                <div class="bar-progress">
                  <div class="bar-fill weed-fill" :style="{ width: getWeedPercentage() + '%' }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { Calendar } from '@element-plus/icons-vue'
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
let lastUpdateTime = 0
const maxDataPoints = 50
let ws = null
let isUnmounted = false
// 存储图表数据，不依赖chart实例
const chartData = {
  battery: [],
  cpu: [],
  temp: []
}

function goToStatusHistory() {
  router.push('/status')
}

function formatCoordinate(val) {
  if (val == null) return '-'
  return Number(val).toFixed(6)
}

// 计算作物和杂草的百分比
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

// 根据机器人状态返回对应的样式类
function getStatusClass() {
  const status = dashboardData.value?.robotStatusText || ''
  if (status.includes('运行')) {
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

// 初始化系统参数折线图
function initSystemMetricsChart() {
  if (!systemMetricsChart.value) return

  systemChart = echarts.init(systemMetricsChart.value)

  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderRadius: 12,
      shadowBlur: 10,
      shadowColor: 'rgba(0, 0, 0, 0.1)'
    },
    legend: {
      data: ['电量 (%)', 'CPU使用率 (%)', '温度 (℃)'],
      top: 8,
      textStyle: {
        fontSize: 13
      }
    },
    grid: {
      left: 60,
      right: 16,
      top: 44,
      bottom: 12
    },
    xAxis: {
      type: 'category',
      data: [],
      show: false
    },
    yAxis: [
      {
        type: 'value',
        name: '电量/CPU (%)',
        min: 0,
        max: 100,
        position: 'left',
        nameTextStyle: {
          fontSize: 12
        }
      },
      {
        type: 'value',
        name: '温度 (℃)',
        min: 0,
        max: 100,
        position: 'right',
        nameTextStyle: {
          fontSize: 12
        }
      }
    ],
    series: [
      {
        name: '电量 (%)',
        type: 'line',
        data: [],
        smooth: true,
        lineStyle: {
          width: 2,
          cap: 'round'
        },
        itemStyle: {
          color: '#67c23a'
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [{
              offset: 0, color: 'rgba(103, 194, 58, 0.3)'
            }, {
              offset: 1, color: 'rgba(103, 194, 58, 0.0)'
            }]
          }
        }
      },
      {
        name: 'CPU使用率 (%)',
        type: 'line',
        data: [],
        smooth: true,
        lineStyle: {
          width: 2,
          cap: 'round'
        },
        itemStyle: {
          color: '#e6a23c'
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [{
              offset: 0, color: 'rgba(230, 162, 60, 0.3)'
            }, {
              offset: 1, color: 'rgba(230, 162, 60, 0.0)'
            }]
          }
        }
      },
      {
        name: '温度 (℃)',
        type: 'line',
        yAxisIndex: 1,
        data: [],
        smooth: true,
        lineStyle: {
          width: 2,
          cap: 'round'
        },
        itemStyle: {
          color: '#f56c6c'
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [{
              offset: 0, color: 'rgba(245, 108, 108, 0.3)'
            }, {
              offset: 1, color: 'rgba(245, 108, 108, 0.0)'
            }]
          }
        }
      }
    ]
  }

  systemChart.setOption(option)
}

// 初始化今日检测分布饼图
function initDetectionPieChart() {
  if (!detectionPieChart.value) return

  detectionPie = echarts.init(detectionPieChart.value)

  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderRadius: 12,
      shadowBlur: 10,
      shadowColor: 'rgba(0, 0, 0, 0.1)'
    },
    legend: {
      orient: 'horizontal',
      bottom: 10,
      textStyle: {
        fontSize: 13
      }
    },
    series: [
      {
        name: '检测目标分布',
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['50%', '45%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}: {d}%',
          fontSize: 14
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold',
            formatter: '{b}: {d}%'
          }
        },
        data: [
          { value: dashboardData.value?.cropTotalToday || 0, name: '作物', itemStyle: { color: 'var(--primary-color)' } },
          { value: dashboardData.value?.weedTotalToday || 0, name: '杂草', itemStyle: { color: 'var(--info-color)' } }
        ]
      }
    ]
  }

  detectionPie.setOption(option)
}

// 更新检测饼图数据
function updateDetectionPieChart() {
  if (isUnmounted || !detectionPie || !dashboardData.value) return

  detectionPie.setOption({
    series: [{
      data: [
        { value: dashboardData.value?.cropTotalToday || 0, name: '作物' },
        { value: dashboardData.value?.weedTotalToday || 0, name: '杂草' }
      ]
    }]
  })
}

// 更新系统参数图表数据
function updateSystemMetricsChart() {
  if (isUnmounted || !systemChart || !currentStatus.value) return

  // 添加新数据到本地存储
  chartData.battery.push(currentStatus.value.battery || 0)
  chartData.cpu.push(currentStatus.value.cpuUsage || 0)
  chartData.temp.push(currentStatus.value.temperature || 0)

  // 限制数据点数量
  if (chartData.battery.length > maxDataPoints) chartData.battery.shift()
  if (chartData.cpu.length > maxDataPoints) chartData.cpu.shift()
  if (chartData.temp.length > maxDataPoints) chartData.temp.shift()

  // 更新x轴
  const xData = Array.from({ length: chartData.battery.length }, (_, i) => '' + i)

  systemChart.setOption({
    xAxis: { data: xData },
    series: [
      { data: chartData.battery },
      { data: chartData.cpu },
      { data: chartData.temp }
    ]
  })
}

// 格式化时间为后端需要的格式 yyyy-MM-dd HH:mm:ss
function formatDateTimeForApi(date) {
  const pad = n => n.toString().padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

// 加载最近历史数据填充图表
async function loadRecentHistory() {
  try {
    // 获取最近 2 小时内的数据
    const endTime = new Date()
    const startTime = new Date(endTime.getTime() - 2 * 60 * 60 * 1000)
    const params = {
      startTime: formatDateTimeForApi(startTime),
      endTime: formatDateTimeForApi(endTime),
      page: 1,
      size: 30
    }
    const res = await getStatusHistory(params)
    if (res.code === 200 && res.data?.list) {
      // 取最新的若干个点填充图表
      const recentList = res.data.list.slice(-maxDataPoints)

      // 重置并填充数据到本地存储
      chartData.battery = []
      chartData.cpu = []
      chartData.temp = []

      recentList.forEach(item => {
        chartData.battery.push(item.battery || 0)
        chartData.cpu.push(item.cpuUsage || 0)
        chartData.temp.push(item.temperature || 0)
      })

      // 更新图表
      if (!isUnmounted && systemChart) {
        const xData = Array.from({ length: chartData.battery.length }, (_, i) => '' + i)
        systemChart.setOption({
          xAxis: { data: xData },
          series: [
            { data: chartData.battery },
            { data: chartData.cpu },
            { data: chartData.temp }
          ]
        })
      }
    }
  } catch (e) {
    console.warn('加载历史数据失败', e)
  }
}

function handleResize() {
  if (isUnmounted) return
  if (systemChart) {
    systemChart.resize()
  }
  if (detectionPie) {
    detectionPie.resize()
  }
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

  // 连接WebSocket接收实时更新
  ws = getRobotStatusWs()
  // 保存回调引用以便后续移除
  ws._statusUpdateCallback = (data) => {
    if (isUnmounted) return
    currentStatus.value = data
    // 刷新仪表盘统计
    loadDashboardData().then(() => {
      updateDetectionPieChart()
    })
    // 更新折线图
    updateSystemMetricsChart()
  }
  ws.on('STATUS_UPDATE', ws._statusUpdateCallback)

  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  isUnmounted = true

  if (ws) {
    // 移除监听器
    if (ws._statusUpdateCallback) {
      ws.off('STATUS_UPDATE', ws._statusUpdateCallback)
    }
    ws.close()
    ws = null
  }

  if (systemChart) {
    systemChart.dispose()
    systemChart = null
  }

  if (detectionPie) {
    detectionPie.dispose()
    detectionPie = null
  }

  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.dashboard-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
  min-height: 100vh;
  background: var(--app-background);
}

.core-status-card,
.stats-card,
.chart-card,
.device-params-card,
.imu-card {
  border-radius: 16px;
  padding: 20px;
  overflow: hidden;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  align-items: center;
  font-weight: 500;
  font-size: 17px;
  color: var(--text-primary);
  justify-content: space-between;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.header-title {
  letter-spacing: -0.2px;
  font-family: var(--font-family);
}

/* 核心实时状态 */
.core-status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  margin-top: 10px;
}

.core-status-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.core-status-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  border-color: rgba(255, 255, 255, 0.1);
}

.core-status-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.core-status-item.speed .core-status-icon {
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-light) 100%);
  color: white;
}

.core-status-item.laser .core-status-icon {
  background: linear-gradient(135deg, var(--success-color) 0%, var(--success-light) 100%);
  color: white;
}

.core-status-item.battery .core-status-icon {
  background: linear-gradient(135deg, var(--success-color) 0%, var(--success-light) 100%);
  color: white;
}

.core-status-item.cpu .core-status-icon {
  background: linear-gradient(135deg, var(--warning-color) 0%, var(--warning-light) 100%);
  color: white;
}

.core-status-item.temp .core-status-icon {
  background: linear-gradient(135deg, var(--error-color) 0%, var(--error-light) 100%);
  color: white;
}

.core-status-item.gps .core-status-icon {
  background: linear-gradient(135deg, var(--info-color) 0%, var(--info-light) 100%);
  color: white;
}

.core-status-item.status .core-status-icon {
  background: linear-gradient(135deg, var(--info-color) 0%, var(--info-light) 100%);
  color: white;
}

.core-status-info {
  flex: 1;
}

.core-status-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  font-family: var(--font-family);
}

.core-status-value {
  font-size: 20px;
  color: var(--text-primary);
  font-weight: 600;
  font-family: var(--font-family);
}

.core-status-tag {
  font-size: 14px;
  padding: 4px 16px;
  border-radius: 16px;
  font-family: var(--font-family);
}

/* 状态颜色 */
.status-running {
  color: var(--success-color);
}

.status-error {
  color: var(--error-color);
}

.status-idle {
  color: var(--primary-color);
}

/* 作业统计 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-top: 10px;
  min-height: 200px;
}

.stats-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 20px 16px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  height: 100px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.stats-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  border-color: rgba(255, 255, 255, 0.1);
}

.stats-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.stats-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  font-family: var(--font-family);
}

.stats-value {
  font-size: 28px;
  font-weight: 600;
  color: var(--text-primary);
  font-family: var(--font-family);
}

/* 设备运行参数 */
.current-values {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.value-card {
  padding: 20px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  text-align: center;
  border: 1px solid rgba(255, 255, 255, 0.05);
  transition: all 0.3s ease;
}

.value-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  border-color: rgba(255, 255, 255, 0.1);
}

.value-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 12px;
  font-family: var(--font-family);
}

.value-number {
  font-size: 28px;
  font-weight: 600;
  color: var(--text-primary);
  font-family: var(--font-family);
}

/* 检测分布 */
.detection-distribution {
  display: flex;
  gap: 24px;
  align-items: center;
  margin-top: 10px;
}

.pie-container {
  flex: 1;
  min-width: 180px;
}

.pie-chart {
  width: 100%;
  height: 240px;
}

.bar-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.bar-item {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.bar-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  font-family: var(--font-family);
}

.bar-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  font-family: var(--font-family);
}

.bar-progress {
  height: 10px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
}

.bar-fill {
  height: 100%;
  border-radius: 8px;
  transition: width 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.bar-fill.crop-fill {
  background: linear-gradient(135deg, var(--success-color) 0%, var(--success-light) 100%);
}

.bar-fill.weed-fill {
  background: linear-gradient(135deg, var(--error-color) 0%, var(--error-light) 100%);
}

/* IMU 姿态 */
.imu-content {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 16px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.05);
  max-height: 200px;
}

.no-imu-data {
  text-align: center;
  padding: 32px 24px;
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  font-family: var(--font-family);
  max-height: 200px;
}

/* 通用样式 */
.icon {
  width: 28px;
  height: 28px;
}

.content-row {
  margin-top: 0;
}

.systemChart-container {
  width: 100%;
  height: 320px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 12px;
  box-sizing: border-box;
  margin-top: 10px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

/* 响应式调整 */
@media (max-width: 768px) {
  .dashboard-container {
    padding: 16px;
  }
  
  .core-status-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }
  
  .core-status-item {
    padding: 16px;
  }
  
  .core-status-icon {
    width: 48px;
    height: 48px;
    font-size: 24px;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }
  
  .stats-item {
    padding: 20px 16px;
    height: 120px;
  }
  
  .detection-distribution {
    flex-direction: column;
    gap: 20px;
  }
  
  .pie-chart {
    height: 200px;
  }
  
  .systemChart-container {
    height: 280px;
  }
  
  .current-values {
    gap: 16px;
  }
}

@media (max-width: 480px) {
  .core-status-grid {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .current-values {
    grid-template-columns: 1fr;
  }
  
  .core-status-card,
  .stats-card,
  .chart-card,
  .device-params-card,
  .imu-card {
    padding: 16px;
  }
}
</style>
