<template>
  <div class="page-shell sync-page">
    <section class="stat-grid">
      <StatCard label="同步策略" :value="`最近 ${syncWindowDays} 天`" icon="Refresh" />
      <StatCard label="最近状态" :value="latestJob ? statusLabel(latestJob.status) : '暂无记录'" icon="CircleCheckFilled" />
      <StatCard label="最近开始" :value="latestJob ? formatDateTime(latestJob.started_at || latestJob.trigger_time, 'MM-DD HH:mm') : '--'" icon="Clock" />
      <StatCard label="最近耗时" :value="latestJob?.actual_seconds ? formatDuration(latestJob.actual_seconds) : '--'" icon="Timer" />
    </section>

    <GlassPanel title="同步策略" compact>
      <div class="toolbar-grid">
        <div class="toolbar-item">
          <span>区域</span>
          <el-select v-model="filters.areas" multiple collapse-tags collapse-tags-tooltip placeholder="默认全部区域">
            <el-option v-for="item in areaOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </div>
        <div class="toolbar-item">
          <span>数据源</span>
          <el-select v-model="filters.sources" multiple collapse-tags collapse-tags-tooltip placeholder="默认全部数据源">
            <el-option v-for="item in sourceOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </div>
        <div class="toolbar-item wide">
          <span>说明</span>
          <div class="strategy-card">手动触发，同步完成后再清理窗口外旧数据，始终维持最近 {{ syncWindowDays }} 天在线数据。</div>
        </div>
        <div class="toolbar-actions">
          <el-button type="primary" :loading="estimating" @click="openEstimateDialog">开始同步</el-button>
          <el-button @click="loadHistory">刷新</el-button>
        </div>
      </div>
    </GlassPanel>

    <GlassPanel title="最近一次同步">
      <div v-if="latestJob" class="latest-grid">
        <div class="latest-item"><span>任务名</span><strong>{{ latestJob.job_name }}</strong></div>
        <div class="latest-item"><span>状态</span><strong>{{ statusLabel(latestJob.status) }}</strong></div>
        <div class="latest-item"><span>抓取数</span><strong>{{ formatNumber(latestJob.fetched_count) }}</strong></div>
        <div class="latest-item"><span>新增数</span><strong>{{ formatNumber(latestJob.inserted_count) }}</strong></div>
        <div class="latest-item"><span>跳过数</span><strong>{{ formatNumber(latestJob.skipped_count) }}</strong></div>
        <div class="latest-item"><span>删除数</span><strong>{{ formatNumber(latestJob.deleted_count) }}</strong></div>
        <div class="latest-item wide"><span>备注</span><strong>{{ latestJob.message || '--' }}</strong></div>
      </div>
      <el-empty v-else description="暂无同步记录" />
    </GlassPanel>

    <GlassPanel title="同步历史">
      <el-table :data="history" height="420">
        <el-table-column prop="trigger_time" label="触发时间" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.trigger_time) }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="区域" min-width="160">
          <template #default="{ row }">{{ joinLabels(row.target_areas, areaLabelMap) }}</template>
        </el-table-column>
        <el-table-column label="数据源" min-width="180">
          <template #default="{ row }">{{ joinLabels(row.target_sources, sourceLabelMap) }}</template>
        </el-table-column>
        <el-table-column prop="fetched_count" label="抓取数" width="100" />
        <el-table-column prop="inserted_count" label="新增数" width="100" />
        <el-table-column prop="deleted_count" label="删除数" width="100" />
        <el-table-column prop="actual_seconds" label="耗时" width="120">
          <template #default="{ row }">{{ row.actual_seconds ? formatDuration(row.actual_seconds) : '--' }}</template>
        </el-table-column>
        <el-table-column prop="message" label="备注" min-width="220" show-overflow-tooltip />
      </el-table>
    </GlassPanel>

    <el-dialog
      v-model="estimateDialogVisible"
      title="同步确认"
      width="620px"
      destroy-on-close
    >
      <div v-if="estimateData" class="estimate-body">
        <div class="estimate-row">
          <span>处理区域</span>
          <strong>{{ joinLabels(estimateData.areas, areaLabelMap) }}</strong>
        </div>
        <div class="estimate-row">
          <span>处理数据源</span>
          <strong>{{ joinLabels(estimateData.sources, sourceLabelMap) }}</strong>
        </div>
        <div class="estimate-row">
          <span>时间窗口</span>
          <strong>{{ formatDateTime(estimateData.window_start) }} 至 {{ formatDateTime(estimateData.window_end) }}</strong>
        </div>
        <div class="estimate-row">
          <span>同步策略</span>
          <strong>{{ estimateData.strategy }}</strong>
        </div>
        <div class="estimate-row">
          <span>预计耗时</span>
          <strong>{{ estimateData.estimated_text }}</strong>
        </div>
        <div class="estimate-row">
          <span>任务数</span>
          <strong>{{ estimateData.total_tasks }}</strong>
        </div>
      </div>
      <template #footer>
        <el-button @click="estimateDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="startingSync" @click="startSync">确认开始</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="progressDialogVisible"
      title="同步中"
      width="660px"
      :show-close="!isJobActive"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <div v-if="activeJob" class="progress-body">
        <div class="progress-row">
          <span>当前状态</span>
          <strong>{{ statusLabel(activeJob.status) }}</strong>
        </div>
        <div class="progress-row">
          <span>当前步骤</span>
          <strong>{{ activeJob.current_step || '--' }}</strong>
        </div>
        <div class="progress-row">
          <span>当前目标</span>
          <strong>{{ activeJob.current_target || '--' }}</strong>
        </div>
        <div class="progress-row">
          <span>任务进度</span>
          <strong>{{ activeJob.completed_tasks }} / {{ activeJob.total_tasks }}</strong>
        </div>
        <el-progress :percentage="progressPercent" :stroke-width="14" :show-text="false" />
        <div class="progress-stats">
          <article><span>抓取</span><strong>{{ formatNumber(activeJob.fetched_count) }}</strong></article>
          <article><span>新增</span><strong>{{ formatNumber(activeJob.inserted_count) }}</strong></article>
          <article><span>跳过</span><strong>{{ formatNumber(activeJob.skipped_count) }}</strong></article>
          <article><span>删除</span><strong>{{ formatNumber(activeJob.deleted_count) }}</strong></article>
        </div>
        <div class="progress-row">
          <span>预计剩余</span>
          <strong>{{ remainingText }}</strong>
        </div>
        <p class="progress-tip">同步进行中，请耐心等待，避免频繁重复触发。</p>
      </div>
      <template #footer>
        <el-button v-if="!isJobActive" type="primary" @click="closeProgressDialog">我知道了</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { syncApi } from '@/api/service'
