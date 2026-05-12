<template>
  <div class="yolo-detection-page">
    <div class="online-detect-card glass-panel">
      <div class="card-header">
        <h2>YOLOv8 Pose 杂草检测</h2>
        <p class="muted">上传图片后，模型会返回杂草边界框、根茎关键点和可视化结果图。</p>
      </div>

      <el-form :model="detectForm" label-width="140px" class="detect-form">
        <el-form-item label="选择图片">
          <div class="upload-container">
            <el-upload
              ref="uploadRef"
              :auto-upload="false"
              :limit="1"
              :on-change="handleFileChange"
              accept="image/jpeg,image/png"
              :show-file-list="false"
            >
              <template #trigger>
                <el-button type="primary" class="upload-button">
                  <el-icon><UploadFilled /></el-icon>
                  选择文件
                </el-button>
              </template>
            </el-upload>
            <div v-if="detectForm.fileName" class="file-info selected">
              <el-icon class="file-icon"><Document /></el-icon>
              <span class="file-text">{{ detectForm.fileName }}</span>
              <el-button type="text" size="small" @click="clearFile" class="clear-button">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
            <div v-else class="file-info">
              <span class="file-text">未选择任何文件</span>
            </div>
          </div>
        </el-form-item>

        <el-form-item label="置信度 (0.01 ~ 1.0)">
          <el-input-number
            v-model="detectForm.conf"
            :min="0.01"
            :max="1.0"
            :step="0.01"
            :precision="2"
            style="width: 200px;"
          />
        </el-form-item>

        <el-form-item label="类别过滤 (可选)">
          <el-input
            v-model="detectForm.classes"
            placeholder="1 = 过滤作物，0 = 过滤杂草"
            style="width: 400px;"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" size="large" @click="startDetection" :loading="detectLoading">
            开始检测
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 检测结果 -->
    <div class="result-card glass-panel" v-if="detectResult !== null" style="margin-top: 20px;">
      <div class="card-header">
        <h3 class="section-title">检测结果</h3>
      </div>

      <el-row :gutter="20">
        <el-col :span="12">
          <div class="image-card glass-panel">
            <div class="card-header">
              <h4 class="section-title">原图</h4>
            </div>
            <el-image
              v-if="detectResult.result?.originalImageUrl"
              :src="detectResult.result.originalImageUrl"
              fit="contain"
              :preview-src-list="[detectResult.result.originalImageUrl]"
              preview-teleported
              style="width: 100%; max-height: 400px"
            />
          </div>
        </el-col>
        <el-col :span="12">
          <div class="image-card glass-panel">
            <div class="card-header">
              <h4 class="section-title">推理结果图</h4>
            </div>
            <el-image
              v-if="detectResult.result?.outputImageUrl"
              :src="detectResult.result.outputImageUrl"
              fit="contain"
              :preview-src-list="[detectResult.result.outputImageUrl]"
              preview-teleported
              style="width: 100%; max-height: 400px"
            />
          </div>
        </el-col>
      </el-row>

      <el-row style="margin-top: 20px;">
        <el-col :span="24">
          <div class="stats-card glass-panel">
            <div class="card-header">
              <h4 class="section-title">检测统计</h4>
            </div>
            <el-descriptions :column="4" border>
              <el-descriptions-item label="目标总数">{{ detectResult.result?.result?.detections?.length || 0 }}</el-descriptions-item>
              <el-descriptions-item label="推理耗时">{{ detectResult.elapsedMs }} ms</el-descriptions-item>
              <el-descriptions-item label="置信度阈值">{{ detectForm.conf }}</el-descriptions-item>
              <el-descriptions-item label="类别过滤">{{ detectForm.classes || '(全部)' }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </el-col>
      </el-row>

      <el-row style="margin-top: 20px;" v-if="detectResult.result?.result?.detections && detectResult.result.result.detections.length > 0">
        <el-col :span="24">
          <div class="targets-card glass-panel">
            <div class="card-header">
              <h4 class="section-title">目标列表 (共 {{ detectResult.result.result.detections.length }} 个目标)</h4>
            </div>
            <el-table :data="detectResult.result.result.detections" border max-height="400" fit style="width: 100%;">
              <el-table-column label="类别ID" width="80">
                <template #default="{ row }">
                  <el-tag>{{ row.classId ?? 0 }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="类别名称" width="120">
                <template #default="{ row }">
                  <el-tag :type="(row.classId ?? 0) === 8 ? 'danger' : 'success'">
                    {{ row.className ?? '-' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="置信度">
                <template #default="{ row }">
                  {{ ((row.confidence ?? 0) * 100).toFixed(1) }}%
                </template>
              </el-table-column>
              <el-table-column label="边界框 [x1, y1, x2, y2]">
                <template #default="{ row }">
                  <template v-if="row.bbox">
                    <template v-if="Array.isArray(row.bbox)">
                      [{{ row.bbox.join(', ') }}]
                    </template>
                    <template v-else>
                      [{{ row.bbox.x1?.toFixed(1) }}, {{ row.bbox.y1?.toFixed(1) }}, {{ row.bbox.x2?.toFixed(1) }}, {{ row.bbox.y2?.toFixed(1) }}]
                    </template>
                  </template>
                  <template v-else>-</template>
                </template>
              </el-table-column>
              <el-table-column label="根茎坐标" width="120">
                <template #default="{ row }">
                  <div v-if="row.stem">
                    ({{ (row.stem.x || 0).toFixed(1) }}, {{ (row.stem.y || 0).toFixed(1) }})
                  </div>
                  <div v-else>-</div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-col>
      </el-row>

      <el-row style="margin-top: 20px;" v-if="detectResult.result?.runtimeLog">
        <el-col :span="24">
          <div class="log-card glass-panel">
            <el-collapse>
              <el-collapse-item title="运行日志">
                <pre class="runtime-log">{{ detectResult.result.runtimeLog }}</pre>
              </el-collapse-item>
            </el-collapse>
          </div>
        </el-col>
      </el-row>

      <!-- 保存到记录按钮 -->
      <div style="margin-top: 20px; text-align: right;">
        <el-button type="primary" @click="saveToDetectionRecords" :loading="saving">
          保存到检测记录
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Document, Delete } from '@element-plus/icons-vue'
import { yoloPredict, saveDetectionRecord } from '@/api/detection'
import { useDetectionStore } from '@/store/detection'

const uploadRef = ref(null)
const detectLoading = ref(false)
const saving = ref(false)

const detectionStore = useDetectionStore()

const detectForm = ref({
  file: detectionStore.detectForm.file,
  fileName: detectionStore.detectForm.fileName,
  conf: detectionStore.detectForm.conf,
  classes: detectionStore.detectForm.classes
})

const detectResult = ref(detectionStore.currentResult)

watch(detectForm, (newForm) => {
  detectionStore.setDetectForm(newForm)
}, { deep: true })

watch(detectResult, (newResult) => {
  detectionStore.setDetectionResult(newResult)
})

function handleFileChange(file, fileList) {
  if (fileList && fileList.length > 0) {
    detectForm.value.file = fileList[fileList.length - 1].raw
    detectForm.value.fileName = fileList[fileList.length - 1].name
  } else {
    detectForm.value.file = null
    detectForm.value.fileName = ''
  }
}

function clearFile() {
  detectForm.value.file = null
  detectForm.value.fileName = ''
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
  detectionStore.clearDetectForm()
}

async function startDetection() {
  if (!detectForm.value.file) {
    ElMessage.warning('请先选择图片文件')
    return
  }

  detectLoading.value = true
  try {
    const res = await yoloPredict(
      detectForm.value.file,
      detectForm.value.conf,
      detectForm.value.classes
    )
    if (res.code === 200) {
      detectResult.value = res.data
      detectionStore.setDetectionResult(res.data)
      ElMessage.success('检测完成')
    } else {
      ElMessage.error(res.message || '检测失败')
    }
  } catch (err) {
    console.error('检测异常:', err)
    ElMessage.error('检测异常: ' + err.message)
  } finally {
    detectLoading.value = false
  }
}

async function saveToDetectionRecords() {
  if (!detectResult.value || !detectResult.value.result) {
    ElMessage.warning('没有检测结果可保存')
    return
  }

  saving.value = true
  try {
    // 从URL获取图片文件
    const originalImageUrl = detectResult.value.result.originalImageUrl
    const outputImageUrl = detectResult.value.result.outputImageUrl
    const resultData = detectResult.value.result.result

    // 下载原始图片
    const originalResponse = await fetch(originalImageUrl)
    if (!originalResponse.ok) {
      throw new Error('下载原始图片失败')
    }
    const originalBlob = await originalResponse.blob()
    const originalFile = new File([originalBlob], 'original.jpg', { type: originalBlob.type })

    // 下载结果图片
    const outputResponse = await fetch(outputImageUrl)
    if (!outputResponse.ok) {
      throw new Error('下载结果图片失败')
    }
    const outputBlob = await outputResponse.blob()
    const outputFile = new File([outputBlob], 'result.jpg', { type: outputBlob.type })

    // 准备结果JSON，添加后端所需的字段
    const enhancedResultData = {
      ...resultData,
      detections: resultData.detections.map(d => ({
        ...d,
        class: d.classId === 8 ? 'weed' : 'crop'
      })),
      weedCount: resultData.detections.filter(d => d.classId === 8).length,
      cropCount: resultData.detections.filter(d => d.classId !== 8).length,
      inferenceTime: detectResult.value.elapsedMs,
      detectedAt: new Date().toISOString()
    }
    const resultJson = JSON.stringify(enhancedResultData)

    // 调用保存API
    const res = await saveDetectionRecord(originalFile, outputFile, resultJson)
    if (res.code === 200) {
      ElMessage.success('保存成功，可在检测记录页面查看')
    } else {
      ElMessage.error(res.message || '保存失败')
    }
  } catch (err) {
    console.error('保存异常:', err)
    ElMessage.error('保存异常: ' + err.message)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.yolo-detection-page {
  min-height: 0;
}

.online-detect-card {
  padding: 24px;
  overflow: hidden;
}

.card-header {
  margin-top: 0;
  margin-bottom: 20px;
}

h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.3px;
}

h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.3px;
}

h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.3px;
}

.detect-form {
  margin-top: 16px;
}

.detect-form :deep(.el-upload) {
  display: block;
}

.upload-container {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  width: 100%;
}

.upload-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 500;
  border-radius: var(--radius-sm);
  transition: all 0.3s ease;
  white-space: nowrap;
}

.upload-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-input);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-sm);
  flex: 1;
  min-width: 200px;
  transition: all 0.3s ease;
}

