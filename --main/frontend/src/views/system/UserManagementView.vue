<template>
  <div class="page-shell user-page">
    <div class="viewport-wrap">
      <section class="viewport-panel hero-panel" :class="{ hidden: viewMode === 'detail' }">
        <section class="stat-grid">
          <StatCard label="用户总数" :value="summary.total" :loading="loading" description="当前系统账号" icon="UserFilled" />
          <StatCard label="管理员" :value="summary.admin" :loading="loading" description="具备管理权限" icon="Lock" />
          <StatCard label="查看用户" :value="summary.viewer" :loading="loading" description="只读访问角色" icon="View" />
          <StatCard label="停用账号" :value="summary.disabled" :loading="loading" description="已禁用账号" icon="CircleCloseFilled" />
        </section>

        <GlassPanel title="用户管理" class="table-panel" :loading="loading" loading-text="用户列表加载中">
          <template #extra>
            <el-button type="primary" @click="openCreateDialog">新增用户</el-button>
          </template>
          <el-table :data="users" height="100%">
            <el-table-column prop="username" label="用户名" min-width="140" />
            <el-table-column prop="email" label="邮箱" min-width="220" />
            <el-table-column prop="role" label="角色" width="120" />
            <el-table-column prop="status" label="状态" width="120" />
            <el-table-column prop="created_at" label="创建时间" min-width="180">
              <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="220">
              <template #default="{ row }">
                <el-button link type="primary" @click="openEditDialog(row)">编辑</el-button>
                <el-button link type="danger" @click="removeUser(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </GlassPanel>

        <button class="view-toggle down" @click="viewMode = 'detail'">
          <el-icon><ArrowDownBold /></el-icon>
          <span>下探分析</span>
        </button>
      </section>

      <section class="viewport-panel detail-panel" :class="{ hidden: viewMode === 'map' }">
        <div class="detail-grid">
          <GlassPanel title="角色分布" :loading="loading" loading-text="角色分布加载中">
            <BaseChart :option="roleOption" :height="220" :loading="loading" loading-text="角色分布加载中" />
          </GlassPanel>

          <GlassPanel title="账号状态" :loading="loading" loading-text="账号状态加载中">
            <BaseChart :option="statusOption" :height="220" :loading="loading" loading-text="账号状态加载中" />
          </GlassPanel>

          <GlassPanel title="最近创建" scrollable :loading="loading" loading-text="最近创建加载中">
            <div class="recent-list">
              <article v-for="item in recentUsers" :key="item.id">
                <div>
                  <strong>{{ item.username }}</strong>
                  <span>{{ item.role }}</span>
                </div>
                <p>{{ formatDateTime(item.created_at) }}</p>
              </article>
            </div>
          </GlassPanel>

          <GlassPanel title="管理摘要" scrollable :loading="loading" loading-text="管理摘要加载中">
            <div class="summary-list">
              <article v-for="item in managementSummary" :key="item.label">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </article>
            </div>
          </GlassPanel>
        </div>

        <button class="view-toggle up" @click="viewMode = 'map'">
          <el-icon><ArrowUpBold /></el-icon>
          <span>返回管理</span>
        </button>
      </section>
    </div>

    <el-dialog v-model="dialogVisible" :title="dialogMode === 'create' ? '新增用户' : '编辑用户'" width="420px">
      <el-form :model="form" label-position="top">
        <el-form-item label="用户名">
          <el-input v-model="form.username" :disabled="dialogMode === 'edit'" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role">
            <el-option label="admin" value="admin" />
            <el-option label="viewer" value="viewer" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status">
            <el-option label="active" value="active" />
            <el-option label="disabled" value="disabled" />
          </el-select>
        </el-form-item>
        <el-form-item :label="dialogMode === 'create' ? '密码' : '重置密码（可选）'">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ArrowDownBold, ArrowUpBold } from '@element-plus/icons-vue'
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { userApi } from '@/api/service'
import BaseChart from '@/components/BaseChart.vue'
import GlassPanel from '@/components/GlassPanel.vue'
import StatCard from '@/components/StatCard.vue'
import { formatDateTime } from '@/utils/format'

const users = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogMode = ref('create')
const currentId = ref(null)
const viewMode = ref('map')

const initialForm = () => ({
  username: '',
  email: '',
  role: 'viewer',
  status: 'active',
  password: '',
})

const form = reactive(initialForm())

const loadUsers = async () => {
  loading.value = true
  try {
    users.value = await userApi.list()
  } finally {
    loading.value = false
  }
}

const summary = computed(() => {
  const total = users.value.length
  const admin = users.value.filter((item) => item.role === 'admin').length
  const viewer = users.value.filter((item) => item.role === 'viewer').length
  const disabled = users.value.filter((item) => item.status === 'disabled').length
  return { total, admin, viewer, disabled }
})

