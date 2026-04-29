<template>
  <div class="stat-card glass-panel">
    <div class="stat-badge">
      <el-icon :size="20">
        <component :is="icon" />
      </el-icon>
    </div>
    <div class="stat-content">
      <span class="stat-label">{{ label }}</span>
      <template v-if="loading">
        <span class="stat-loading-line value"></span>
        <span class="stat-loading-line desc"></span>
      </template>
      <template v-else>
        <strong class="stat-value">{{ value }}</strong>
        <span v-if="description" class="stat-desc">{{ description }}</span>
      </template>
    </div>
  </div>
</template>

<script setup>
defineProps({
  label: String,
  value: [String, Number],
  description: String,
  icon: {
    type: [Object, String],
    default: 'DataLine',
  },
  loading: {
    type: Boolean,
    default: false,
  },
})
</script>

<style scoped>
.stat-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 14px;
  min-height: 116px;
  padding: 18px 20px;
  overflow: hidden;
}

.stat-card::after {
  content: '';
  position: absolute;
  inset: auto -20% -60% auto;
  width: 160px;
  height: 160px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(82, 215, 255, 0.18), transparent 70%);
}

.stat-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  border-radius: 16px;
  color: var(--accent-cyan);
  background: linear-gradient(145deg, rgba(10, 43, 74, 0.96), rgba(18, 89, 122, 0.36));
  border: 1px solid rgba(82, 215, 255, 0.22);
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.stat-label,
.stat-desc {
  color: var(--text-secondary);
}

.stat-value {
  font-size: 30px;
  line-height: 1.1;
}

.stat-loading-line {
  display: block;
  border-radius: 999px;
  background: linear-gradient(
    90deg,
    rgba(112, 144, 182, 0.12),
    rgba(135, 190, 240, 0.36),
    rgba(112, 144, 182, 0.12)
  );
  background-size: 200% 100%;
  animation: stat-shimmer 1.4s linear infinite;
}

.stat-loading-line.value {
  width: 116px;
  height: 32px;
}

.stat-loading-line.desc {
  width: 82px;
  height: 14px;
  margin-top: 8px;
}

@keyframes stat-shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>