.file-info.selected {
  background: var(--interactive-hover);
  border-color: var(--accent-blue);
}

.file-icon {
  font-size: 16px;
  color: var(--accent-blue);
  flex-shrink: 0;
}

.file-text {
  flex: 1;
  font-size: 13px;
  color: var(--text-secondary);
  word-break: break-all;
}

.file-info.selected .file-text {
  color: var(--text-primary);
  font-weight: 500;
}

.clear-button {
  flex-shrink: 0;
  color: var(--accent-red);
  transition: all 0.3s ease;
  padding: 8px;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 93, 93, 0.1);
  border: 1px solid rgba(255, 93, 93, 0.3);
  border-radius: 12px;
  font-size: 18px;
}

.clear-button:hover {
  background: rgba(255, 93, 93, 0.2);
  border-color: var(--accent-red);
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(255, 93, 93, 0.3);
}

.form-tip {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 4px;
}

.result-card {
  padding: 24px;
  overflow: hidden;
}

.image-card,
.stats-card,
.targets-card,
.log-card {
  padding: 16px;
  overflow: hidden;
}

.runtime-log {
  color: var(--text-primary);
  background: var(--bg-input);
  padding: 16px;
  max-height: 200px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  font-family: 'Consolas', 'Monaco', 'Microsoft YaHei', monospace;
  font-size: 13px;
  line-height: 1.8;
  border-radius: var(--radius-sm);
  border: 1px solid var(--line-soft);
}