const recentUsers = computed(() =>
  [...users.value]
    .sort((a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime())
    .slice(0, 8),
)

const managementSummary = computed(() => [
  { label: '活跃账号', value: summary.value.total - summary.value.disabled },
  { label: '停用账号', value: summary.value.disabled },
  { label: '管理员占比', value: summary.value.total ? `${((summary.value.admin / summary.value.total) * 100).toFixed(1)}%` : '--' },
  { label: '查看用户占比', value: summary.value.total ? `${((summary.value.viewer / summary.value.total) * 100).toFixed(1)}%` : '--' },
])

const roleOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: {
    bottom: 0,
    textStyle: { color: '#d7e6ff' },
  },
  series: [
    {
      type: 'pie',
      radius: ['42%', '68%'],
      center: ['50%', '46%'],
      itemStyle: {
        borderRadius: 10,
        borderColor: 'rgba(6, 11, 18, 0.9)',
        borderWidth: 4,
      },
      label: {
        color: '#d7e6ff',
        formatter: '{b}\n{c}',
      },
      data: [
        { name: 'admin', value: summary.value.admin, itemStyle: { color: '#59e3ff' } },
        { name: 'viewer', value: summary.value.viewer, itemStyle: { color: '#ff9b5c' } },
      ],
    },
  ],
}))

const statusOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  xAxis: {
    type: 'category',
    data: ['active', 'disabled'],
    axisLabel: { color: '#c7d6ee' },
    axisLine: { lineStyle: { color: 'rgba(120, 162, 214, 0.28)' } },
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: 'rgba(120, 162, 214, 0.14)' } },
    axisLabel: { color: '#8ea2c7' },
  },
  grid: { left: 46, right: 18, top: 24, bottom: 34 },
  series: [
    {
      type: 'bar',
      barWidth: 34,
      data: [
        {
          value: summary.value.total - summary.value.disabled,
          itemStyle: { color: '#3b82f6', borderRadius: [10, 10, 0, 0] },
        },
        {
          value: summary.value.disabled,
          itemStyle: { color: '#ff6a66', borderRadius: [10, 10, 0, 0] },
        },
      ],
    },
  ],
}))

const resetForm = () => Object.assign(form, initialForm())

const openCreateDialog = () => {
  dialogMode.value = 'create'
  currentId.value = null
  resetForm()
  dialogVisible.value = true
}

const openEditDialog = (row) => {
  dialogMode.value = 'edit'
  currentId.value = row.id
  Object.assign(form, {
    username: row.username,
    email: row.email,
    role: row.role,
    status: row.status,
    password: '',
  })
  dialogVisible.value = true
}

const submitForm = async () => {
  if (dialogMode.value === 'create') {
    await userApi.create(form)
  } else {
    await userApi.update(currentId.value, {
      email: form.email,
      role: form.role,
      status: form.status,
      password: form.password || undefined,
    })
  }
  dialogVisible.value = false
  await loadUsers()
  ElMessage.success(dialogMode.value === 'create' ? '用户创建成功' : '用户更新成功')
}

const removeUser = async (row) => {
  await ElMessageBox.confirm(`确认删除用户 ${row.username} 吗？`, '提示', { type: 'warning' })
  await userApi.remove(row.id)
  await loadUsers()
  ElMessage.success('用户删除成功')
}

onMounted(loadUsers)
</script>

<style scoped>
.user-page {
  position: relative;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.viewport-wrap {
  position: relative;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.viewport-panel {
  position: absolute;
  inset: 0;
  display: grid;
  min-height: 0;
  transition: transform 0.32s ease, opacity 0.24s ease;
}

.viewport-panel.hidden {
  opacity: 0;
  pointer-events: none;
}

.hero-panel.hidden {
  transform: translateY(-6%);
}

.detail-panel.hidden {
  transform: translateY(6%);
}

.hero-panel {
  grid-template-rows: auto minmax(0, 1fr);
  gap: 18px;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.table-panel :deep(.panel),
.table-panel :deep(.panel-body) {
  height: 100%;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  grid-template-rows: minmax(0, 300px) minmax(0, 1fr);
  gap: 18px;
  min-height: 0;
  padding-top: 44px;
}

.detail-grid > * {
  min-height: 0;
}

.recent-list,
.summary-list {
  display: grid;
  gap: 12px;
}

.recent-list article,
.summary-list article {
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid var(--line-soft);
  background: var(--bg-elevated);
}

.recent-list strong,
.summary-list strong {
  display: block;
}

.recent-list span,
.recent-list p,
.summary-list span {
  color: var(--text-secondary);
}

.recent-list article div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.recent-list p {
  margin: 10px 0 0;
}

.summary-list article {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.view-toggle {
  position: absolute;
  left: 50%;
  z-index: 3;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  color: var(--text-primary);
  border-radius: 999px;
  border: 1px solid var(--line-soft);
  background: rgba(6, 18, 30, 0.9);
  transform: translateX(-50%);
  cursor: pointer;
}

.view-toggle.down {
  bottom: 10px;
}

.view-toggle.up {
  top: 10px;
}

@media (max-width: 1280px) {
  .stat-grid,
  .detail-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .user-page {
    overflow: auto;
  }

  .viewport-wrap {
    height: auto;
    overflow: visible;
  }

  .viewport-panel {
    position: relative;
    inset: auto;
  }

  .stat-grid,
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .view-toggle {
    position: static;
    transform: none;
    justify-self: center;
    margin-top: 12px;
  }
}
</style>
