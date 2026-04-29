<template>
  <div class="laser-control-page">
    <el-row :gutter="16">
      <el-col :span="16">
        <!-- 激光设备状态卡片 -->
        <div class="status-card glass-panel">
          <div class="card-header">
            <el-icon><Connection /></el-icon>
            <span>激光设备状态</span>
            <el-button type="primary" @click="refreshStatus" :loading="loadingStatus" style="margin-left: auto;">
              <el-icon><Refresh /></el-icon>
              刷新状态
            </el-button>
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
          <div class="card-header">
            <el-icon><Operation /></el-icon>
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

          <el-form :model="commandForm" label-width="140px" size="default" style="max-width: 800px; margin-top: 16px;">
            <!-- 指令类型选择 - 按钮组 -->
            <el-form-item label="指令类型">
              <el-button-group>
                <el-button
                  :type="commandForm.action === 'ENABLE' ? 'primary' : 'default'"
                  :disabled="status?.connected"
                  @click="selectAction('ENABLE')"
                >
                  ▶ 上电使能
                </el-button>
                <el-button
                  :type="commandForm.action === 'DISABLE' ? 'primary' : 'default'"
                  :disabled="!status?.connected"
                  @click="selectAction('DISABLE')"
                >
                  ■ 断电关闭
                </el-button>
              </el-button-group>
              <br/>
              <el-button-group style="margin-top: 8px;">
                <el-button
                  :type="commandForm.action === 'AIM' ? 'success' : 'default'"
                  :disabled="!status?.connected"
                  @click="selectAction('AIM')"
                >
                  🎯 瞄准
                </el-button>
                <el-button
                  :type="commandForm.action === 'FIRE' ? 'primary' : 'default'"
                  :disabled="!status?.connected"
                  @click="selectAction('FIRE')"
                >
                  🔥 照射
                </el-button>
                <el-button
                  type="danger"
                  :disabled="!status?.connected"
                  @click="sendStopCommand"
                  :loading="stopSending"
                >
                  ⏸ 停止
                </el-button>
              </el-button-group>
              <br/>
              <el-button-group style="margin-top: 8px;">
                <el-button
                  :type="commandForm.action === 'SET_POWER' ? 'primary' : 'default'"
                  :disabled="!status?.connected"
                  @click="selectAction('SET_POWER')"
                >
                  ⚙ 设置功率
                </el-button>
                <el-button
                  :type="commandForm.action === 'SELF_TEST' ? 'primary' : 'default'"
                  :disabled="!status?.connected"
                  @click="selectAction('SELF_TEST')"
                >
                  🔧 自检
                </el-button>
                <el-button
                  :type="commandForm.action === 'RESET' ? 'primary' : 'default'"
                  @click="selectAction('RESET')"
                >
                  🔄 复位
                </el-button>
              </el-button-group>
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
              v-if="currentAimPosition"
              :title="`✓ 已瞄准位置: X=${currentAimPosition.targetX}, Y=${currentAimPosition.targetY}`"
              type="success"
              :closable="false"
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

            <!-- 参数区域 - 根据选中的指令显示对应参数 -->
            <template v-if="needParams">
              <el-divider content-position="left">指令参数</el-divider>
              <div class="params-group">
                <!-- AIM 瞄准参数 -->
                <template v-if="commandForm.action === 'AIM'">
                  <el-row :gutter="24">
                    <el-col :span="12">
                      <el-form-item label="X (像素坐标)">
                        <el-input-number
                          v-model="commandForm.params.targetX"
                          :precision="2"
                          :min="-500"
                          :max="5000"
                          style="width: 100%;"
                        />
                      </el-form-item>
                    </el-col>
                    <el-col :span="12">
                      <el-form-item label="Y (像素坐标)">
                        <el-input-number
                          v-model="commandForm.params.targetY"
                          :precision="2"
                          :min="-500"
                          :max="5000"
                          style="width: 100%;"
                        />
                      </el-form-item>
                    </el-col>
                  </el-row>
                </template>

                <!-- FIRE 照射：深度、3D坐标、时长 -->
                <template v-if="commandForm.action === 'FIRE'">
                  <el-row :gutter="24">
                    <el-col :span="8">
                      <el-form-item label="深度 (像素图像)">
                        <el-input-number
                          v-model="commandForm.params.depth"
                          :precision="3"
                          :step="0.1"
                          :min="0"
                          :max="5"
                          style="width: 100%;"
                        />
                      </el-form-item>
                    </el-col>
                    <el-col :span="16">
                      <el-form-item label="照射时长 (毫秒)">
                        <el-input-number
                          v-model="commandForm.params.duration"
                          :min="100"
                          :max="10000"
                          :step="100"
                          style="width: 100%;"
                        />
                      </el-form-item>
                    </el-col>
                  </el-row>

                  <el-divider content-position="left">三维坐标 (相机坐标系，单位米)</el-divider>
                  <el-row :gutter="24">
                    <el-col :span="8">
                      <el-form-item label="position3d.X">
                        <el-input-number
                          v-model="commandForm.params.position3d.x"
                          :precision="3"
                          :step="0.05"
                          :min="-5"
                          :max="5"
                          style="width: 100%;"
                        />
                      </el-form-item>
                    </el-col>
                    <el-col :span="8">
                      <el-form-item label="position3d.Y">
                        <el-input-number
                          v-model="commandForm.params.position3d.y"
                          :precision="3"
                          :step="0.05"
                          :min="-5"
                          :max="5"
                          style="width: 100%;"
                        />
                      </el-form-item>
                    </el-col>
                    <el-col :span="8">
                      <el-form-item label="position3d.Z (深度)">
                        <el-input-number
                          v-model="commandForm.params.position3d.z"
                          :precision="3"
                          :step="0.05"
                          :min="0"
                          :max="5"
                          style="width: 100%;"
                        />
                      </el-form-item>
                    </el-col>
                  </el-row>
                </template>

                <!-- SET_POWER 设置功率 -->
                <template v-if="commandForm.action === 'SET_POWER'">
                  <el-row :gutter="24">
                    <el-col :span="12">
                      <el-form-item label="输出功率 (瓦)">
                        <el-input-number
                          v-model="commandForm.params.power"
                          :min="1"
                          :max="100"
                          :step="5"
                          style="width: 100%;"
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
                <el-icon><VideoPlay /></el-icon>
                发送指令
              </el-button>
            </div>
          </el-form>
        </div>

      </el-col>
      <el-col :span="8">
        <!-- 树莓派端面板 -->
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
  VideoPause,
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
const aimSending = ref(false)
const fireSending = ref(false)
const stopSending = ref(false)
const status = ref(null)
// 最新指令执行状态
const lastCommandStatus = ref(null)
// 当前瞄准位置
const currentAimPosition = ref(null)

