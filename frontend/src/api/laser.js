import request from './request'

/**
 * 下发激光控制指令
 */
export function sendLaserCommand(action, params) {
  return request({
    url: '/robot/laser/command',
    method: 'post',
    data: { action, params }
  })
}

/**
 * 获取激光设备状态
 */
export function getLaserStatus() {
  return request({
    url: '/robot/laser/status',
    method: 'get'
  })
}

/**
 * 获取激光设备能力
 */
export function getLaserCapabilities() {
  return request({
    url: '/robot/laser/capabilities',
    method: 'get'
  })
}

/**
 * 查询激光操作日志（新接口支持多条件筛选）
 */
export function getLaserLogs(params) {
  return request({
    url: '/robot/laser/logs',
    method: 'get',
    params
  })
}

/**
 * 导出激光操作日志（指定ID列表）
 */
export function exportLaserLogs(ids) {
  return request({
    url: '/robot/laser/logs/export',
    method: 'post',
    data: { ids }
  })
}

/**
 * 批量删除激光操作日志
 */
export function batchDeleteLogs(ids) {
  return request({
    url: '/robot/laser/logs/batch-delete',
    method: 'post',
    data: { ids }
  })
}
