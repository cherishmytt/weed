<template>
  <div class="page-shell">
    <GlassPanel v-if="authStore.isAdmin" title="数据导入">
      <div class="upload-grid">
        <div class="upload-card">
          <h4>导入 FIRMS 合并 CSV</h4>
          <p>支持一次选择多个 `*_merged.csv` 文件，优先导入最终合并数据。</p>
          <input ref="fireInputRef" type="file" accept=".csv" hidden multiple @change="handleFireImport" />
          <el-button type="primary" @click="fireInputRef?.click()">选择多个 CSV 文件</el-button>
        </div>
        <div class="upload-card">
          <h4>导入国家边界 JSON</h4>
          <p>国家匹配依赖边界数据，只需导入一次即可。</p>
          <input ref="boundaryInputRef" type="file" accept=".json,.geojson" hidden @change="handleBoundaryImport" />
          <el-button @click="boundaryInputRef?.click()">选择边界文件</el-button>
        </div>
      </div>
    </GlassPanel>

    <GlassPanel title="火点查询">
      <div class="filter-grid">
        <el-date-picker
          v-model="filters.dateRange"
          type="daterange"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
        />
        <el-select v-model="filters.area_label" clearable placeholder="区域">
          <el-option v-for="item in areaOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="filters.source_product" clearable placeholder="数据源">
          <el-option v-for="item in sourceProductOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="filters.satellite" clearable placeholder="卫星">
          <el-option v-for="item in satelliteOptions" :key="item" :label="item" :value="item" />
        </el-select>
        <el-select v-model="filters.instrument" clearable placeholder="传感器">
          <el-option v-for="item in instrumentOptions" :key="item" :label="item" :value="item" />
        </el-select>
        <el-select v-model="filters.confidence" clearable placeholder="置信度">
          <el-option label="高(h)" value="h" />
          <el-option label="中(n)" value="n" />
          <el-option label="低(l)" value="l" />
        </el-select>
        <el-select v-model="filters.daynight" clearable placeholder="昼夜">
          <el-option label="白天" value="D" />
          <el-option label="夜间" value="N" />
        </el-select>
        <el-input v-model="filters.country_name" placeholder="国家名称" />
      </div>
      <div class="filter-actions">
        <el-button type="primary" @click="handleSearch">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
        <el-button @click="exportData">导出筛选结果</el-button>
      </div>
    </GlassPanel>

    <GlassPanel title="火点列表">
      <el-table :data="fireRows.items" height="460" @row-click="openFireDetail">
        <el-table-column prop="acq_datetime" label="时间" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.acq_datetime) }}</template>
        </el-table-column>
        <el-table-column prop="area_label" label="区域" width="120">
          <template #default="{ row }">{{ areaLabel(row.area_label) }}</template>
        </el-table-column>
        <el-table-column prop="source_product" label="数据源" min-width="160">
          <template #default="{ row }">{{ sourceProductLabel(row.source_product) }}</template>
        </el-table-column>
        <el-table-column prop="country_name" label="国家" min-width="120" />
        <el-table-column prop="satellite" label="卫星" width="90" />
        <el-table-column prop="confidence" label="置信度" width="90">
          <template #default="{ row }">{{ confidenceLabel(row.confidence) }}</template>
        </el-table-column>
        <el-table-column prop="frp" label="FRP" width="90" />
        <el-table-column label="操作" width="110">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="openFireDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination">
        <el-pagination
          background
          layout="total, prev, pager, next"
          :total="fireRows.total"
          :page-size="pagination.page_size"
          :current-page="pagination.page"
          @current-change="handlePageChange"
        />
      </div>
    </GlassPanel>

    <GlassPanel v-if="authStore.isAdmin" title="导入批次记录">
      <el-table :data="batches" height="360">
        <el-table-column prop="batch_name" label="批次名称" min-width="180" />
        <el-table-column prop="source_type" label="类型" width="140" />
        <el-table-column prop="file_name" label="文件名" min-width="220" />
        <el-table-column prop="record_count" label="记录数" width="110" />
        <el-table-column prop="status" label="状态" width="100" />
        <el-table-column prop="remark" label="说明" min-width="260" />
        <el-table-column prop="import_time" label="导入时间" min-width="180">
          <template #default="{ row }">{{ formatDateTime(row.import_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button link type="danger" @click="removeBatch(row)">删除批次</el-button>
          </template>
        </el-table-column>
      </el-table>
    </GlassPanel>
  </div>
</template>

<script setup>
import dayjs from 'dayjs'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import http from '@/api/http'
import { fireApi, importApi } from '@/api/service'
import GlassPanel from '@/components/GlassPanel.vue'
import { useAuthStore } from '@/stores/auth'
import { AREA_PRESETS, SOURCE_PRODUCT_PRESETS, normalizeOptionList } from '@/utils/fireDataConfig'
import { confidenceLabel, formatDateTime } from '@/utils/format'