const commandForm = ref({
  action: 'FIRE',
  params: {
    targetX: 150,
    targetY: 100,
    depth: 0.45,
    position3d: {
      x: 0.10,
      y: 0.40,
      z: 0.85
    },
    duration: 500,
    power: 10
  }
})

// 指令说明描述
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

const currentInstructionDesc = computed(() => {
  return instructionDescriptions[commandForm.value.action] || ''
})

const needParams = computed(() => {
  return ['AIM', 'FIRE', 'SET_POWER'].includes(commandForm.value.action)
})

// 格式化时间显示 - 后端返回的 yyyy-MM-dd HH:mm:ss 格式已是本地时间，直接显示
function formatTime(timeStr) {
  if (!timeStr) return '-'
  // 已是标准格式，直接返回
  if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(timeStr)) {
    return timeStr
  }
  // 其他格式尝试解析后格式化
  try {
    const date = new Date(timeStr)
    if (isNaN(date.getTime())) return timeStr
    const pad = n => n.toString().padStart(2, '0')
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
  } catch (e) {
    return timeStr
  }
}

function selectAction(action) {
  commandForm.value.action = action
  handleActionChange()
}

function handleActionChange() {
  // 根据指令类型设置合理默认参数
  switch (commandForm.value.action) {
    case 'FIRE':
      if (!commandForm.value.params.duration) {
        commandForm.value.params.duration = 500
      }
      break
    case 'AIM':
      // AIM 不需要 duration 参数，保持默认即可
      break
    case 'SET_POWER':
      if (!commandForm.value.params.power) {
        commandForm.value.params.power = 10
      }
      break
  }
}

async function refreshStatus() {
  loadingStatus.value = true
  try {
    const res = await getLaserStatus()
    if (res.code === 200) {
      status.value = res.data
      // 同时更新瞄准位置
      if (res.data.aimTargetX !== undefined && res.data.aimTargetY !== undefined) {
        currentAimPosition.value = {
          targetX: res.data.aimTargetX,
          targetY: res.data.aimTargetY
        }
      }
    }
  } finally {
    loadingStatus.value = false
  }
}

