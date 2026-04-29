<template>
  <Teleport to="body">
    <transition name="fade-overlay">
      <div v-if="visible" class="loading-overlay">
        <div class="loading-card">
          <span class="loading-dot"></span>
          <div class="loading-copy">
            <strong>{{ title }}</strong>
            <small>{{ description }}</small>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: '正在加载中',
  },
  description: {
    type: String,
    default: '预计 3-6 秒',
  },
})
</script>

<style scoped>
.loading-overlay {
  position: fixed;
  inset: 0;
  z-index: 3000;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.loading-card {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 240px;
  max-width: 360px;
  padding: 14px 18px;
  border-radius: 18px;
  border: 1px solid rgba(99, 195, 255, 0.18);
  background: rgba(6, 18, 30, 0.94);
  box-shadow: 0 18px 36px rgba(0, 0, 0, 0.32);
  backdrop-filter: blur(18px);
}

.loading-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent-cyan), var(--accent-orange));
  box-shadow: 0 0 0 8px rgba(89, 214, 255, 0.1);
  animation: pulse 1.2s ease-in-out infinite;
}

.loading-copy {
  display: grid;
  gap: 4px;
}

.loading-copy small {
  color: var(--text-secondary);
}

.fade-overlay-enter-active,
.fade-overlay-leave-active {
  transition: opacity 0.2s ease;
}

.fade-overlay-enter-from,
.fade-overlay-leave-to {
  opacity: 0;
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
    opacity: 0.8;
  }
  50% {
    transform: scale(1.15);
    opacity: 1;
  }
}
</style>
