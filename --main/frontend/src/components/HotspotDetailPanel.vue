<template>
  <GlassPanel title="热点区域" compact>
    <div v-if="hotspot" class="hotspot-grid">
      <div class="hotspot-item">
        <span>区域</span>
        <strong>{{ hotspot.major_country || hotspot.id }}</strong>
      </div>
      <div class="hotspot-item">
        <span>火点数</span>
        <strong>{{ hotspot.fire_count }}</strong>
      </div>
      <div class="hotspot-item">
        <span>平均 FRP</span>
        <strong>{{ hotspot.avg_frp }}</strong>
      </div>
      <div class="hotspot-item">
        <span>最大 FRP</span>
        <strong>{{ hotspot.max_frp }}</strong>
      </div>
      <div class="hotspot-item wide">
        <span>时段</span>
        <strong>{{ formatDateTime(hotspot.time_start) }} - {{ formatDateTime(hotspot.time_end) }}</strong>
      </div>
    </div>
    <p v-else class="muted">点击热点区域查看详情</p>
  </GlassPanel>
</template>

<script setup>
import GlassPanel from './GlassPanel.vue'
import { formatDateTime } from '@/utils/format'

defineProps({
  hotspot: {
    type: Object,
    default: null,
  },
})
</script>

<style scoped>
.hotspot-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.hotspot-item {
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(9, 26, 46, 0.78);
  border: 1px solid rgba(99, 195, 255, 0.12);
}

.hotspot-item span {
  color: var(--text-secondary);
}

.hotspot-item strong {
  display: block;
  margin-top: 8px;
}

.wide {
  grid-column: 1 / -1;
}
</style>