// ==================== 新的指令发送方法 ====================
async function sendAimCommand() {
  aimSending.value = true
  try {
    const params = {
      targetX: commandForm.value.params.targetX,
      targetY: commandForm.value.params.targetY
    }
    const res = await sendLaserCommand('AIM', params)
    if (res.code === 200) {
      // 瞄准成功，更新当前瞄准位置
      currentAimPosition.value = {
        targetX: commandForm.value.params.targetX,
        targetY: commandForm.value.params.targetY
      }
      ElMessage.success('瞄准指令已下发')
    } else {
      ElMessage.error(res.message || '瞄准失败')
    }
  } catch (e) {
    ElMessage.error('瞄准指令发送失败')
  } finally {
    aimSending.value = false
  }
}

async function sendFireCommand() {
  if (!currentAimPosition.value) {
    ElMessage.warning('请先执行瞄准指令设置目标位置')
    return
  }
  fireSending.value = true
  try {
    const params = {
      targetX: currentAimPosition.value.targetX,
      targetY: currentAimPosition.value.targetY,
      depth: commandForm.value.params.depth,
      position3d: commandForm.value.params.position3d,
      duration: commandForm.value.params.duration
    }
    const res = await sendLaserCommand('FIRE', params)
    if (res.code === 200) {
      ElMessage.success('照射指令已下发，执行中...')
    } else {
      ElMessage.error(res.message || '照射指令发送失败')
    }
  } catch (e) {
    ElMessage.error('照射指令发送失败')
  } finally {
    fireSending.value = false
  }
}

async function sendStopCommand() {
  stopSending.value = true
  try {
    const res = await sendLaserCommand('STOP', null)
    if (res.code === 200) {
      ElMessage.success('停止指令已下发')
    } else {
      ElMessage.error(res.message || '停止指令发送失败')
    }
  } catch (e) {
    ElMessage.error('停止指令发送失败')
  } finally {
    stopSending.value = false
  }
}

// 指令中文名称映射
const commandNames = {
  ENABLE: '上电使能',
  DISABLE: '断电关闭',
  FIRE: '激光照射',
  STOP: '停止照射',
  AIM: '瞄准定位',
  SET_POWER: '设置功率',
  SELF_TEST: '设备自检',
  RESET: '复位设备'
}

