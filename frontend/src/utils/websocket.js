/**
 * WebSocket封装 - 机器人状态实时推送
 */
export class RobotStatusWebSocket {
  constructor(url) {
    this.url = url
    this.ws = null
    this.reconnectDelay = 3000
    this.maxReconnectAttempts = 5
    this.reconnectAttempts = 0
    this.listeners = new Map()
  }

  connect() {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${wsProtocol}//${window.location.host}${this.url}`

    this.ws = new WebSocket(wsUrl)

    this.ws.onopen = () => {
      console.log('WebSocket连接成功')
      this.reconnectAttempts = 0
    }

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        console.log('✅ WebSocket收到消息:', message.type, message.data)

        // 处理状态更新
        if (message.type === 'STATUS_UPDATE') {
          if (this.listeners.has('STATUS_UPDATE')) {
            this.listeners.get('STATUS_UPDATE').forEach(cb => cb(message.data))
          }
        }
        // 处理指令执行结果反馈（树莓派上报）
        if (message.type === 'COMMAND_FEEDBACK') {
          console.log('🎯 收到指令执行结果:', message.data)
          if (this.listeners.has('COMMAND_FEEDBACK')) {
            this.listeners.get('COMMAND_FEEDBACK').forEach(cb => cb(message.data))
          }
        }
        // 处理检测结果（树莓派上报）
        if (message.type === 'DETECTION_RESULT') {
          console.log('🔍 收到检测结果:', message.data)
          if (this.listeners.has('DETECTION_RESULT')) {
            this.listeners.get('DETECTION_RESULT').forEach(cb => cb(message.data))
          }
        }
        // 处理激光反馈（树莓派上报）
        if (message.type === 'LASER_FEEDBACK') {
          console.log('💥 收到激光反馈:', message.data)
          if (this.listeners.has('LASER_FEEDBACK')) {
            this.listeners.get('LASER_FEEDBACK').forEach(cb => cb(message.data))
          }
        }
        // 处理新指令（服务器推送）
        if (message.type === 'NEW_COMMAND') {
          console.log('📋 收到新指令:', message.data)
          if (this.listeners.has('NEW_COMMAND')) {
            this.listeners.get('NEW_COMMAND').forEach(cb => cb(message.data))
          }
        }
      } catch (e) {
        console.error('❌ WebSocket消息解析错误', e, event.data)
      }
    }

    this.ws.onclose = () => {
      console.log('WebSocket连接关闭')
      this.tryReconnect()
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket错误', error)
    }
  }

  tryReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('WebSocket重连次数已达上限，停止重连')
      return
    }

    this.reconnectAttempts++
    console.log(`WebSocket重连... 尝试第 ${this.reconnectAttempts} 次`)
    setTimeout(() => {
      this.connect()
    }, this.reconnectDelay)
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, [])
    }
    this.listeners.get(event).push(callback)
  }

  off(event, callback) {
    if (!this.listeners.has(event)) return
    const callbacks = this.listeners.get(event)
    const index = callbacks.indexOf(callback)
    if (index !== -1) {
      callbacks.splice(index, 1)
    }
  }

  close() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }
}

// 单例
let instance = null
export function getRobotStatusWs() {
  if (!instance) {
    instance = new RobotStatusWebSocket('/ws/robot-status')
    instance.connect()
  }
  return instance
}
