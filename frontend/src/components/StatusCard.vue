<template>
  <el-card class="status-card" :body-style="{ padding: '20px' }">
    <div class="status-card-header">
      <div class="title">{{ title }}</div>
      <div v-if="status !== undefined" class="status-badge" :class="statusClass">
        {{ statusText }}
      </div>
    </div>
    <div class="content">
      <slot></slot>
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  status: {
    type: Number,
    default: undefined
  }
})

const statusText = computed(() => {
  if (props.status === undefined) return ''
  const map = {
    0: '离线',
    1: '待机',
    2: '作业中',
    3: '故障'
  }
  return map[props.status] || '未知'
})

const statusClass = computed(() => {
  return `status-${props.status}`
})
</script>

<style scoped>
.status-card {
  height: 100%;
}

.status-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.status-card-header .title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  color: #fff;
}

.status-0 {
  background-color: #909399;
}

.status-1 {
  background-color: #67c23a;
}

.status-2 {
  background-color: #409eff;
}

.status-3 {
  background-color: #f56c6c;
}

.content {
  min-height: 80px;
}
</style>