async function sendCommand() {
  const actionName = commandNames[commandForm.value.action] || commandForm.value.action

  // 显示待执行状态
  lastCommandStatus.value = {
    status: 'pending',
    title: `${actionName}指令已下发`,
    message: '正在执行中，请稍候...',
    time: new Date().toLocaleTimeString()
  }

  sending.value = true
  try {
    let params = null
    // 根据指令类型发送必要的参数
    switch (commandForm.value.action) {
      case 'RESET':
        params = null
        break
      case 'AIM':
        params = {
          targetX: commandForm.value.params.targetX,
          targetY: commandForm.value.params.targetY
        }
        break
      case 'FIRE':
        // FIRE 检查是否已瞄准，然后发送完整参数（坐标使用已瞄准位置）
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
        params = {
          power: commandForm.value.params.power
        }
        break
      default:
        params = null
        break
    }
    const res = await sendLaserCommand(commandForm.value.action, params)
    if (res.code === 200) {
      // 标记待执行的指令ID，等待后端反馈结果
      pendingCommand = actionName
      pendingCommandId = res.data.commandId
      console.log('📤 指令已下发，等待反馈commandId:', pendingCommandId)
      // 显示"已下发"状态
      // FIRE 指令特殊显示：显示"照射中"
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
      // 设置超时：30秒后如果还没收到反馈就自动标记为超时
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
// 等待执行结果的指令信息
let pendingCommand = null
let pendingCommandId = null

// 指令执行结果完全通过 COMMAND_FEEDBACK WebSocket事件上报
// 不再通过 STATUS_UPDATE 推断执行结果，避免误判

function connectWebSocket() {
  // 使用 WebSocket 单例接收实时状态更新
  statusWs = getRobotStatusWs()

  // 监听激光状态更新
  statusWs._laserStatusCallback = (data) => {
    if (isUnmounted || !data) return
    // 区分数据类型：激光状态有 connected 字段，机器人状态没有
    if (data.connected !== undefined) {
      const oldStatus = { ...status.value }
      // 更新状态
      status.value = { ...status.value, ...data }

      // 更新当前瞄准位置
      if (data.aimTargetX !== undefined && data.aimTargetY !== undefined) {
        currentAimPosition.value = {
          targetX: data.aimTargetX,
          targetY: data.aimTargetY
        }
      }

      // 重要：只通过 COMMAND_FEEDBACK 事件更新指令执行状态
      // 不再通过 STATUS_UPDATE 推断执行结果，避免误判
    }
    // 忽略机器人状态推送，避免字段冲突
  }
  statusWs.on('STATUS_UPDATE', statusWs._laserStatusCallback)

  // 监听指令执行结果反馈（树莓派上报）
  statusWs._commandFeedbackCallback = (data) => {
    if (isUnmounted || !data) return
    console.log('📩 前端收到指令反馈:', data, '等待的commandId:', pendingCommandId)

    // 只有匹配当前等待的 commandId 才更新状态
    if (pendingCommandId && data.commandId === pendingCommandId) {
      console.log('✅ commandId匹配，更新状态显示')
      const actionName = commandNames[data.action] || data.action
      const resultUpper = (data.result || '').toUpperCase()

      if (resultUpper === 'SUCCESS') {
        // 检测是否是照射被中断的情况（FIRE 指令被中断 或 STOP 指令执行）
        const isInterrupted = (data.action === 'FIRE' && data.message && data.message.includes('中断')) ||
                             data.action === 'STOP'

        if (isInterrupted) {
          // 照射被停止：显示特殊标题
          lastCommandStatus.value = {
            status: 'success',
            title: '激光照射停止',
            message: data.message || '已成功停止激光照射',
            time: new Date().toLocaleTimeString()
          }
        } else {
          // 正常执行成功
          lastCommandStatus.value = {
            status: 'success',
            title: `${actionName}执行成功`,
            message: data.message || '指令已执行完成',
            time: new Date().toLocaleTimeString()
          }
        }

        // AIM 成功后，更新瞄准位置显示
        if (data.action === 'AIM' && commandForm.value.params.targetX && commandForm.value.params.targetY) {
          currentAimPosition.value = {
            targetX: commandForm.value.params.targetX,
            targetY: commandForm.value.params.targetY
          }
        }
      } else {
        // 执行失败
        lastCommandStatus.value = {
          status: 'error',
          title: `${actionName}执行失败`,
          message: data.message || '未知错误',
          time: new Date().toLocaleTimeString()
        }
      }

      // 清除等待状态
      pendingCommand = null
      pendingCommandId = null
    }
  }
  statusWs.on('COMMAND_FEEDBACK', statusWs._commandFeedbackCallback)
}

onMounted(() => {
  refreshStatus()
  connectWebSocket()
})

onUnmounted(() => {
  isUnmounted = true
  pendingCommand = null
  pendingCommandId = null
  if (statusWs) {
    if (statusWs._laserStatusCallback) {
      statusWs.off('STATUS_UPDATE', statusWs._laserStatusCallback)
      statusWs._laserStatusCallback = null
    }
    if (statusWs._commandFeedbackCallback) {
      statusWs.off('COMMAND_FEEDBACK', statusWs._commandFeedbackCallback)
      statusWs._commandFeedbackCallback = null
    }
    statusWs = null
  }
})
</script>

<style scoped>
.laser-control-page {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-height: 100vh;
  background: var(--app-background);
}

.status-card,
.command-card {
  border-radius: 16px;
  padding: 24px;
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
  font-weight: 500;
  font-size: 17px;
  color: var(--text-primary);
  justify-content: space-between;
  margin-bottom: 24px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  letter-spacing: -0.2px;
  font-family: var(--font-family);
}

.status-text {
  font-weight: 500;
  color: var(--text-secondary);
  font-size: 15px;
  font-family: var(--font-family);
}

.stat-value {
  font-weight: 600;
  color: var(--primary-color);
  font-size: 15px;
  font-family: var(--font-family);
}

.params-group {
  margin-bottom: 24px;
}

.submit-area {
  margin-top: 32px;
  padding-top: 28px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

/* 固定描述列表列宽，防止数据更新时布局跳动 */
.fixed-width-descriptions {
  .el-descriptions__cell {
    width: fit-content !important;
    padding-top: 16px;
    padding-bottom: 16px;
    color: var(--text-primary);
    font-family: var(--font-family);
  }
  
  .el-descriptions__label {
    color: var(--text-secondary) !important;
    font-family: var(--font-family);
  }
}

.info-value {
  font-size: 15px;
  color: var(--text-primary);
  font-weight: 500;
  font-family: var(--font-family);
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

  &.pending {
    background: rgba(64, 158, 255, 0.1);
    border-color: rgba(64, 158, 255, 0.2);
    .status-title { color: var(--primary-color); }
  }

  &.success {
    background: rgba(64, 158, 255, 0.1);
    border-color: rgba(64, 158, 255, 0.2);
    .status-title { color: var(--primary-color); }
  }

  &.error {
    background: rgba(64, 158, 255, 0.1);
    border-color: rgba(64, 158, 255, 0.2);
    .status-title { color: var(--primary-color); }
  }
}

.status-icon {
  font-size: 28px;
  flex-shrink: 0;
  margin-top: 2px;

  &.pending {
    color: var(--primary-color);
    animation: spin 1s linear infinite;
  }
  &.success { color: var(--primary-color); }
  &.error { color: var(--primary-color); }
}

.status-content {
  flex: 1;
}

.status-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
  font-family: var(--font-family);
}

.status-desc {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 4px;
  font-family: var(--font-family);
}

.status-time {
  font-size: 13px;
  color: var(--text-tertiary);
  font-family: var(--font-family);
}

/* 自定义表单样式 */
.laser-control-page :deep(.el-form-item__label) {
  color: var(--text-secondary);
  font-family: var(--font-family);
  font-size: 14px;
  font-weight: 500;
}

.laser-control-page :deep(.el-input-number__decrease),
.laser-control-page :deep(.el-input-number__increase) {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
  color: var(--text-secondary);
}

.laser-control-page :deep(.el-input__inner) {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
  font-family: var(--font-family);
}

.laser-control-page :deep(.el-input__inner:focus) {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

/* 自定义分割线样式 */
.laser-control-page :deep(.el-divider__text) {
  color: var(--text-secondary);
  font-family: var(--font-family);
  font-size: 14px;
  font-weight: 500;
  padding: 0 12px;
  background: transparent !important;
  border: none !important;
}

.laser-control-page :deep(.el-divider) {
  border-color: rgba(255, 255, 255, 0.1);
  background: transparent !important;
}

/* 自定义alert样式，使其与深色主题协调 */
.laser-control-page :deep(.el-alert) {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
  border-radius: 12px;
  margin-bottom: 16px;
}

.laser-control-page :deep(.el-alert__title) {
  color: var(--text-primary);
  font-family: var(--font-family);
  font-size: 14px;
}

.laser-control-page :deep(.el-alert__description) {
  color: var(--text-secondary);
  font-family: var(--font-family);
  font-size: 13px;
}

.laser-control-page :deep(.el-alert--info) {
  background: rgba(64, 158, 255, 0.1);
  border-color: rgba(64, 158, 255, 0.2);
}

.laser-control-page :deep(.el-alert--success) {
  background: rgba(64, 158, 255, 0.1);
  border-color: rgba(64, 158, 255, 0.2);
}

.laser-control-page :deep(.el-alert--warning) {
  background: rgba(64, 158, 255, 0.1);
  border-color: rgba(64, 158, 255, 0.2);
}

.laser-control-page :deep(.el-alert__icon) {
  color: var(--primary-color);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 响应式调整 */
@media (max-width: 768px) {
  .laser-control-page {
    padding: 16px;
    gap: 20px;
  }
  
  .status-card,
  .command-card {
    padding: 20px;
  }
  
  .card-header {
    margin-bottom: 20px;
    padding-bottom: 12px;
  }
  
  .command-status-feedback {
    padding: 16px 20px;
  }
  
  .submit-area {
    margin-top: 28px;
    padding-top: 24px;
  }
}

/* 自定义按钮样式 */
.laser-control-page :deep(.el-button) {
  border-radius: 12px !important;
  font-family: var(--font-family) !important;
  font-weight: 500 !important;
  transition: all 0.3s ease !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

.laser-control-page :deep(.el-button--primary),
.laser-control-page :deep(.el-button--success),
.laser-control-page :deep(.el-button--danger) {
  background: var(--primary-color) !important;
  border-color: var(--primary-color) !important;
  color: white !important;
}

.laser-control-page :deep(.el-button--default) {
  background: rgba(255, 255, 255, 0.05) !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
  color: var(--text-primary) !important;
}

.laser-control-page :deep(.el-button:disabled) {
  background: rgba(255, 255, 255, 0.05) !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
  color: var(--text-tertiary) !important;
  cursor: not-allowed !important;
}
</style>
