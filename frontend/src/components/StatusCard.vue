<template>
  <section class="glass-panel status-card" :class="{ compact }">
    <div class="panel-header">
      <span class="section-title">{{ title }}</span>
      <div v-if="status !== undefined" class="status-badge" :class="statusClass">
        {{ statusText }}
      </div>
    </div>
    <div class="panel-body">
      <slot></slot>
    </div>
  </section>
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
  },
  compact: {
    type: Boolean,
    default: false
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
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  padding: 18px 20px;
}

.status-card.compact {
  padding: 14px 16px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 22px;
  margin-bottom: 16px;
}

.section-title {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 0.03em;
  color: var(--text-primary);
}

.status-badge {
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
}

.status-0 {
  background: rgba(156, 163, 175, 0.8);
}

.status-1 {
  background: linear-gradient(135deg, var(--accent-green), var(--accent-green));
  box-shadow: 0 4px 14px rgba(57, 211, 152, 0.3);
}

.status-2 {
  background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
  box-shadow: 0 4px 14px rgba(89, 214, 255, 0.3);
}

.status-3 {
  background: linear-gradient(135deg, var(--accent-red), #d94646);
  box-shadow: 0 4px 14px rgba(255, 93, 93, 0.3);
}

.panel-body {
  flex: 1;
  min-height: 0;
}
</style>