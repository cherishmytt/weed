import request from './request'

/**
 * 获取仪表盘概览数据
 */
export function getDashboardData() {
  return request({
    url: '/statistics/dashboard',
    method: 'get'
  })
}