import GlassPanel from '@/components/GlassPanel.vue'
import StatCard from '@/components/StatCard.vue'
import { AREA_PRESETS, SOURCE_PRODUCT_PRESETS } from '@/utils/fireDataConfig'
import { formatDateTime, formatNumber } from '@/utils/format'

const syncWindowDays = 30
const filters = reactive({
  areas: [],
  sources: [],
})

const history = ref([])
const latestJob = ref(null)
const estimateData = ref(null)
const activeJob = ref(null)
const remainingSeconds = ref(null)
const estimateDialogVisible = ref(false)
const progressDialogVisible = ref(false)
const estimating = ref(false)
const startingSync = ref(false)
let pollingTimer = null

const areaOptions = Object.entries(AREA_PRESETS).map(([value, config]) => ({ value, label: config.label }))
const sourceOptions = Object.entries(SOURCE_PRODUCT_PRESETS).map(([value, config]) => ({ value, label: config.label }))

const areaLabelMap = Object.fromEntries(areaOptions.map((item) => [item.value, item.label]))
const sourceLabelMap = Object.fromEntries(sourceOptions.map((item) => [item.value, item.label]))

const isJobActive = computed(() => ['pending', 'running'].includes(activeJob.value?.status))
const progressPercent = computed(() => {
  const total = Number(activeJob.value?.total_tasks || 0)
  const completed = Number(activeJob.value?.completed_tasks || 0)
  if (!total) return 0
  return Math.max(4, Math.min(100, Math.round((completed / total) * 100)))
})
const remainingText = computed(() => {
  if (!isJobActive.value) {
    return activeJob.value?.actual_seconds ? formatDuration(activeJob.value.actual_seconds) : '--'
  }
  const remaining = Number(remainingSeconds.value)
  return Number.isFinite(remaining) ? formatDuration(remaining) : '计算中'
})

const statusLabel = (status) =>
  ({
    pending: '等待启动',
    running: '同步中',
    success: '成功',
    partial_success: '部分成功',
    failed: '失败',
    skipped: '已跳过',
  })[status] || status || '--'

