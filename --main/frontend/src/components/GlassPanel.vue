<template>
  <section class="glass-panel panel" :class="{ compact }">
    <div v-if="title || $slots.header || $slots.extra" class="panel-header">
      <slot name="header">
        <h3 v-if="title" class="section-title">{{ title }}</h3>
      </slot>
      <slot name="extra" />
    </div>
    <div class="panel-body" :class="{ scrollable }" :aria-busy="loading">
      <slot />
      <transition name="panel-fade">
        <div v-if="loading" class="panel-loading">
          <span class="panel-loading-dot"></span>
          <span>{{ loadingText }}</span>
        </div>
      </transition>
    </div>
  </section>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: '',
  },
  compact: {
    type: Boolean,
    default: false,
  },
  scrollable: {
    type: Boolean,
    default: false,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  loadingText: {
    type: String,
    default: '正在加载中',
  },
})
</script>

<style scoped>
.panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  padding: 18px 20px;
}

.panel.compact {
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

.panel-body {
  position: relative;
  flex: 1;
  min-height: 0;
}

.panel-body.scrollable {
  overflow: auto;
  max-height: 100%;
}

.panel-loading {
  position: absolute;
  inset: 0;
  z-index: 3;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-radius: 16px;
  color: var(--text-secondary);
  background: rgba(4, 14, 24, 0.62);
  backdrop-filter: blur(6px);
}

.panel-loading-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent-cyan), var(--accent-orange));
  box-shadow: 0 0 0 7px rgba(89, 214, 255, 0.12);
  animation: panel-pulse 1.2s ease-in-out infinite;
}

.panel-fade-enter-active,
.panel-fade-leave-active {
  transition: opacity 0.18s ease;
}

.panel-fade-enter-from,
.panel-fade-leave-to {
  opacity: 0;
}

@keyframes panel-pulse {
  0%,
  100% {
    transform: scale(1);
    opacity: 0.82;
  }
  50% {
    transform: scale(1.12);
    opacity: 1;
  }
}
</style>
