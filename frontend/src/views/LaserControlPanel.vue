<template>
  <div class="laser-control-page">
    <el-row :gutter="16">
      <el-col :span="16">
        <!-- 激光设备状态卡片 -->
        <div class="status-card glass-panel">
          <div class="card-header">
            <span>激光设备状态</span>
          </div>
          <el-descriptions :column="3" border v-loading="loadingStatus" class="fixed-width-descriptions">
            <el-descriptions-item label="连接状态" :width="180">
              <el-tag :type="status?.connected ? 'success' : 'info'" size="large">
                {{ status?.connected ? '已连接' : '未连接' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="当前状态" :width="180">
              <span class="status-text">{{ status?.statusText || '-' }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="当前功率" :width="180">
              <span v-if="status?.power !== null && status?.power !== undefined">
                {{ status.power }} W
              </span>
              <span v-else>-</span>
            </el-descriptions-item>
            <el-descriptions-item label="累计发射次数" :width="180">
              <span class="stat-value">{{ status?.totalFireCount || 0 }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="累计发射时长" :width="180">
              <span>{{ status?.totalFireDuration || 0 }} ms</span>
            </el-descriptions-item>
            <el-descriptions-item label="上次发射" :width="180">
              <span>{{ formatTime(status?.lastFireAt) }}</span>
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 发送控制指令卡片 -->
        <div class="command-card glass-panel" style="margin-top: 24px;">
          <div class="card-header-left">
            <span>发送控制指令</span>
          </div>

          <!-- 指令执行状态反馈 -->
          <div v-if="lastCommandStatus" class="command-status-feedback" :class="lastCommandStatus.status">
            <el-icon v-if="lastCommandStatus.status === 'pending'" class="status-icon pending"><Loading /></el-icon>
            <el-icon v-else-if="lastCommandStatus.status === 'success'" class="status-icon success"><CircleCheck /></el-icon>
            <el-icon v-else class="status-icon error"><CircleClose /></el-icon>
            <div class="status-content">
              <div class="status-title">{{ lastCommandStatus.title }}</div>
              <div class="status-desc">{{ lastCommandStatus.message }}</div>
              <div class="status-time" v-if="lastCommandStatus.time">{{ lastCommandStatus.time }}</div>
            </div>
          </div>

          <el-form :model="commandForm" label-width="auto" size="default" style="max-width: 100%; margin-top: 16px;">
            <!-- 指令类型选择 - 按钮组 -->
            <el-form-item label="指令类型">
              <div class="btn-group-container">
                <!-- 第一行：上电 / 断电 / 自检 / 复位 -->
                <div class="action-btn-row">
                  <button
                    class="action-btn"
                    :class="{ 'active': commandForm.action === 'ENABLE', 'disabled': status?.connected }"
                    :disabled="status?.connected"
                    @click.prevent="selectAction('ENABLE')"
                  >
                    <span class="btn-label">上电使能</span>
                  </button>
                  <button
                    class="action-btn"
                    :class="{ 'active': commandForm.action === 'DISABLE', 'disabled': !status?.connected }"
                    :disabled="!status?.connected"
                    @click.prevent="selectAction('DISABLE')"
                  >
                    <span class="btn-label">断电关闭</span>
                  </button>
                  <button
                    class="action-btn"
                    :class="{ 'active': commandForm.action === 'SELF_TEST', 'disabled': !status?.connected }"
                    :disabled="!status?.connected"
                    @click.prevent="selectAction('SELF_TEST')"
                  >
                    <span class="btn-label">自检</span>
                  </button>
                  <button
                    class="action-btn"
                    :class="{ 'active': commandForm.action === 'RESET' }"
                    @click.prevent="selectAction('RESET')"
                  >
                    <span class="btn-label">复位</span>
                  </button>
                </div>

                <!-- 第二行：瞄准 / 照射 / 停止 / 设置功率 -->
                <div class="action-btn-row">
                  <button
                    class="action-btn"
                    :class="{ 'active': commandForm.action === 'AIM', 'disabled': !status?.connected }"
                    :disabled="!status?.connected"
                    @click.prevent="selectAction('AIM')"
                  >
                    <span class="btn-label">瞄准</span>
                  </button>
                  <button
                    class="action-btn"
                    :class="{ 'active': commandForm.action === 'FIRE', 'disabled': !status?.connected }"
                    :disabled="!status?.connected"
                    @click.prevent="selectAction('FIRE')"
                  >
                    <span class="btn-label">照射</span>
                  </button>
                  <button
                    class="action-btn action-btn--danger"
                    :class="{ 'disabled': !status?.connected, 'loading': stopSending }"
                    :disabled="!status?.connected"
                    @click.prevent="sendStopCommand"
                  >
                    <span class="btn-label">{{ stopSending ? '执行中…' : '停止' }}</span>
                  </button>
                  <button
                    class="action-btn"
                    :class="{ 'active': commandForm.action === 'SET_POWER', 'disabled': !status?.connected }"
                    :disabled="!status?.connected"
                    @click.prevent="selectAction('SET_POWER')"
                  >
                    <span class="btn-label">设置功率</span>
                  </button>
                </div>
              </div>
            </el-form-item>

            <!-- 指令说明 -->
            <el-alert
              v-if="currentInstructionDesc"
              :title="currentInstructionDesc"
              type="info"
              :closable="false"
              show-icon
              style="margin-bottom: 16px;"
            />

            <!-- 当前瞄准位置显示 -->
            <el-alert
              v-if="showAimPosition && currentAimPosition"
              :title="`✓ 已瞄准位置: X=${currentAimPosition.targetX}, Y=${currentAimPosition.targetY}`"
              type="success"
              :closable="true"
              @close="showAimPosition = false"
              show-icon
              style="margin-bottom: 16px;"
            />
            <el-alert
              v-else-if="commandForm.action === 'FIRE'"
              title="提示：照射将使用当前瞄准位置的X/Y坐标，请先执行瞄准指令"
              type="warning"
              :closable="false"
              show-icon
              style="margin-bottom: 16px;"
            />

            <!-- 参数区域 -->
            <template v-if="needParams">
              <el-divider content-position="left">指令参数</el-divider>
              <div class="params-group">

                <!-- AIM 瞄准参数 -->
                <template v-if="commandForm.action === 'AIM'">
                  <el-row :gutter="16">
                    <el-col :span="12">
                      <el-form-item label="X 坐标 (px)">
                        <el-input-number
                          v-model="commandForm.params.targetX"
                          :precision="2"
                          :min="-500"
                          :max="5000"
                          class="param-input"
                        />
                      </el-form-item>
                    </el-col>
                    <el-col :span="12">
                      <el-form-item label="Y 坐标 (px)">
                        <el-input-number
                          v-model="commandForm.params.targetY"
                          :precision="2"
                          :min="-500"
                          :max="5000"
                          class="param-input"
                        />
                      </el-form-item>
                    </el-col>
                  </el-row>
                </template>

                <!-- FIRE 照射参数 -->
                <template v-if="commandForm.action === 'FIRE'">
                  <el-row :gutter="16">
                    <el-col :span="12">
                      <el-form-item label="深度">
                        <el-input-number
                          v-model="commandForm.params.depth"
                          :precision="3"
                          :step="0.1"
                          :min="0"
                          :max="5"
                          class="param-input"
                        />
                      </el-form-item>
                    </el-col>
                    <el-col :span="12">
                      <el-form-item label="时长 (ms)">
                        <el-input-number
                          v-model="commandForm.params.duration"
                          :min="100"
                          :max="10000"
                          :step="100"
                          class="param-input"
                        />
                      </el-form-item>
                    </el-col>
                  </el-row>

                  <el-divider content-position="left">三维坐标 (相机坐标系，单位米)</el-divider>
                  <el-row :gutter="16">
                    <el-col :span="8">
                      <el-form-item label="X">
                        <el-input-number
                          v-model="commandForm.params.position3d.x"
                          :precision="3"
                          :step="0.05"
                          :min="-5"
                          :max="5"
                          class="param-input"
                        />
                      </el-form-item>
                    </el-col>
                    <el-col :span="8">
                      <el-form-item label="Y">
                        <el-input-number
                          v-model="commandForm.params.position3d.y"
                          :precision="3"
                          :step="0.05"
                          :min="-5"
                          :max="5"
                          class="param-input"
                        />
                      </el-form-item>
                    </el-col>
                    <el-col :span="8">
                      <el-form-item label="Z ">
                        <el-input-number
                          v-model="commandForm.params.position3d.z"
                          :precision="3"
                          :step="0.05"
                          :min="0"
                          :max="5"
                          class="param-input"
                        />
                      </el-form-item>
                    </el-col>
                  </el-row>
                </template>

                <!-- SET_POWER 设置功率 -->
                <template v-if="commandForm.action === 'SET_POWER'">
                  <el-row :gutter="16">
                    <el-col :span="12">
                      <el-form-item label="功率 (W)">
                        <el-input-number
                          v-model="commandForm.params.power"
                          :min="1"
                          :max="100"
                          :step="5"
                          class="param-input"
                        />
                      </el-form-item>
                    </el-col>
                  </el-row>
                </template>

              </div>
            </template>

            <!-- 发送指令按钮 -->
            <div class="submit-area">
              <el-button type="primary" size="large" @click="sendCommand" :loading="sending" style="min-width: 200px;">
                发送指令
              </el-button>
            </div>
          </el-form>
        </div>

      </el-col>

      <!-- 右侧：模拟树莓派端面板 -->
      <el-col :span="8">
        <RobotMonitorPanel />
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Connection,
  Refresh,
  Operation,
  VideoPlay,
  Loading,
  CircleCheck,
  CircleClose
} from '@element-plus/icons-vue'
import { sendLaserCommand, getLaserStatus } from '@/api/laser'
import { getRobotStatusWs } from '@/utils/websocket'
import RobotMonitorPanel from '@/components/RobotMonitorPanel.vue'

const router = useRouter()
const loadingStatus = ref(false)
const sending = ref(false)
const stopSending = ref(false)
const status = ref(null)
const lastCommandStatus = ref(null)
const currentAimPosition = ref(null)
const showAimPosition = ref(false)

const commandForm = ref({
  action: 'FIRE',
  params: {
    targetX: 150,
    targetY: 100,
    depth: 0.45,
    position3d: { x: 0.10, y: 0.40, z: 0.85 },
    duration: 500,
    power: 10
  }
})

const instructionDescriptions = {
  'ENABLE': '使激光设备上电，进入待机状态',
  'DISABLE': '关闭激光设备电源，断开连接',
  'FIRE': '在当前瞄准位置开启激光照射，可随时按停止指令终止照射',
  'STOP': '立即停止当前正在进行的激光照射',
  'SET_POWER': '设置激光的输出功率，单位：瓦特',
  'AIM': '激光头移动到指定坐标位置瞄准，为照射做准备',
  'SELF_TEST': '执行激光设备全套自检程序',
  'RESET': '复位激光设备控制器，清除错误状态'
}

const currentInstructionDesc = computed(() => instructionDescriptions[commandForm.value.action] || '')
const needParams = computed(() => ['AIM', 'FIRE', 'SET_POWER'].includes(commandForm.value.action))

function formatTime(timeStr) {
  if (!timeStr) return '-'
  if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(timeStr)) return timeStr
  try {
    const date = new Date(timeStr)
    if (isNaN(date.getTime())) return timeStr
    const pad = n => n.toString().padStart(2, '0')
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
  } catch (e) { return timeStr }
}

function selectAction(action) {
  commandForm.value.action = action
  handleActionChange()
}

function handleActionChange() {
  switch (commandForm.value.action) {
    case 'FIRE':
      if (!commandForm.value.params.duration) commandForm.value.params.duration = 500
      break
    case 'SET_POWER':
      if (!commandForm.value.params.power) commandForm.value.params.power = 10
      break
  }
}

async function refreshStatus() {
  loadingStatus.value = true
  try {
    const res = await getLaserStatus()
    if (res.code === 200) {
      status.value = res.data
      if (res.data.aimTargetX !== undefined && res.data.aimTargetY !== undefined) {
        currentAimPosition.value = { targetX: res.data.aimTargetX, targetY: res.data.aimTargetY }
      }
    }
  } finally {
    loadingStatus.value = false
  }
}

async function sendStopCommand() {
  stopSending.value = true
  try {
    const res = await sendLaserCommand('STOP', null)
    if (res.code === 200) ElMessage.success('停止指令已下发')
    else ElMessage.error(res.message || '停止指令发送失败')
  } catch (e) {
    ElMessage.error('停止指令发送失败')
  } finally {
    stopSending.value = false
  }
}

const commandNames = {
  ENABLE: '上电使能', DISABLE: '断电关闭', FIRE: '激光照射',
  STOP: '停止照射', AIM: '瞄准定位', SET_POWER: '设置功率',
  SELF_TEST: '设备自检', RESET: '复位设备'
}

async function sendCommand() {
  const actionName = commandNames[commandForm.value.action] || commandForm.value.action
  lastCommandStatus.value = {
    status: 'pending',
    title: `${actionName}指令已下发`,
    message: '正在执行中，请稍候...',
    time: new Date().toLocaleTimeString()
  }
  sending.value = true
  try {
    let params = null
    switch (commandForm.value.action) {
      case 'RESET': params = null; break
      case 'AIM':
        params = { targetX: commandForm.value.params.targetX, targetY: commandForm.value.params.targetY }
        break
      case 'FIRE':
        if (!currentAimPosition.value) {
          ElMessage.warning('请先执行瞄准指令设置目标位置')
          sending.value = false
          return
        }
        params = {
          targetX: currentAimPosition.value.targetX,
          targetY: currentAimPosition.value.targetY,
          depth: commandForm.value.params.depth,
          position3d: commandForm.value.params.position3d,
          duration: commandForm.value.params.duration
        }
        break
      case 'SET_POWER':
        params = { power: commandForm.value.params.power }
        break
      default: params = null
    }
    const res = await sendLaserCommand(commandForm.value.action, params)
    if (res.code === 200) {
      pendingCommand = actionName
      pendingCommandId = res.data.commandId
      if (commandForm.value.action === 'FIRE') {
        lastCommandStatus.value = {
          status: 'pending',
          title: '激光照射中',
          message: `预计 ${commandForm.value.params.duration}ms 后完成，可随时点击停止中断`,
          time: new Date().toLocaleTimeString()
        }
      } else {
        lastCommandStatus.value = {
          status: 'pending',
          title: `${actionName}指令已下发`,
          message: '正在执行中，请稍候...',
          time: new Date().toLocaleTimeString()
        }
      }
      setTimeout(() => {
        if (pendingCommandId === res.data.commandId) {
          lastCommandStatus.value = {
            status: 'error',
            title: `${actionName}执行超时`,
            message: '未收到设备执行反馈，请检查设备状态',
            time: new Date().toLocaleTimeString()
          }
          pendingCommand = null
          pendingCommandId = null
        }
      }, 30000)
      ElMessage.success('指令已下发')
    } else {
      lastCommandStatus.value = {
        status: 'error',
        title: `${actionName}执行失败`,
        message: res.message || '未知错误',
        time: new Date().toLocaleTimeString()
      }
      pendingCommand = null
      pendingCommandId = null
      ElMessage.error(res.message)
    }
  } catch (e) {
    lastCommandStatus.value = {
      status: 'error',
      title: `${actionName}发送失败`,
      message: e.message || '网络错误',
      time: new Date().toLocaleTimeString()
    }
    ElMessage.error('指令发送失败')
  } finally {
    sending.value = false
  }
}

let statusWs = null
let isUnmounted = false
let pendingCommand = null
let pendingCommandId = null

function connectWebSocket() {
  statusWs = getRobotStatusWs()
  statusWs._laserStatusCallback = (data) => {
    if (isUnmounted || !data) return
    if (data.connected !== undefined) {
      status.value = { ...status.value, ...data }
      if (data.aimTargetX !== undefined && data.aimTargetY !== undefined) {
        currentAimPosition.value = { targetX: data.aimTargetX, targetY: data.aimTargetY }
      }
    }
  }
  statusWs.on('STATUS_UPDATE', statusWs._laserStatusCallback)

  statusWs._commandFeedbackCallback = (data) => {
    if (isUnmounted || !data) return
    if (pendingCommandId && data.commandId === pendingCommandId) {
      const actionName = commandNames[data.action] || data.action
      const resultUpper = (data.result || '').toUpperCase()
      if (resultUpper === 'SUCCESS') {
        const isInterrupted = (data.action === 'FIRE' && data.message?.includes('中断')) || data.action === 'STOP'
        lastCommandStatus.value = {
          status: 'success',
          title: isInterrupted ? '激光照射停止' : `${actionName}执行成功`,
          message: data.message || (isInterrupted ? '已成功停止激光照射' : '指令已执行完成'),
          time: new Date().toLocaleTimeString()
        }
        if (data.action === 'AIM' && commandForm.value.params.targetX && commandForm.value.params.targetY) {
          currentAimPosition.value = { targetX: commandForm.value.params.targetX, targetY: commandForm.value.params.targetY }
          showAimPosition.value = true
        }
      } else {
        lastCommandStatus.value = {
          status: 'error',
          title: `${actionName}执行失败`,
          message: data.message || '未知错误',
          time: new Date().toLocaleTimeString()
        }
      }
      pendingCommand = null
      pendingCommandId = null
    }
  }
  statusWs.on('COMMAND_FEEDBACK', statusWs._commandFeedbackCallback)
}

onMounted(() => { refreshStatus(); connectWebSocket() })
onUnmounted(() => {
  isUnmounted = true
  pendingCommand = null
  pendingCommandId = null
  if (statusWs) {
    if (statusWs._laserStatusCallback) { statusWs.off('STATUS_UPDATE', statusWs._laserStatusCallback); statusWs._laserStatusCallback = null }
    if (statusWs._commandFeedbackCallback) { statusWs.off('COMMAND_FEEDBACK', statusWs._commandFeedbackCallback); statusWs._commandFeedbackCallback = null }
    statusWs = null
  }
})
</script>

<style scoped>
.laser-control-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.laser-control-page :deep(.el-row) {
  min-height: 100%;
}

.laser-control-page :deep(.el-col) {
  display: flex;
  flex-direction: column;
}

.status-card,
.command-card {
  border-radius: var(--radius-lg);
  padding: 24px;
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  font-weight: 500;
  font-size: 17px;
  color: var(--text-primary);
  margin-bottom: 24px;
  padding-bottom: 12px;
}

.card-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  font-size: 17px;
  color: var(--text-primary);
  margin-bottom: 24px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.status-text {
  font-weight: 500;
  color: var(--text-secondary);
  font-size: 15px;
}

.stat-value {
  font-weight: 600;
  color: var(--primary-color);
  font-size: 15px;
}

/* ── 自定义指令按钮组 ──────────────────────────── */
.btn-group-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
  max-width: 580px;
}

.action-btn-row {
  display: flex;
  gap: 10px;
}

.action-btn {
  flex: 1;
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 12px 14px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: 1px solid rgba(89, 214, 255, 0.25);
  background: rgba(11, 29, 49, 0.8);
  color: rgba(237, 245, 255, 0.9);
  transition: all 0.22s ease;
  outline: none;
  user-select: none;
  height: 44px;
}

.action-btn:hover:not(.disabled) {
  background: rgba(26, 68, 112, 0.85);
  border-color: rgba(89, 214, 255, 0.5);
  color: #fff;
}

.action-btn.active {
  background: linear-gradient(135deg, rgba(47, 115, 255, 0.65) 0%, rgba(89, 214, 255, 0.55) 100%);
  border-color: rgba(89, 214, 255, 0.85);
  color: #fff;
  box-shadow: 0 4px 20px rgba(47, 115, 255, 0.45);
}

.action-btn--danger {
  border-color: rgba(255, 93, 93, 0.5);
  background: rgba(192, 59, 59, 0.25);
  color: #ff9999;
}
.action-btn--danger:hover:not(.disabled) {
  background: rgba(192, 59, 59, 0.4);
  border-color: rgba(255, 93, 93, 0.75);
  color: #fff;
}

.action-btn.disabled,
.action-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
  pointer-events: none;
  box-shadow: none;
}
/* ─────────────────────────────────────────────── */