const statusTagType = (status) =>
  ({
    pending: 'info',
    running: 'warning',
    success: 'success',
    partial_success: 'warning',
    failed: 'danger',
  })[status] || 'info'

const formatDuration = (seconds) => {
  const total = Number(seconds || 0)
  if (!Number.isFinite(total) || total <= 0) return '--'
  if (total < 60) return `${total} 秒`
  const minutes = Math.floor(total / 60)
  const remain = total % 60
  return remain ? `${minutes} 分 ${remain} 秒` : `${minutes} 分`
}

const joinLabels = (values = [], labelMap = {}) => {
  const list = Array.isArray(values) ? values : []
  if (!list.length) return '--'
  return list.map((value) => labelMap[value] || value).join('、')
}

const pollStatus = async (jobId) => {
  try {
    const payload = await syncApi.status({ job_id: jobId }, { silent: true })
    activeJob.value = payload.job
    remainingSeconds.value = payload.remaining_seconds
    latestJob.value = payload.job || latestJob.value
    if (!payload.active) {
      stopPolling()
      await loadHistory()
      if (payload.job?.status === 'success') {
        ElMessage.success('同步完成')
      } else if (payload.job?.status === 'partial_success') {
        ElMessage.warning('同步完成，但有部分任务失败')
      } else if (payload.job?.status === 'failed') {
        ElMessage.error(payload.job?.message || '同步失败')
      }
    }
  } catch {
    stopPolling()
  }
}

const startPolling = (jobId) => {
  stopPolling()
  pollingTimer = window.setInterval(() => {
    pollStatus(jobId)
  }, 3000)
}

const stopPolling = () => {
  if (pollingTimer) {
    window.clearInterval(pollingTimer)
    pollingTimer = null
  }
}

const loadHistory = async () => {
  history.value = await syncApi.history({ limit: 20 })
  latestJob.value = history.value[0] || null
}

const openEstimateDialog = async () => {
  estimating.value = true
  try {
    estimateData.value = await syncApi.estimate({
      areas: filters.areas,
      sources: filters.sources,
    })
    estimateDialogVisible.value = true
  } finally {
    estimating.value = false
  }
}

const startSync = async () => {
  startingSync.value = true
  try {
    const job = await syncApi.runNow({
      areas: filters.areas,
      sources: filters.sources,
    })
    estimateDialogVisible.value = false
    activeJob.value = job
    remainingSeconds.value = job.estimated_seconds || null
    progressDialogVisible.value = true
    await loadHistory()
    startPolling(job.id)
  } finally {
    startingSync.value = false
  }
}

const closeProgressDialog = () => {
  if (isJobActive.value) return
  progressDialogVisible.value = false
}

onMounted(async () => {
  await loadHistory()
  if (latestJob.value && ['pending', 'running'].includes(latestJob.value.status)) {
    activeJob.value = latestJob.value
    remainingSeconds.value = latestJob.value.estimated_seconds || null
    progressDialogVisible.value = true
    startPolling(latestJob.value.id)
  }
})

onBeforeUnmount(() => {
  stopPolling()
})
</script>

<style scoped>
.sync-page {
  padding-bottom: 8px;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.toolbar-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.toolbar-item {
  display: grid;
  gap: 8px;
}

.toolbar-item span,
.progress-tip {
  color: var(--text-secondary);
}

.toolbar-item.wide {
  grid-column: 1 / -1;
}

.strategy-card {
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid var(--line-soft);
  background: var(--bg-elevated);
  color: var(--text-primary);
  line-height: 1.8;
}

.toolbar-actions {
  display: flex;
  align-items: end;
  gap: 10px;
}

.latest-grid,
.progress-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.latest-item,
.progress-stats article,
.estimate-row {
  padding: 12px 14px;
  border-radius: 16px;
  border: 1px solid var(--line-soft);
  background: var(--bg-elevated);
}

.latest-item span,
.progress-stats span,
.estimate-row span,
.progress-row span {
  color: var(--text-secondary);
}

.latest-item strong,
.progress-stats strong,
.estimate-row strong,
.progress-row strong {
  display: block;
  margin-top: 8px;
}

.wide {
  grid-column: 1 / -1;
}

.estimate-body,
.progress-body {
  display: grid;
  gap: 12px;
}

.progress-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.progress-tip {
  margin: 0;
}

@media (max-width: 1280px) {
  .stat-grid,
  .toolbar-grid,
  .latest-grid,
  .progress-stats {
    grid-template-columns: 1fr;
  }
}
</style>