const authStore = useAuthStore()
const router = useRouter()
const fireInputRef = ref()
const boundaryInputRef = ref()
const batches = ref([])
const fireRows = reactive({ items: [], total: 0 })
const pagination = reactive({ page: 1, page_size: 20 })
const filterOptions = ref({
  area_labels: [],
  source_products: [],
  satellites: [],
  instruments: [],
})
const filters = reactive({
  dateRange: [],
  area_label: '',
  source_product: '',
  satellite: '',
  instrument: '',
  confidence: '',
  daynight: '',
  country_name: '',
})

const areaOptions = computed(() => normalizeOptionList(filterOptions.value.area_labels, AREA_PRESETS))
const sourceProductOptions = computed(() => normalizeOptionList(filterOptions.value.source_products, SOURCE_PRODUCT_PRESETS))
const satelliteOptions = computed(() => filterOptions.value.satellites || [])
const instrumentOptions = computed(() => filterOptions.value.instruments || [])

const areaLabel = (value) => AREA_PRESETS[value]?.label || value || '--'
const sourceProductLabel = (value) => SOURCE_PRODUCT_PRESETS[value]?.label || value || '--'

const buildQuery = () => ({
  page: pagination.page,
  page_size: pagination.page_size,
  start_date: filters.dateRange?.[0] || undefined,
  end_date: filters.dateRange?.[1] || undefined,
  area_label: filters.area_label || undefined,
  source_product: filters.source_product || undefined,
  satellite: filters.satellite || undefined,
  instrument: filters.instrument || undefined,
  confidence: filters.confidence || undefined,
  daynight: filters.daynight || undefined,
  country_name: filters.country_name || undefined,
})

const loadBatches = async () => {
  batches.value = await importApi.batches()
}

const loadFilterOptions = async () => {
  filterOptions.value = await fireApi.filterOptions()
}

const loadFireList = async () => {
  Object.assign(fireRows, await fireApi.list(buildQuery()))
}

const handleFileImport = async (event, action) => {
  const files = Array.from(event.target.files || [])
  if (!files.length) return
  const formData = new FormData()
  files.forEach((file) => formData.append('files', file))
  const result = await action(formData)
  ElMessage.success(`导入成功，共处理 ${Array.isArray(result) ? result.length : 1} 个文件`)
  await Promise.all([loadBatches(), loadFilterOptions(), loadFireList()])
  event.target.value = ''
}

const handleFireImport = async (event) => handleFileImport(event, importApi.uploadFireCsv)

const handleBoundaryImport = async (event) => {
  const file = event.target.files?.[0]
  if (!file) return
  const formData = new FormData()
  formData.append('file', file)
  await importApi.uploadCountryBoundary(formData)
  ElMessage.success('边界导入成功')
  await loadBatches()
  event.target.value = ''
}

const removeBatch = async (row) => {
  await ElMessageBox.confirm(`确认删除批次 ${row.batch_name} 吗？对应火点数据也会一并删除。`, '提示', { type: 'warning' })
  await importApi.removeBatch(row.id)
  await Promise.all([loadBatches(), loadFilterOptions(), loadFireList()])
}

const resetFilters = () => {
  filters.dateRange = []
  filters.area_label = ''
  filters.source_product = ''
  filters.satellite = ''
  filters.instrument = ''
  filters.confidence = ''
  filters.daynight = ''
  filters.country_name = ''
  pagination.page = 1
  loadFireList()
}

const handleSearch = () => {
  pagination.page = 1
  loadFireList()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadFireList()
}

const openFireDetail = (row) => {
  if (!row?.id) return
  router.push(`/fire-detail/${row.id}`)
}

const exportData = async () => {
  const response = await http.get('/fire/export', {
    params: buildQuery(),
    responseType: 'blob',
  })
  const blob = new Blob([response], { type: 'text/csv;charset=utf-8;' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `fire-points-${dayjs().format('YYYYMMDDHHmmss')}.csv`
  link.click()
  window.URL.revokeObjectURL(url)
}

onMounted(async () => {
  await Promise.all([
    loadFilterOptions(),
    authStore.isAdmin ? loadBatches() : Promise.resolve(),
    loadFireList(),
  ])
})
</script>

<style scoped>
.upload-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.upload-card {
  padding: 20px;
  border-radius: 20px;
  background: var(--bg-elevated);
  border: 1px solid var(--line-soft);
}

.upload-card h4,
.upload-card p {
  margin: 0;
}

.upload-card p {
  margin-top: 10px;
  margin-bottom: 14px;
  color: var(--text-secondary);
  line-height: 1.8;
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.filter-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

@media (max-width: 1200px) {
  .upload-grid,
  .filter-grid {
    grid-template-columns: 1fr;
  }
}
</style>
