<template>
  <div class="laser-logs-container">
  <div class="main-card glass-panel">
    <div class="card-header">
      <div class="header-title">
        <span>激光操作日志</span>
        <span v-if="selectedIds.size > 0" class="selected-count">(已选择 {{ selectedIds.size }} 条)</span>
      </div>
      <div class="header-actions">
        <el-button type="success" size="small" @click="exportSelected">
          <el-icon><Download /></el-icon>
          导出选中
        </el-button>
        <el-button type="primary" size="small" @click="exportAll">
          <el-icon><Download /></el-icon>
          导出全部
        </el-button>
        <el-button type="danger" size="small" @click="batchDelete">
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
        <el-divider direction="vertical" />
        <el-button type="primary" size="small" @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回控制
        </el-button>
      </div>
    </div>

    <!-- 搜索筛选区域 -->
    <div class="filter-area">
      <!-- 快捷时间选项 -->
      <div class="quick-time">
        <span class="label">快捷筛选：</span>
        <el-button-group>
          <el-button size="small" :type="quickTime === 'today' ? 'primary' : ''" @click="setQuickTime('today')">今天</el-button>
          <el-button size="small" :type="quickTime === 'yesterday' ? 'primary' : ''" @click="setQuickTime('yesterday')">昨天</el-button>
          <el-button size="small" :type="quickTime === 'week' ? 'primary' : ''" @click="setQuickTime('week')">近7天</el-button>
          <el-button size="small" :type="quickTime === 'month' ? 'primary' : ''" @click="setQuickTime('month')">近30天</el-button>
        </el-button-group>
      </div>

      <el-row :gutter="16" class="filter-row">
        <el-col :span="8">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
            placeholder="选择时间范围"
            style="width: 100%;"
          />
        </el-col>
        <el-col :span="4">
          <el-select v-model="filters.action" placeholder="指令类型" multiple clearable style="width: 100%;">
            <el-option label="ENABLE" value="ENABLE" />
            <el-option label="DISABLE" value="DISABLE" />
            <el-option label="FIRE" value="FIRE" />
            <el-option label="STOP" value="STOP" />
            <el-option label="SET_POWER" value="SET_POWER" />
            <el-option label="AIM" value="AIM" />
            <el-option label="SELF_TEST" value="SELF_TEST" />
            <el-option label="RESET" value="RESET" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filters.result" placeholder="执行结果" multiple clearable style="width: 100%;">
            <el-option label="成功" value="SUCCESS" />
            <el-option label="失败" value="FAILED" />
            <el-option label="警告" value="WARNING" />
            <el-option label="待执行" value="PENDING" />
          </el-select>
        </el-col>
        <el-col :span="8">
          <el-input v-model="filters.keyword" placeholder="关键词搜索（说明）" clearable style="width: 100%;">
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
      </el-row>

      <el-row :gutter="16" class="filter-row">
        <el-col :span="4">
          <el-range-input
            v-model="filters.targetXRange"
            placeholder="Target X 范围"
            style="width: 100%;"
          />
        </el-col>
        <el-col :span="4">
          <el-range-input
            v-model="filters.targetYRange"
            placeholder="Target Y 范围"
            style="width: 100%;"
          />
        </el-col>
        <el-col :span="4">
          <el-range-input
            v-model="filters.depthRange"
            placeholder="深度范围 (m)"
            style="width: 100%;"
          />
        </el-col>
        <el-col :span="4">
          <el-range-input
            v-model="filters.durationRange"
            placeholder="时长范围 (ms)"
            style="width: 100%;"
          />
        </el-col>
        <el-col :span="8">
          <div class="filter-buttons">
            <el-button type="primary" @click="loadLogs" :loading="loadingLogs">
              <el-icon><Search /></el-icon>
              查询
            </el-button>
            <el-button @click="resetFilters">
              <el-icon><RefreshLeft /></el-icon>
              重置
            </el-button>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 日志表格 -->
    <div class="log-table-container">
      <el-table
        :data="tableData"
        border
        v-loading="loadingLogs"
        stripe
        height="100%"
        width="100%"
        @selection-change="handleSelectionChange"
        @row-click="handleRowClick"
        @sort-change="handleSortChange"
        :default-sort="{ prop: 'createdAt', order: 'descending' }"
        :sort-method="() => 0"
      >
        <el-table-column type="selection" width="50" fixed />
        <el-table-column prop="id" label="ID" width="60" fixed align="center" sortable />
        <el-table-column prop="action" label="指令" width="100" fixed>
          <template #default="{ row }">
            <el-tag :type="getActionTagType(row.action)" size="small">{{ row.action }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="targetCoord" label="目标坐标" width="150" sortable>
          <template #default="{ row }">
            <span v-if="row.targetX !== null && row.targetY !== null">({{ formatNumber(row.targetX) }}, {{ formatNumber(row.targetY) }})</span>
            <span v-else>--</span>
          </template>
        </el-table-column>
        <el-table-column prop="depth" label="深度 m" width="90" align="right" sortable>
          <template #default="{ row }">
            {{ formatNumber(row.depth) }}
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="时长 ms" width="90" align="right" sortable>
          <template #default="{ row }">
            <el-tooltip v-if="row.duration" content="{{ (row.duration / 1000).toFixed(2) }} 秒" placement="top">
              <span>{{ row.duration }}</span>
            </el-tooltip>
            <span v-else>--</span>
          </template>
        </el-table-column>
        <el-table-column prop="result" label="结果" width="100">
          <template #default="{ row }">
            <el-tag :type="getResultTagType(row.result)" size="small">
              {{ getResultLabel(row.result) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="说明" min-width="180">
          <template #default="{ row }">
            <el-tooltip v-if="row.message && row.message.length > 30" :content="row.message" placement="top">
              <span class="ellipsis">{{ row.message }}</span>
            </el-tooltip>
            <span v-else>{{ row.message || '--' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="执行时间" width="170" fixed="right" sortable />
      </el-table>
    </div>

    <!-- 分页 -->
    <div class="pagination-wrapper">
      <el-pagination
        :current-page="currentPage"
        :page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        layout="total, sizes, prev, pager, next, jumper"
      />
    </div>
  </div>

  <!-- 日志详情弹窗 -->
  <el-dialog
    v-model="detailDialogVisible"
    title="日志详情"
    width="600px"
    :close-on-click-modal="false"
    center
    teleport="body"
  >
    <el-descriptions :column="1" border v-if="currentLog">
      <el-descriptions-item label="ID">{{ currentLog.id }}</el-descriptions-item>
      <el-descriptions-item label="指令ID">{{ currentLog.commandId }}</el-descriptions-item>
      <el-descriptions-item label="指令类型">
        <el-tag :type="getActionTagType(currentLog.action)">{{ currentLog.action }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="目标坐标">
        <span v-if="currentLog.targetX !== null && currentLog.targetY !== null">
          ({{ formatNumber(currentLog.targetX) }}, {{ formatNumber(currentLog.targetY) }})
        </span>
        <span v-else>--</span>
      </el-descriptions-item>
      <el-descriptions-item label="深度">{{ formatNumber(currentLog.depth) }} m</el-descriptions-item>
      <el-descriptions-item label="时长">
        <span v-if="currentLog.duration">{{ currentLog.duration }} ms ({{ (currentLog.duration / 1000).toFixed(2) }} s)</span>
        <span v-else>--</span>
      </el-descriptions-item>
      <el-descriptions-item label="执行结果">
        <el-tag :type="getResultTagType(currentLog.result)">{{ getResultLabel(currentLog.result) }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="执行时间">{{ currentLog.createdAt }}</el-descriptions-item>
      <el-descriptions-item label="说明">
        <pre class="message-pre">{{ currentLog.message || '--' }}</pre>
      </el-descriptions-item>
    </el-descriptions>
    <template #footer>
      <el-button @click="detailDialogVisible = false">关闭</el-button>
    </template>
  </el-dialog>
</div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { List, Search, RefreshLeft, ArrowLeft, Download, Delete } from '@element-plus/icons-vue'
import { getLaserLogs, exportLaserLogs, batchDeleteLogs } from '@/api/laser'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

const loadingLogs = ref(false)
const tableData = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const dateRange = ref([])
const quickTime = ref('')
const isFirstLoad = ref(true)

const filters = ref({
  action: [],
  result: [],
  keyword: '',
  targetXRange: [],
  targetYRange: [],
  depthRange: [],
  durationRange: []
})

const selectedIds = ref(new Set())
const selectedRows = ref([])

const sortProp = ref('createdAt')
const sortOrder = ref('descending')

const detailDialogVisible = ref(false)
const currentLog = ref(null)

const router = useRouter()
const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

function goBack() {
  router.push('/laser')
}

function setQuickTime(type) {
  const now = new Date()
  let start, end

  switch (type) {
    case 'today':
      start = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0)
      end = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59)
      quickTime.value = 'today'
      break
    case 'yesterday':
      start = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1, 0, 0, 0)
      end = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1, 23, 59, 59)
      quickTime.value = 'yesterday'
      break
    case 'week':
      start = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
      end = now
      quickTime.value = 'week'
      break
    case 'month':
      start = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
      end = now
      quickTime.value = 'month'
      break
  }

  dateRange.value = [
    formatDateForPicker(start),
    formatDateForPicker(end)
  ]
}

function formatDateForPicker(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

async function loadLogs() {
  loadingLogs.value = true
  try {
    const params = {
      action: filters.value.action.length > 0 ? filters.value.action : null,
      result: filters.value.result.length > 0 ? filters.value.result : null,
      keyword: filters.value.keyword || null,
      targetXMin: filters.value.targetXRange[0] !== undefined ? filters.value.targetXRange[0] : null,
      targetXMax: filters.value.targetXRange[1] !== undefined ? filters.value.targetXRange[1] : null,
      targetYMin: filters.value.targetYRange[0] !== undefined ? filters.value.targetYRange[0] : null,
      targetYMax: filters.value.targetYRange[1] !== undefined ? filters.value.targetYRange[1] : null,
      depthMin: filters.value.depthRange[0] !== undefined ? filters.value.depthRange[0] : null,
      depthMax: filters.value.depthRange[1] !== undefined ? filters.value.depthRange[1] : null,
      durationMin: filters.value.durationRange[0] !== undefined ? filters.value.durationRange[0] : null,
      durationMax: filters.value.durationRange[1] !== undefined ? filters.value.durationRange[1] : null,
      sortBy: sortProp.value,
      sortOrder: sortOrder.value,
      page: currentPage.value,
      size: pageSize.value
    }
    if (dateRange.value && dateRange.value.length === 2) {
      params.startTime = dateRange.value[0]
      params.endTime = dateRange.value[1]
    }

    const res = await getLaserLogs(params)
    if (res.code === 200) {
      tableData.value = res.data.list
      total.value = res.data.total
      if (!isFirstLoad.value) {
        ElMessage.success(`查询完成，共找到 ${res.data.total} 条日志`)
      } else {
        isFirstLoad.value = false
      }
    }
  } catch (error) {
    if (!isFirstLoad.value) {
      ElMessage.error('查询失败，请稍后重试')
    } else {
      isFirstLoad.value = false
    }
  } finally {
    loadingLogs.value = false
  }
}

function resetFilters() {
  quickTime.value = ''
  dateRange.value = []
  filters.value = {
    action: [],
    result: [],
    keyword: '',
    targetXRange: [],
    targetYRange: [],
    depthRange: [],
    durationRange: []
  }
  selectedIds.value.clear()
  currentPage.value = 1
  loadLogs()
}

function handleSizeChange(size) {
  pageSize.value = size
  currentPage.value = 1
  loadLogs()
}

function handleCurrentChange(page) {
  currentPage.value = page
  loadLogs()
}

function handleSelectionChange(selection) {
  selectedIds.value = new Set(selection.map(row => row.id))
  selectedRows.value = selection
}

function handleRowClick(row) {
  currentLog.value = row
  detailDialogVisible.value = true
}

function handleSortChange({ column, prop, order }) {
  sortProp.value = prop
  sortOrder.value = order || 'descending'
  currentPage.value = 1
  loadLogs()
}

function formatNumber(num) {
  if (num === null || num === undefined) return '--'
  return Number(num).toFixed(2)
}

function getActionTagType(action) {
  const colorMap = {
    'ENABLE': 'success',
    'DISABLE': 'info',
    'FIRE': 'danger',
    'STOP': 'warning',
    'AIM': 'primary',
    'SET_POWER': '',
    'SELF_TEST': '',
    'RESET': ''
  }
  return colorMap[action] || 'info'
}

function getResultTagType(result) {
  const typeMap = {
    'SUCCESS': 'success',
    'FAILED': 'danger',
    'WARNING': 'warning',
    'PENDING': 'info'
  }
  return typeMap[result] || 'info'
}

function getResultLabel(result) {
  const labelMap = {
    'SUCCESS': '成功',
    'FAILED': '失败',
    'WARNING': '警告',
    'PENDING': '待执行'
  }
  return labelMap[result] || result
}

async function exportSelected() {
  if (selectedIds.value.size === 0) {
    ElMessage.warning('请先选择要导出的日志')
    return
  }
  await exportCsv(Array.from(selectedIds.value))
}

async function exportAll() {
  try {
    loadingLogs.value = true
    const res = await getLaserLogs({
      ...getCurrentParams(),
      page: 1,
      size: 10000
    })
    if (res.code === 200) {
      const ids = res.data.list.map(item => item.id)
      await exportCsv(ids)
    }
  } finally {
    loadingLogs.value = false
  }
}

async function exportCsv(ids) {
  try {
    const res = await exportLaserLogs(ids)
    if (res.code === 200) {
      const csvContent = generateCsv(res.data)
      downloadCsv(csvContent)
      ElMessage.success(`成功导出 ${ids.length} 条记录`)
    }
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

function generateCsv(data) {
  const headers = [
    'ID', '指令ID', '指令类型', 'Target X', 'Target Y', '深度(m)', '时长(ms)',
    '执行结果', '说明', '执行时间'
  ]
  const rows = data.map(log => [
    log.id,
    `"${log.commandId || ''}"`,
    `"${log.action || ''}"`,
    log.targetX,
    log.targetY,
    log.depth,
    log.duration,
    log.result,
    `"${(log.message || '').replace(/"/g, '""')}"`,
    log.createdAt
  ])
  return [headers.join(','), ...rows.map(r => r.join(','))].join('\n')
}

function downloadCsv(content) {
  const blob = new Blob(['\uFEFF' + content], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  const timestamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')
  link.download = `laser-logs-${timestamp}.csv`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function getCurrentParams() {
  const params = {
    action: filters.value.action.length > 0 ? filters.value.action : null,
    result: filters.value.result.length > 0 ? filters.value.result : null,
    keyword: filters.value.keyword || null,
    targetXMin: filters.value.targetXRange[0] !== undefined ? filters.value.targetXRange[0] : null,
    targetXMax: filters.value.targetXRange[1] !== undefined ? filters.value.targetXRange[1] : null,
    targetYMin: filters.value.targetYRange[0] !== undefined ? filters.value.targetYRange[0] : null,
    targetYMax: filters.value.targetYRange[1] !== undefined ? filters.value.targetYRange[1] : null,
    depthMin: filters.value.depthRange[0] !== undefined ? filters.value.depthRange[0] : null,
    depthMax: filters.value.depthRange[1] !== undefined ? filters.value.depthRange[1] : null,
    durationMin: filters.value.durationRange[0] !== undefined ? filters.value.durationRange[0] : null,
    durationMax: filters.value.durationRange[1] !== undefined ? filters.value.durationRange[1] : null,
  }
  if (dateRange.value && dateRange.value.length === 2) {
    params.startTime = dateRange.value[0]
    params.endTime = dateRange.value[1]
  }
  return params
}

async function batchDelete() {
  if (selectedIds.value.size === 0) {
    ElMessage.warning('请先选择要删除的日志')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedIds.value.size} 条日志吗？此操作不可撤销。`,
      '确认批量删除',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    const ids = Array.from(selectedIds.value)
    const res = await batchDeleteLogs(ids)
    if (res.code === 200) {
      ElMessage.success(`成功删除 ${ids.length} 条日志`)
      selectedIds.value.clear()
      loadLogs()
    }
  } catch {
  }
}

onMounted(() => {
  loadLogs()
})
</script>

<style scoped>
.laser-logs-container {
}

.main-card {
  border-radius: var(--radius-lg);
  overflow: hidden;
  padding: 24px;
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

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.selected-count {
  font-weight: normal;
  font-size: 14px;
  color: var(--text-secondary);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.log-count {
  font-weight: normal;
  font-size: 14px;
  color: var(--text-secondary);
  margin-left: 8px;
}

.filter-area {
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.quick-time {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.quick-time .label {
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
}

.quick-time :deep(.el-button) {
  background: rgba(255, 255, 255, 0.05) !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
  color: var(--text-primary) !important;
}

.quick-time :deep(.el-button:hover) {
  background: rgba(255, 255, 255, 0.1) !important;
  border-color: var(--primary-color) !important;
  color: var(--text-primary) !important;
}

.quick-time :deep(.el-button--primary) {
  background: rgba(64, 158, 255, 0.3) !important;
  border-color: rgba(64, 158, 255, 0.5) !important;
  color: white !important;
  backdrop-filter: blur(10px) !important;
}

.quick-time :deep(.el-button--primary:hover) {
  background: rgba(64, 158, 255, 0.4) !important;
  border-color: rgba(64, 158, 255, 0.6) !important;
  color: white !important;
}

.filter-row {
  margin-bottom: 16px;
}

.filter-label {
  font-size: 12px;
  color: var(--text-secondary);
  text-align: center;
  margin-top: 4px;
}

.filter-buttons {
  display: flex;
  gap: 10px;
  justify-content: flex-start;
  height: 32px;
  align-items: flex-end;
}

.log-table-container {
  width: 100%;
  overflow-x: auto;
}

.log-table-container :deep(.el-table) {
  width: 100% !important;
}

.ellipsis {
  display: block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pagination-wrapper {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
  padding-top: 16px;
  border-top: 1px solid var(--line-soft);
}

.message-pre {
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  font-family: inherit;
  font-size: inherit;
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.05);
  padding: 12px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

</style>