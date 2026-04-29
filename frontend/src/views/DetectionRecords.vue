<template>
  <div class="detection-records-page">
    <div class="records-card glass-panel">
      <div class="card-header">
        <h2>视觉检测记录</h2>
      </div>
      <div class="filter-bar">
        <div class="filter-wrapper">
          <el-date-picker
            v-model="dateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            @change="handleDateChange"
            style="width: 100%;"
          />
        </div>
        <div class="filter-buttons">
          <el-button type="primary" @click="handleQuery">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </div>
      </div>

      <div class="table-container">
        <el-table :data="tableData" border v-loading="loading" style="width: 100%;">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="图片预览" width="200">
          <template #default="{ row }">
            <el-image
              :src="row.imageUrl"
              fit="cover"
              :preview-src-list="[row.imageUrl]"
              style="width: 180px; height: 120px; border: 1px solid var(--line-soft); border-radius: var(--radius-sm); background: var(--bg-input);"
            />
          </template>
        </el-table-column>
        <el-table-column prop="weedCount" label="杂草数量" width="100" />
        <el-table-column prop="cropCount" label="作物数量" width="100" />
        <el-table-column prop="inferenceTime" label="推理耗时 ms" width="120" />
        <el-table-column prop="detectedAt" label="检测时间" width="180" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button type="primary" link @click="openDetail(row.id)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
        </el-table>
      </div>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="total"
          @size-change="handleQuery"
          @current-change="handleQuery"
          layout="total, sizes, prev, pager, next, jumper"
        />
      </div>

      <!-- 详情抽屉 -->
      <el-drawer
        v-model="detailDrawerVisible"
        title="检测记录详情"
        size="70%"
      >
        <div v-if="currentDetail" class="detail-content">
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="glass-panel detail-card">
                <div class="card-section-header">原始图像</div>
                <el-image
                  :src="currentDetail.imageUrl"
                  fit="contain"
                  :preview-src-list="[currentDetail.imageUrl]"
                  style="width: 100%; max-height: 300px; border: 1px solid var(--line-soft); border-radius: var(--radius-sm); background: var(--bg-input);"
                />
              </div>
            </el-col>
            <el-col :span="12">
              <div class="glass-panel detail-card">
                <div class="card-section-header">检测结果标注</div>
                <el-image
                  :src="currentDetail.resultUrl"
                  fit="contain"
                  :preview-src-list="[currentDetail.resultUrl]"
                  style="width: 100%; max-height: 300px; border: 1px solid var(--line-soft); border-radius: var(--radius-sm); background: var(--bg-input);"
                />
              </div>
            </el-col>
          </el-row>

          <el-row style="margin-top: 20px;">
            <el-col :span="24">
              <div class="glass-panel detail-card">
                <div class="card-section-header">检测统计</div>
                <el-descriptions :column="4" border>
                  <el-descriptions-item label="杂草数量">{{ currentDetail.weedCount }}</el-descriptions-item>
                  <el-descriptions-item label="作物数量">{{ currentDetail.cropCount }}</el-descriptions-item>
                  <el-descriptions-item label="推理耗时">{{ currentDetail.inferenceTime }} ms</el-descriptions-item>
                  <el-descriptions-item label="检测时间">{{ currentDetail.detectedAt }}</el-descriptions-item>
                </el-descriptions>
              </div>
            </el-col>
          </el-row>

          <el-row style="margin-top: 20px;" v-if="currentDetail.detections && currentDetail.detections.length > 0">
            <el-col :span="24">
              <div class="glass-panel detail-card">
                <div class="card-section-header">检测目标列表 (共 {{ currentDetail.detections.length }} 个目标)</div>
                <div class="detail-table-container">
                  <el-table :data="currentDetail.detections" border max-height="400" style="width: 100%;">
                  <el-table-column label="类别" width="100">
                    <template #default="{ row }">
                      <el-tag :type="row.classId === 8 || row.class === 'weed' ? 'danger' : 'success'">
                        {{ row.className }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="confidence" label="置信度" width="100">
                    <template #default="{ row }">
                      {{ (row.confidence * 100).toFixed(1) }}%
                    </template>
                  </el-table-column>
                  <el-table-column label="边界框 [x1, y1, x2, y2]" width="200">
                    <template #default="{ row }">
                      <div v-if="row.bbox">[{{ row.bbox.map(num => parseFloat(num).toFixed(1)).join(', ') }}]</div>
                      <div v-else>--</div>
                    </template>
                  </el-table-column>
                  <el-table-column label="茎干坐标" width="180">
                    <template #default="{ row }">
                      <div v-if="row.stem">
                        ({{ parseFloat(row.stem.x).toFixed(1) }}, {{ parseFloat(row.stem.y).toFixed(1) }})
                      </div>
                      <div v-else>--</div>
                    </template>
                  </el-table-column>
                  </el-table>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
      </el-drawer>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getDetectionRecords, getDetectionDetail } from '@/api/detection'

