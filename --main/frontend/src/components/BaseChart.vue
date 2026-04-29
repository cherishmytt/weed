<template>
  <div class="chart-shell" :style="{ height: `${height}px`, minHeight: `${height}px` }">
    <div ref="chartRef" class="chart-box"></div>
    <transition name="chart-fade">
      <div v-if="loading" class="chart-loading">
        <span class="chart-loading-dot"></span>
        <span>{{ loadingText }}</span>
      </div>
    </transition>
  </div>
</template>

<script setup>
import * as echarts from 'echarts'
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  option: {
    type: Object,
    required: true,
  },
  height: {
    type: Number,
    default: 320,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  loadingText: {
    type: String,
    default: '图表加载中',
  },
})

const emit = defineEmits(['chart-click'])

const chartRef = ref()
let chartInstance
let resizeObserver

const renderChart = async () => {
  await nextTick()
  if (!chartRef.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
    chartInstance.on('click', (params) => emit('chart-click', params))
  }
  chartInstance.resize()
  chartInstance.setOption(props.option, true)
  chartInstance.resize()
}

onMounted(() => {
  renderChart()
  window.addEventListener('resize', renderChart)
  if (typeof ResizeObserver !== 'undefined' && chartRef.value) {
    resizeObserver = new ResizeObserver(() => renderChart())
    resizeObserver.observe(chartRef.value)
  }
})

watch(
  () => props.option,
  () => renderChart(),
  { deep: true },
)

watch(
  () => props.height,
  () => renderChart(),
)

watch(
  () => props.loading,
  (value) => {
    if (!value) {
      renderChart()
    }
  },
)

onBeforeUnmount(() => {
  window.removeEventListener('resize', renderChart)
  resizeObserver?.disconnect()
  chartInstance?.dispose()
})
</script>

<style scoped>
.chart-shell {
  position: relative;
  width: 100%;
}

.chart-box {
  width: 100%;
  height: 100%;
  min-height: inherit;
}

.chart-loading {
  position: absolute;
  inset: 0;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: var(--text-secondary);
  background: rgba(4, 14, 24, 0.62);
  backdrop-filter: blur(6px);
}

.chart-loading-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent-cyan), var(--accent-orange));
  box-shadow: 0 0 0 7px rgba(89, 214, 255, 0.12);
  animation: chart-pulse 1.2s ease-in-out infinite;
}

.chart-fade-enter-active,
.chart-fade-leave-active {
  transition: opacity 0.18s ease;
}

.chart-fade-enter-from,
.chart-fade-leave-to {
  opacity: 0;
}

@keyframes chart-pulse {
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