/* 自定义折叠面板样式 */
.log-card :deep(.el-collapse-item__header) {
  background: transparent;
  border: none !important;
  color: var(--text-primary);
  font-family: var(--font-family);
  font-weight: 500;
  padding: 8px 0;
  margin-bottom: 8px;
}

.log-card :deep(.el-collapse-item__header:hover) {
  background: transparent;
}

.log-card :deep(.el-collapse-item__content) {
  background: transparent;
  border: none !important;
  padding: 0;
}

.log-card :deep(.el-collapse-item__arrow) {
  color: var(--text-secondary);
}

.log-card :deep(.el-collapse) {
  border: none !important;
  background: transparent !important;
}

.log-card :deep(.el-collapse-item) {
  border: none !important;
  background: transparent !important;
}

.log-card :deep(.el-collapse-item__wrap) {
  border: none !important;
  background: transparent !important;
}

.log-card :deep(.el-collapse-item__header) {
  background: transparent !important;
}

.log-card :deep(.el-collapse-item__content) {
  background: transparent !important;
}

/* 响应式设计 */
@media (max-width: 768px) {
  
  .online-detect-card,
  .result-card {
    padding: 16px;
  }
  
  .image-card,
  .stats-card,
  .targets-card,
  .log-card {
    padding: 12px;
  }
}