const dateRange = ref([])
const currentPage = ref(1)
const pageSize = ref(10)
const loading = ref(false)
const tableData = ref([])
const total = ref(0)

// 详情抽屉
const detailDrawerVisible = ref(false)
const currentDetail = ref(null)
const loadingDetail = ref(false)

async function handleQuery() {
  loading.value = true
  try {
    let startTime = null
    let endTime = null
    if (dateRange.value && dateRange.value.length === 2) {
      startTime = formatDate(dateRange.value[0])
      endTime = formatDate(dateRange.value[1])
    }
    const res = await getDetectionRecords(startTime, endTime, currentPage.value, pageSize.value)
    if (res.code === 200) {
      tableData.value = res.data.list
      total.value = res.data.total
    }
  } finally {
    loading.value = false
  }
}

function handleDateChange() {
  currentPage.value = 1
}

function resetFilters() {
  dateRange.value = []
  currentPage.value = 1
  handleQuery()
}

function formatDate(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

async function openDetail(id) {
  loadingDetail.value = true
  try {
    const res = await getDetectionDetail(id)
    if (res.code === 200) {
      currentDetail.value = res.data
      detailDrawerVisible.value = true
    }
  } finally {
    loadingDetail.value = false
  }
}

onMounted(() => {
  handleQuery()
})
</script>

<style scoped>
.detection-records-page {
  padding: 20px;
  min-height: 100vh;
  background: var(--app-background);
}

.records-card {
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

.filter-bar {
  margin-bottom: 24px;
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
}

.filter-wrapper {
  flex: 1;
  min-width: 300px;
}

.filter-buttons {
  display: flex;
  gap: 10px;
  align-items: center;
}

.table-container {
  width: 100%;
  overflow-x: auto;
  margin-bottom: 20px;
}

.table-container :deep(.el-table) {
  width: 100% !important;
}

.detail-table-container {
  width: 100%;
  overflow-x: auto;
}

.detail-table-container :deep(.el-table) {
  width: 100% !important;
}

.pagination-wrapper {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
  padding-top: 16px;
  border-top: 1px solid var(--line-soft);
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-card {
  padding: 20px;
  margin-bottom: 20px;
}

.card-section-header {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
  margin-bottom: 15px;
}

/* 检测统计样式 */
.detail-card :deep(.el-descriptions) {
  background: transparent;
}

.detail-card :deep(.el-descriptions__label) {
  color: var(--text-secondary) !important;
  font-weight: 500;
  font-size: 14px;
}

.detail-card :deep(.el-descriptions__content) {
  color: var(--text-primary) !important;
  font-weight: 600;
  font-size: 14px;
}

.detail-card :deep(.el-descriptions__border) {
  border-color: var(--line-soft) !important;
}

.detail-card :deep(.el-descriptions__cell) {
  border-color: var(--line-soft) !important;
}

/* 重置按钮样式 */
.filter-buttons :deep(.el-button:not(.el-button--primary)) {
  background: rgba(255, 255, 255, 0.05) !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
  color: var(--text-primary) !important;
}

.filter-buttons :deep(.el-button:not(.el-button--primary):hover) {
  background: rgba(255, 255, 255, 0.1) !important;
  border-color: var(--primary-color) !important;
  color: var(--text-primary) !important;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .detection-records-page {
    padding: 10px;
  }

  .filter-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-bar .el-date-picker {
    width: 100% !important;
  }
}
</style>
