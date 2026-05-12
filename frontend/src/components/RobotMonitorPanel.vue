<template>
  <section class="glass-panel robot-monitor-panel">
    <div class="panel-header">
      <div class="card-header">
        <el-icon class="card-icon"><Monitor /></el-icon>
        <span class="section-title">模拟树莓派端面板</span>
      </div>
    </div>

    <div class="panel-body scrollable">
      <div class="panel-content">
        <div class="panel-section command-section">
          <h3 class="section-title">
            <el-icon><Operation /></el-icon>
            指令执行流程
          </h3>
          <el-table :data="commandList" style="width: 100%" size="small" :show-header="true" :fit="true">
            <el-table-column prop="commandId" label="ID" width="125" show-overflow-tooltip />
            <el-table-column prop="action" label="动作" width="87" />
            <el-table-column prop="result" label="结果" width="68" align="center">
              <template #default="scope">
                <span :class="{ 'success-text': scope.row.result === 'SUCCESS', 'error-text': scope.row.result === 'FAILED', 'info-text': !scope.row.result }">
                  {{ scope.row.result || '待执行' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="laserReported" label="上报" width="60" align="center">
              <template #default="scope">
                <span :class="{ 'success-text': scope.row.laserReported, 'info-text': !scope.row.laserReported }">
                  {{ scope.row.laserReported ? '已上报' : '未上报' }}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </div>

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
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { 
  Monitor, DataAnalysis, Operation, Reading 
} from '@element-plus/icons-vue'
import { getRobotStatusWs } from '../utils/websocket'

const commandList = ref(JSON.parse(localStorage.getItem('commandList') || '[]'))
if (commandList.value.length > 3) {
  commandList.value = commandList.value.slice(0, 3)
  localStorage.setItem('commandList', JSON.stringify(commandList.value))
}
const reportList = ref(JSON.parse(localStorage.getItem('reportList') || '[]'))
const logs = ref(JSON.parse(localStorage.getItem('logs') || '[]'))
const logsContainer = ref(null)

let ws = null

const addLog = (level, message) => {
  const now = new Date()
  const time = now.toLocaleTimeString()
  logs.value.unshift({ level, message, time })
  if (logs.value.length > 3) {
    logs.value = logs.value.slice(0, 3)
  }
  localStorage.setItem('logs', JSON.stringify(logs.value))
  nextTick(() => {
    if (logsContainer.value) {
      logsContainer.value.scrollTop = 0
    }
  })
}

const handleStatusUpdate = (data) => {
  const report = {
    time: new Date().toLocaleTimeString(),
    status: '已上报',
    message: '机器人运行状态已上报',
    details: `电量: ${data.battery}%, 温度: ${data.temperature}°C`
  }
  reportList.value.unshift(report)
  if (reportList.value.length > 3) {
    reportList.value = reportList.value.slice(0, 3)
  }
  localStorage.setItem('reportList', JSON.stringify(reportList.value))
  addLog('INFO', '机器人状态已上报')
}

const handleCommandFeedback = (data) => {
  const index = commandList.value.findIndex(cmd => cmd.commandId === data.commandId)
  if (index !== -1) {
    commandList.value[index].result = data.result
    commandList.value[index].message = data.message
  } else {
    commandList.value.unshift({
      commandId: data.commandId,
      action: data.action,
      result: data.result,
      message: data.message,
      laserReported: false
    })
  }
  if (commandList.value.length > 3) {
    commandList.value = commandList.value.slice(0, 3)
  }
  localStorage.setItem('commandList', JSON.stringify(commandList.value))
  addLog('INFO', `指令执行: ${data.action} - ${data.result}`)
}

const handleDetectionResult = (data) => {
  const report = {
    time: new Date().toLocaleTimeString(),
    status: '已上报',
    message: '检测结果与图像已上报',
    details: `杂草: ${data.weedCount}, 作物: ${data.cropCount}`
  }
  reportList.value.unshift(report)
  if (reportList.value.length > 3) {
    reportList.value = reportList.value.slice(0, 3)
  }
  localStorage.setItem('reportList', JSON.stringify(reportList.value))
  addLog('INFO', `检测结果已上报: 杂草 ${data.weedCount}, 作物 ${data.cropCount}`)
}

const handleLaserFeedback = (data) => {
  addLog('DEBUG', `收到激光反馈数据: ${JSON.stringify(data)}`)
  const index = commandList.value.findIndex(cmd => cmd.commandId === data.commandId)
  if (index !== -1) {
    commandList.value[index].laserReported = true
    commandList.value[index].laserMessage = data.message
    localStorage.setItem('commandList', JSON.stringify(commandList.value))
    addLog('DEBUG', `更新指令激光上报状态: ${data.commandId} -> 已上报`)
  } else {
    addLog('WARNING', `收到激光反馈但找不到对应指令: ${data.commandId}`)
  }
  addLog('INFO', `激光反馈: ${data.message}`)
}

const handleNewCommand = (data) => {
  commandList.value.unshift({
    commandId: data.commandId,
    action: data.action,
    result: null,
    message: null,
    laserReported: false
  })
  if (commandList.value.length > 3) {
    commandList.value = commandList.value.slice(0, 3)
  }
  localStorage.setItem('commandList', JSON.stringify(commandList.value))
  addLog('INFO', `收到新指令: ${data.action}`)
}

onMounted(() => {
  ws = getRobotStatusWs()
  ws.on('STATUS_UPDATE', handleStatusUpdate)
  ws.on('COMMAND_FEEDBACK', handleCommandFeedback)
  ws.on('DETECTION_RESULT', handleDetectionResult)
  ws.on('LASER_FEEDBACK', handleLaserFeedback)
  ws.on('NEW_COMMAND', handleNewCommand)
  addLog('INFO', '树莓派端面板已启动')
  addLog('INFO', '正在连接 WebSocket...')
})

onUnmounted(() => {
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
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  padding: 18px 20px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 22px;
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-icon {
  font-size: 20px;
  color: var(--accent-cyan);
}

.section-title {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 0.03em;
  color: var(--text-primary);
}

.panel-body {
  position: relative;
  flex: 1;
  min-height: 0;
}

.panel-body.scrollable {
  overflow: auto;
  max-height: 100%;
}

.panel-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.panel-section {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: 16px;
  border: 1px solid var(--line-soft);
}

.panel-section h3.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  margin: 0 0 16px 0;
  color: var(--text-secondary);
}

.report-list {
  background: var(--bg-input);
  border-radius: var(--radius-sm);
  padding: 12px;
}

.report-item {
  display: flex;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--line-soft);
}

.report-item:last-child {
  border-bottom: none;
}

.report-item.reported .report-content {
  color: var(--accent-green);
  font-weight: 500;
}

.report-time {
  min-width: 80px;
  font-size: 12px;
  color: var(--text-tertiary);
  font-style: italic;
  display: flex;
  align-items: center;
}

.report-content {
  flex: 1;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.4;
}

.report-details {
  display: block;
  font-size: 11px;
  color: var(--text-tertiary);
  margin-top: 4px;
}

.success-text {
  color: var(--accent-green);
  font-weight: 500;
}

.error-text {
  color: var(--accent-red);
  font-weight: 500;
}

.info-text {
  color: var(--accent-cyan);
  font-weight: 500;
}

/* 表格样式优化 */
.robot-monitor-panel :deep(.el-table) {
  background: var(--bg-input);
}

.robot-monitor-panel :deep(.el-table th),
.robot-monitor-panel :deep(.el-table tr) {
  background: transparent;
}

.robot-monitor-panel :deep(.el-table td),
.robot-monitor-panel :deep(.el-table th.el-table__cell) {
  border-color: var(--line-soft);
}

.robot-monitor-panel :deep(.el-table__body-wrapper) {
  overflow-x: hidden;
}

.logs-container {
  max-height: 140px;
  overflow-y: auto;
  background: var(--bg-input);
  border-radius: var(--radius-sm);
  padding: 12px;
  border: 1px solid var(--line-soft);
}

.log-item {
  display: flex;
  gap: 12px;
  font-size: 12px;
  margin-bottom: 10px;
  line-height: 1.4;
}

.log-item:last-child {
  margin-bottom: 0;
}

.log-time {
  color: var(--text-tertiary);
  min-width: 80px;
}

.log-level {
  min-width: 60px;
  font-weight: 600;
}

.log-info .log-level {
  color: var(--accent-cyan);
}

.log-error .log-level {
  color: var(--accent-red);
}

.log-warning .log-level {
  color: var(--accent-orange);
}

.log-message {
  flex: 1;
  word-break: break-word;
  color: var(--text-secondary);
}

@media (max-width: 768px) {
  .panel-section {
    padding: 12px;
  }
  
  .report-item {
    flex-direction: column;
    gap: 6px;
  }
  
  .report-time {
    min-width: auto;
  }
}
</style>