import request from './request'

/**
 * 获取机器人基本信息
 */
export function getRobotInfo() {
  return request({
    url: '/robot/info',
    method: 'get'
  })
}

/**
 * 获取最新运行状态
 */
export function getLatestStatus() {
  return request({
    url: '/robot/status/latest',
    method: 'get'
  })
}

/**
 * 查询状态历史（支持多条件筛选）
 */
export function getStatusHistory(params) {
  return request({
    url: '/robot/status/history',
    method: 'get',
    params
  })
}

/**
 * 导出状态历史（筛选结果）
 */
export function exportStatusHistory(params) {
  return request({
    url: '/robot/status/history/export',
    method: 'get',
    params
  })
}

/**
 * 查询轨迹
 */
export function getTrajectory(startTime, endTime) {
  return request({
    url: '/robot/trajectory',
    method: 'get',
    params: { startTime, endTime }
  })
}