/* 检测统计样式 */
.stats-card :deep(.el-descriptions) {
  background: transparent;
}

.stats-card :deep(.el-descriptions__label) {
  color: #a0c8e8 !important;
  font-weight: 600;
  font-size: 14px;
  background: transparent;
}

.stats-card :deep(.el-descriptions__content) {
  color: #eaf5ff !important;
  font-weight: 700;
  font-size: 16px;
}

.stats-card :deep(.el-descriptions__border) {
  border: none !important;
}

.stats-card :deep(.el-descriptions__cell) {
  border: none !important;
  padding: 8px 12px !important;
}

/* 目标列表表格样式 */
.targets-card :deep(.el-table) {
  background: transparent;
}

.targets-card :deep(.el-table__header) {
  background: transparent;
}

.targets-card :deep(.el-table th) {
  color: #a0c8e8 !important;
  font-weight: 600;
  font-size: 14px;
}

.targets-card :deep(.el-table td) {
  color: #eaf5ff !important;
  font-size: 14px;
}

.targets-card :deep(.el-table__row:hover) {
  background: rgba(89, 214, 255, 0.1) !important;
}

.targets-card :deep(.el-table__border) {
  border: none !important;
}

/* 自定义按钮样式 */
.yolo-detection-page :deep(.el-button) {
  border-radius: 12px !important;
  font-family: var(--font-family) !important;
  font-weight: 500 !important;
  transition: all 0.3s ease !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

.yolo-detection-page :deep(.el-button--primary),
.yolo-detection-page :deep(.el-button--success),
.yolo-detection-page :deep(.el-button--danger) {
  background: var(--primary-color) !important;
  border-color: var(--primary-color) !important;
  color: white !important;
}

.yolo-detection-page :deep(.el-button--default) {
  background: rgba(255, 255, 255, 0.05) !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
  color: var(--text-primary) !important;
}

.yolo-detection-page :deep(.el-button:disabled) {
  background: rgba(255, 255, 255, 0.05) !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
  color: var(--text-tertiary) !important;
  cursor: not-allowed !important;
}

/* 自定义输入数字组件样式 */
.yolo-detection-page :deep(.el-input-number) {
  background: rgba(255, 255, 255, 0.05) !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
}

.yolo-detection-page :deep(.el-input-number__decrease),
.yolo-detection-page :deep(.el-input-number__increase) {
  background: transparent !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
  color: var(--text-secondary);
}

.yolo-detection-page :deep(.el-input-number__decrease:hover),
.yolo-detection-page :deep(.el-input-number__increase:hover) {
  background: rgba(255, 255, 255, 0.1) !important;
  color: var(--text-primary);
  border-color: rgba(255, 255, 255, 0.2) !important;
}

.yolo-detection-page :deep(.el-input-number__inner) {
  background: transparent !important;
  color: var(--text-primary);
}
</style>
