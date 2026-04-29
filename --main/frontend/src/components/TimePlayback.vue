<template>
  <div class="timeline-wrap glass-panel">
    <div class="timeline-actions">
      <div class="left">
        <el-button circle type="primary" @click="togglePlay">
          <el-icon><component :is="playing ? 'VideoPause' : 'VideoPlay'" /></el-icon>
        </el-button>
        <strong>{{ currentLabel }}</strong>
      </div>
      <el-segmented v-if="showGranularityToggle" v-model="innerGranularity" :options="granularityOptions" />
    </div>
    <div
      v-if="visibleTickItems.length"
      class="timeline-labels"
      :class="{ dense: visibleTickItems.length > 12 }"
    >
      <span
        v-for="item in visibleTickItems"
        :key="`${item.index}-${item.label}`"
        class="timeline-label"
        :class="{ active: item.index === innerIndex }"
        :style="{ left: `${item.left}%` }"
      >
        {{ item.label }}
      </span>
    </div>
    <el-slider
      v-model="innerIndex"
      :min="0"
      :max="Math.max(options.length - 1, 0)"
      :marks="marks"
      :show-tooltip="false"
    />
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({
  options: {
    type: Array,
    default: () => [],
  },
  modelValue: {
    type: Number,
    default: 0,
  },
  granularity: {
    type: String,
    default: 'day',
  },
  interval: {
    type: Number,
    default: 1500,
  },
  autoplay: {
    type: Boolean,
    default: false,
  },
  showGranularityToggle: {
    type: Boolean,
    default: true,
  },
  showTickLabels: {
    type: Boolean,
    default: false,
  },
  tickLabelMode: {
    type: String,
    default: 'edge',
  },
})

const emit = defineEmits(['update:modelValue', 'update:granularity', 'play-change'])

const innerIndex = ref(props.modelValue)
const innerGranularity = ref(props.granularity)
const playing = ref(false)
let timer = null

const granularityOptions = [
  { label: '按天', value: 'day' },
  { label: '按小时', value: 'hour' },
]

watch(
  () => props.modelValue,
  (value) => {
    const maxIndex = Math.max(props.options.length - 1, 0)
    innerIndex.value = Math.min(Math.max(Number(value || 0), 0), maxIndex)
  },
)

watch(
  () => props.options,
  (value) => {
    const maxIndex = Math.max(value.length - 1, 0)
    if (innerIndex.value > maxIndex) {
      innerIndex.value = maxIndex
    }
  },
  { deep: true },
)

watch(innerIndex, (value) => emit('update:modelValue', value))
watch(innerGranularity, (value) => emit('update:granularity', value))

const currentLabel = computed(() => props.options[innerIndex.value]?.label || '暂无数据')
const visibleTickItems = computed(() => {
  if (!props.showTickLabels || !props.options.length) return []

  const shouldShow = (index) => {
    if (props.tickLabelMode === 'all') return true
    if (props.tickLabelMode === 'none') return false
    return index === 0 || index === props.options.length - 1
  }

  return props.options
    .map((item, index) => ({
      index,
      label: item.shortLabel || item.label,
      left: props.options.length <= 1 ? 50 : (index / (props.options.length - 1)) * 100,
    }))
    .filter((item) => shouldShow(item.index))
})
const marks = computed(() =>
  props.showTickLabels
    ? {}
    : props.options.reduce((accumulator, item, index) => {
    if (index === 0 || index === props.options.length - 1) {
      accumulator[index] = item.shortLabel || item.label
    }
    return accumulator
  }, {}),
)

const startTimer = () => {
  if (playing.value) return
  playing.value = true
  emit('play-change', true)
  timer = window.setInterval(() => {
    if (!props.options.length) return
    innerIndex.value = innerIndex.value >= props.options.length - 1 ? 0 : innerIndex.value + 1
  }, props.interval)
}

const stopTimer = () => {
  playing.value = false
  emit('play-change', false)
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

const togglePlay = () => {
  if (playing.value) {
    stopTimer()
    return
  }
  startTimer()
}

watch(
  () => props.autoplay,
  (value) => {
    if (value) {
      startTimer()
    } else if (playing.value) {
      stopTimer()
    }
  },
  { immediate: true },
)

onBeforeUnmount(stopTimer)
</script>

<style scoped>
.timeline-wrap {
  padding: 14px 18px 18px;
}

.timeline-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.timeline-labels {
  position: relative;
  height: 34px;
  margin: 0 10px 8px;
  pointer-events: none;
}

.timeline-labels.dense {
  height: 52px;
}

.timeline-label {
  position: absolute;
  top: 0;
  transform: translateX(-50%);
  color: var(--text-tertiary);
  font-size: 10px;
  line-height: 1;
  white-space: nowrap;
  transition: color 0.2s ease, transform 0.2s ease;
}

.timeline-label::after {
  content: '';
  position: absolute;
  left: 50%;
  top: 15px;
  width: 1px;
  height: 8px;
  background: var(--line-strong);
  transform: translateX(-50%);
}

.timeline-labels.dense .timeline-label:nth-child(even) {
  top: 18px;
}

.timeline-label.active {
  color: var(--accent-cyan);
  font-weight: 700;
  transform: translateX(-50%) scale(1.04);
}

.timeline-label.active::after {
  background: var(--accent-cyan);
}

.left {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
