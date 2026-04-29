<template>
  <GlassPanel :title="title" compact>
    <div v-if="loading" class="weather-state">天气加载中...</div>
    <div v-else-if="weather" class="weather-grid">
      <div class="weather-item">
        <span>温度</span>
        <strong>{{ formatMetric(weather.temperature_2m, '°C') }}</strong>
      </div>
      <div class="weather-item">
        <span>当前降水</span>
        <strong>{{ formatMetric(weather.precipitation, 'mm') }}</strong>
      </div>
      <div class="weather-item">
        <span>24h降水</span>
        <strong>{{ formatMetric(weather.precipitation_24h, 'mm') }}</strong>
      </div>
      <div class="weather-item">
        <span>风速 / 风向</span>
        <strong>{{ formatWind(weather.wind_speed_10m, weather.wind_direction_10m) }}</strong>
      </div>
    </div>
    <div v-else class="weather-state">{{ emptyText }}</div>
  </GlassPanel>
</template>

<script setup>
import GlassPanel from './GlassPanel.vue'

defineProps({
  title: {
    type: String,
    default: '天气',
  },
  weather: {
    type: Object,
    default: null,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  emptyText: {
    type: String,
    default: '暂无天气数据',
  },
})

const formatMetric = (value, unit) => (value === null || value === undefined ? '--' : `${value}${unit}`)
const formatWind = (speed, direction) => {
  const speedText = speed === null || speed === undefined ? '--' : `${speed}km/h`
  const directionText = direction === null || direction === undefined ? '--' : `${direction}°`
  return `${speedText} / ${directionText}`
}
</script>

<style scoped>
.weather-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.weather-item {
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(9, 26, 46, 0.78);
  border: 1px solid rgba(99, 195, 255, 0.12);
}

.weather-item span,
.weather-state {
  color: var(--text-secondary);
}

.weather-item strong {
  display: block;
  margin-top: 10px;
  font-size: 20px;
}
</style>