.params-group {
  margin-bottom: 24px;
}

.laser-control-page :deep(.param-input) {
  width: 100% !important;
}

.submit-area {
  margin-top: 32px;
  padding-top: 28px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

/* 描述列表 */
.fixed-width-descriptions :deep(.el-descriptions__cell) {
  width: fit-content !important;
  padding-top: 16px;
  padding-bottom: 16px;
  color: var(--text-primary);
}
.fixed-width-descriptions :deep(.el-descriptions__label) {
  color: var(--text-secondary) !important;
}

/* 指令执行状态反馈 */
.command-status-feedback {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 20px 24px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 20px;
}

.command-status-feedback.pending {
  background: rgba(64, 158, 255, 0.1);
  border-color: rgba(64, 158, 255, 0.2);
}
.command-status-feedback.pending .status-title { color: var(--accent-cyan); }

.command-status-feedback.success {
  background: rgba(57, 211, 152, 0.08);
  border-color: rgba(57, 211, 152, 0.25);
}
.command-status-feedback.success .status-title { color: var(--accent-green); }

.command-status-feedback.error {
  background: rgba(255, 93, 93, 0.08);
  border-color: rgba(255, 93, 93, 0.25);
}
.command-status-feedback.error .status-title { color: var(--accent-red); }

.status-icon {
  font-size: 28px;
  flex-shrink: 0;
  margin-top: 2px;
}
.status-icon.pending { color: var(--accent-cyan); animation: spin 1s linear infinite; }
.status-icon.success { color: var(--accent-green); }
.status-icon.error   { color: var(--accent-red); }

.status-content { flex: 1; }
.status-title { font-size: 16px; font-weight: 600; margin-bottom: 8px; }
.status-desc  { font-size: 14px; color: var(--text-secondary); margin-bottom: 4px; }
.status-time  { font-size: 13px; color: var(--text-tertiary); }

/* 表单 label */
.laser-control-page :deep(.el-form-item__label) {
  color: var(--text-secondary);
  font-size: 15px;
  font-weight: 500;
  padding-right: 20px !important;
}

.laser-control-page :deep(.el-form-item) {
  margin-bottom: 22px;
}

/* ── 数字输入框 ──────────────────────────── */
.laser-control-page :deep(.el-input-number) {
  width: 100%;
}
.laser-control-page :deep(.el-input-number .el-input__wrapper) {
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid rgba(99, 195, 255, 0.14) !important;
  box-shadow: none !important;
  border-radius: 12px !important;
}
.laser-control-page :deep(.el-input-number .el-input__wrapper:hover) {
  border-color: rgba(99, 195, 255, 0.3) !important;
}
.laser-control-page :deep(.el-input-number .el-input__wrapper.is-focus) {
  border-color: rgba(89, 214, 255, 0.5) !important;
  box-shadow: 0 0 0 1px rgba(89, 214, 255, 0.2) inset !important;
}
.laser-control-page :deep(.el-input-number .el-input__inner) {
  color: var(--text-primary) !important;
  background: transparent !important;
  text-align: center;
  font-size: 14px;
  font-weight: 500;
}
.laser-control-page :deep(.el-input-number__decrease),
.laser-control-page :deep(.el-input-number__increase) {
  background: transparent !important;
  border-color: rgba(99, 195, 255, 0.1) !important;
  color: var(--text-secondary);
  box-shadow: none !important;
}
.laser-control-page :deep(.el-input-number__decrease:hover),
.laser-control-page :deep(.el-input-number__increase:hover) {
  background: rgba(89, 214, 255, 0.1) !important;
  color: var(--accent-cyan) !important;
}
.laser-control-page :deep(.el-input-number__decrease:disabled),
.laser-control-page :deep(.el-input-number__increase:disabled) {
  color: var(--text-tertiary);
  background: transparent !important;
}
/* ─────────────────────────────────────────────── */

/* 分割线 */
.laser-control-page :deep(.el-divider__text) {
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  padding: 0 12px;
  background: transparent !important;
}
.laser-control-page :deep(.el-divider) {
  border-color: rgba(255, 255, 255, 0.08);
}

/* Alert */
.laser-control-page :deep(.el-alert) {
  border-radius: 12px;
  margin-bottom: 16px;
}
.laser-control-page :deep(.el-alert__title) {
  color: var(--text-primary);
  font-size: 14px;
}
.laser-control-page :deep(.el-alert--info) {
  background: rgba(47, 115, 255, 0.08);
  border-color: rgba(47, 115, 255, 0.2);
}
.laser-control-page :deep(.el-alert--success) {
  background: rgba(57, 211, 152, 0.08);
  border-color: rgba(57, 211, 152, 0.22);
}
.laser-control-page :deep(.el-alert--warning) {
  background: rgba(255, 141, 67, 0.08);
  border-color: rgba(255, 141, 67, 0.22);
}
.laser-control-page :deep(.el-alert--info .el-alert__icon)    { color: var(--accent-blue); }
.laser-control-page :deep(.el-alert--success .el-alert__icon) { color: var(--accent-green); }
.laser-control-page :deep(.el-alert--warning .el-alert__icon) { color: var(--accent-orange); }

/* 发送指令按钮 */
.laser-control-page :deep(.el-button) {
  border-radius: 10px !important;
  font-weight: 500 !important;
  transition: all 0.22s ease !important;
  border: 1px solid rgba(89, 214, 255, 0.35) !important;
  background: rgba(11, 29, 49, 0.85) !important;
  color: rgba(237, 245, 255, 0.95) !important;
}
.laser-control-page :deep(.el-button:hover) {
  background: rgba(26, 68, 112, 0.9) !important;
  border-color: rgba(89, 214, 255, 0.6) !important;
  color: #fff !important;
  box-shadow: 0 4px 18px rgba(47, 115, 255, 0.35) !important;
}
.laser-control-page :deep(.el-button--primary) {
  background: linear-gradient(135deg, rgba(47, 115, 255, 0.75) 0%, rgba(89, 214, 255, 0.65) 100%) !important;
  border-color: rgba(89, 214, 255, 0.85) !important;
  color: #fff !important;
  box-shadow: 0 6px 22px rgba(47, 115, 255, 0.5) !important;
}
.laser-control-page :deep(.el-button--primary:hover) {
  background: linear-gradient(135deg, rgba(47, 115, 255, 0.85) 0%, rgba(89, 214, 255, 0.75) 100%) !important;
  border-color: rgba(89, 214, 255, 0.95) !important;
  box-shadow: 0 8px 26px rgba(47, 115, 255, 0.55) !important;
}
.laser-control-page :deep(.el-button:disabled) {
  opacity: 0.35 !important;
  cursor: not-allowed !important;
  box-shadow: none !important;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .status-card, .command-card { padding: 20px; }
  .card-header { margin-bottom: 20px; }
  .command-status-feedback { padding: 16px 20px; }
  .submit-area { margin-top: 28px; padding-top: 24px; }
}
</style>