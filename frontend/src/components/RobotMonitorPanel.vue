<template>
  <div class="robot-monitor-panel">
    <el-card shadow="hover" class="monitor-card">
      <template #header>
        <div class="card-header">
          <el-icon class="card-icon"><Monitor /></el-icon>
          <span>模拟树莓派端面板</span>
        </div>
      </template>

      <div class="panel-content">
        <!-- 指令相关功能 -->
        <div class="panel-section command-section">
          <h3 class="section-title">
            <el-icon><Operation /></el-icon>
            指令执行流程
          </h3>
          <el-table :data="commandList" style="width: 100%" size="small">
            <el-table-column prop="commandId" label="ID" width="120" />
            <el-table-column prop="action" label="动作" width="120" />
            <el-table-column prop="result" label="运行结果" width="100" align="center">
              <template #default="scope">
                <span :class="{ 'success-text': scope.row.result === 'SUCCESS', 'error-text': scope.row.result === 'FAILED', 'info-text': !scope.row.result }">
                  {{ scope.row.result || '待执行' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="laserReported" label="是否上报" width="100" align="center">
              <template #default="scope">
                <span :class="{ 'success-text': scope.row.laserReported, 'info-text': !scope.row.laserReported }">
                  {{ scope.row.laserReported ? '已上报' : '未上报' }}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 上报状态 -->
        <div class="panel-section report-section">
          <h3 class="section-title">
            <el-icon><DataAnalysis /></el-icon>
            上报状态
          </h3>
          <div class="report-list">
            <div 
              v-for="(report, index) in reportList" 
              :key="index" 
              class="report-item"
              :class="{ 'reported': report.status === '已上报' }"
            >
              <div class="report-time">{{ report.time }}</div>
              <div class="report-content">
                {{ report.message }}
                <span v-if="report.details" class="report-details">{{ report.details }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 运行日志流 -->
        <div class="panel-section logs-panel">
          <h3 class="section-title">
            <el-icon><Reading /></el-icon>
            运行日志
          </h3>
          <div class="logs-container" ref="logsContainer">
            <div 
              v-for="(log, index) in logs" 
              :key="index" 
              class="log-item" 
              :class="`log-${log.level.toLowerCase()}`"
            >
              <span class="log-time">{{ log.time }}</span>
              <span class="log-level">{{ log.level }}</span>
              <span class="log-message">{{ log.message }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { 
  Monitor, DataAnalysis, RefreshRight, 
  Warning, Search, Operation, Reading, Check, Timer 
} from '@element-plus/icons-vue'
import { getRobotStatusWs } from '../utils/websocket'

// 响应式数据
const commandList = ref(JSON.parse(localStorage.getItem('commandList') || '[]')) // 指令列表
// 初始化时限制数量
if (commandList.value.length > 3) {
  commandList.value = commandList.value.slice(0, 3)
  // 保存到 localStorage
  localStorage.setItem('commandList', JSON.stringify(commandList.value))
}
const lastDetection = ref(JSON.parse(localStorage.getItem('lastDetection') || 'null')) // 最新检测结果
const lastDetectionTime = ref(localStorage.getItem('lastDetectionTime') || null) // 最后检测上报时间
const lastStatus = ref(JSON.parse(localStorage.getItem('lastStatus') || 'null')) // 最新状态
const lastStatusTime = ref(localStorage.getItem('lastStatusTime') || null) // 最后状态上报时间
const reportList = ref(JSON.parse(localStorage.getItem('reportList') || '[]')) // 上报状态历史
const logs = ref(JSON.parse(localStorage.getItem('logs') || '[]')) // 运行日志
const logsContainer = ref(null)

// WebSocket 实例
let ws = null

// 方法
const addLog = (level, message) => {
  const now = new Date()
  const time = now.toLocaleTimeString()
  logs.value.unshift({ level, message, time })
  if (logs.value.length > 3) {
    logs.value = logs.value.slice(0, 3)
  }
  // 保存到 localStorage
  localStorage.setItem('logs', JSON.stringify(logs.value))
  // 滚动到顶部
  nextTick(() => {
    if (logsContainer.value) {
      logsContainer.value.scrollTop = 0
    }
  })
}

const handleStatusUpdate = (data) => {
  lastStatus.value = data
  lastStatusTime.value = new Date().toLocaleTimeString()
  // 保存到 localStorage
  localStorage.setItem('lastStatus', JSON.stringify(data))
  localStorage.setItem('lastStatusTime', lastStatusTime.value)
  
  // 添加到上报状态历史
  const report = {
    time: lastStatusTime.value,
    status: '已上报',
    message: '机器人运行状态已上报',
    details: `电量: ${data.battery}%, 温度: ${data.temperature}°C`
  }
  reportList.value.unshift(report)
  // 限制上报状态数量
  if (reportList.value.length > 3) {
    reportList.value = reportList.value.slice(0, 3)
  }
  // 保存到 localStorage
  localStorage.setItem('reportList', JSON.stringify(reportList.value))
  
  addLog('INFO', '机器人状态已上报')
}

const handleCommandFeedback = (data) => {
  // 查找对应的指令并更新执行结果
  const index = commandList.value.findIndex(cmd => cmd.commandId === data.commandId)
  if (index !== -1) {
    commandList.value[index].result = data.result
    commandList.value[index].message = data.message
  } else {
    // 如果找不到对应指令，添加新指令
    commandList.value.unshift({
      commandId: data.commandId,
      action: data.action,
      result: data.result,
      message: data.message,
      laserReported: false
    })
  }
  // 限制指令数量
  if (commandList.value.length > 3) {
    commandList.value = commandList.value.slice(0, 3)
  }
  // 保存到 localStorage
  localStorage.setItem('commandList', JSON.stringify(commandList.value))
  addLog('INFO', `指令执行: ${data.action} - ${data.result}`)
}

const handleDetectionResult = (data) => {
  lastDetection.value = data
  lastDetectionTime.value = new Date().toLocaleTimeString()
  // 保存到 localStorage
  localStorage.setItem('lastDetection', JSON.stringify(data))
  localStorage.setItem('lastDetectionTime', lastDetectionTime.value)
  
  // 添加到上报状态历史
  const report = {
    time: lastDetectionTime.value,
    status: '已上报',
    message: '检测结果与图像已上报',
    details: `杂草: ${data.weedCount}, 作物: ${data.cropCount}`
  }
  reportList.value.unshift(report)
  // 限制上报状态数量
  if (reportList.value.length > 3) {
    reportList.value = reportList.value.slice(0, 3)
  }
  // 保存到 localStorage
  localStorage.setItem('reportList', JSON.stringify(reportList.value))
  
  addLog('INFO', `检测结果已上报: 杂草 ${data.weedCount}, 作物 ${data.cropCount}`)
}

const handleLaserFeedback = (data) => {
  // 详细日志
  addLog('DEBUG', `收到激光反馈数据: ${JSON.stringify(data)}`)
  
  // 查找对应的指令并更新激光上报状态
  const index = commandList.value.findIndex(cmd => cmd.commandId === data.commandId)
  addLog('DEBUG', `查找指令结果: 索引=${index}, 指令列表=${JSON.stringify(commandList.value.map(cmd => cmd.commandId))}`)
  
  if (index !== -1) {
    commandList.value[index].laserReported = true
    commandList.value[index].laserMessage = data.message
    // 保存到 localStorage
    localStorage.setItem('commandList', JSON.stringify(commandList.value))
    addLog('DEBUG', `更新指令激光上报状态: ${data.commandId} -> 已上报`)
  } else {
    // 如果找不到对应指令，记录日志
    addLog('WARNING', `收到激光反馈但找不到对应指令: ${data.commandId}`)
  }
  addLog('INFO', `激光反馈: ${data.message}`)
}

const handleNewCommand = (data) => {
  // 添加新指令到列表
  commandList.value.unshift({
    commandId: data.commandId,
    action: data.action,
    result: null,
    message: null,
    laserReported: false
  })
  // 限制指令数量
  if (commandList.value.length > 3) {
    commandList.value = commandList.value.slice(0, 3)
  }
  // 保存到 localStorage
  localStorage.setItem('commandList', JSON.stringify(commandList.value))
  addLog('INFO', `收到新指令: ${data.action}`)
}

// 生命周期
onMounted(() => {
  // 初始化 WebSocket 连接
  ws = getRobotStatusWs()
  
  // 注册事件监听
  ws.on('STATUS_UPDATE', handleStatusUpdate)
  ws.on('COMMAND_FEEDBACK', handleCommandFeedback)
  ws.on('DETECTION_RESULT', handleDetectionResult)
  ws.on('LASER_FEEDBACK', handleLaserFeedback)
  ws.on('NEW_COMMAND', handleNewCommand)
  
  // 添加初始日志
  addLog('INFO', '树莓派端面板已启动')
  addLog('INFO', '正在连接 WebSocket...')
})

onUnmounted(() => {
  // 清理事件监听
  if (ws) {
    ws.off('STATUS_UPDATE', handleStatusUpdate)
    ws.off('COMMAND_FEEDBACK', handleCommandFeedback)
    ws.off('DETECTION_RESULT', handleDetectionResult)
    ws.off('LASER_FEEDBACK', handleLaserFeedback)
    ws.off('NEW_COMMAND', handleNewCommand)
  }
})
</script>

<style scoped>
.robot-monitor-panel {
  width: 100%;
}

.monitor-card {
  width: 100%;
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
  align-items: center;
  gap: 8px;
  font-weight: 500;
  font-size: 17px;
  color: var(--text-primary);
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  letter-spacing: -0.2px;
  font-family: var(--font-family);
}

.card-icon {
  font-size: 20px;
  color: var(--primary-color);
}

.panel-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-top: 20px;
}

.panel-section {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  margin: 0 0 16px 0;
  color: var(--text-primary);
  font-family: var(--font-family);
}

/* 指令执行流程 */
.command-flow {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.command-step {
  flex: 1;
  min-width: 200px;
  background: rgba(255, 255, 255, 0.05);
  padding: 12px;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  border-left: 4px solid var(--primary-color);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.step-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 8px;
  font-family: var(--font-family);
}

.step-content {
  font-size: 12px;
  color: var(--text-secondary);
  font-family: var(--font-family);
}

.command-info {
  color: var(--primary-color);
  font-weight: 500;
}

.command-result {
  font-weight: 500;
  padding: 2px 6px;
  border-radius: 3px;
}

.command-result.success {
  color: var(--success-color);
  background: rgba(103, 194, 58, 0.1);
}

.command-result.error {
  color: var(--error-color);
  background: rgba(245, 108, 108, 0.1);
}

.feedback-info {
  color: var(--warning-color);
  font-weight: 500;
}

.no-data {
  color: var(--text-tertiary);
  font-style: italic;
}

/* 上报状态 */
.report-list {
  max-height: 200px;
  overflow-y: auto;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.report-item {
  display: flex;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.report-item:last-child {
  border-bottom: none;
}

.report-item.reported .report-content {
  color: var(--success-color);
  font-weight: 500;
}

.report-time {
  min-width: 80px;
  font-size: 11px;
  color: var(--text-tertiary);
  font-style: italic;
  display: flex;
  align-items: center;
  font-family: var(--font-family);
}

.report-content {
  flex: 1;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.4;
  font-family: var(--font-family);
}

.report-details {
  display: block;
  font-size: 11px;
  color: var(--text-tertiary);
  margin-top: 2px;
  margin-left: 0;
  font-family: var(--font-family);
}

.success-text {
  color: var(--success-color);
  font-weight: 500;
}

.error-text {
  color: var(--error-color);
  font-weight: 500;
}

.info-text {
  color: var(--primary-color);
  font-weight: 500;
}

/* 日志面板 */
.logs-container {
  max-height: 200px;
  overflow-y: auto;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.log-item {
  display: flex;
  gap: 12px;
  font-size: 12px;
  margin-bottom: 8px;
  line-height: 1.4;
  font-family: var(--font-family);
}

.log-time {
  color: var(--text-tertiary);
  min-width: 80px;
}

.log-level {
  min-width: 60px;
  font-weight: 500;
}

.log-info .log-level {
  color: var(--primary-color);
}

.log-error .log-level {
  color: var(--error-color);
}

.log-warning .log-level {
  color: var(--warning-color);
}

.log-message {
  flex: 1;
  word-break: break-word;
  color: var(--text-secondary);
}

/* 响应式调整 */
@media (max-width: 768px) {
  .command-flow {
    flex-direction: column;
  }
  
  .command-step {
    min-width: 100%;
  }
  
  .report-status {
    flex-direction: column;
  }
  
  .report-item {
    min-width: 100%;
  }
}
</style>