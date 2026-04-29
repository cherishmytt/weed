import request from './request'

/**
 * 查询检测记录列表
 */
export function getDetectionRecords(startTime, endTime, page = 1, size = 10) {
  return request({
    url: '/detection/records',
    method: 'get',
    params: { startTime, endTime, page, size }
  })
}

/**
 * 获取检测详情
 */
export function getDetectionDetail(id) {
  return request({
    url: `/detection/records/${id}`,
    method: 'get'
  })
}

/**
 * YOLO在线检测 - 上传图片进行预测
 */
export function yoloPredict(file, conf, classes) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('conf', conf)
  if (classes && classes.trim()) {
    formData.append('classes', classes.trim())
  }
  return request({
    url: '/detection/yolo-predict',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 保存检测记录
 */
export function saveDetectionRecord(rawImage, resultImage, resultJson) {
  const formData = new FormData()
  formData.append('rawImage', rawImage)
  formData.append('resultImage', resultImage)
  formData.append('result', resultJson)
  return request({
    url: '/detection/report',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}
