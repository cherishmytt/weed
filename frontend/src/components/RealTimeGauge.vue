<template>
  <div class="gauge-container">
    <div ref="chartRef" :style="{ width: '100%', height: height + 'px' }"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  value: {
    type: Number,
    default: 0
  },
  max: {
    type: Number,
    default: 100
  },
  title: {
    type: String,
    default: ''
  },
  unit: {
    type: String,
    default: ''
  },
  height: {
    type: Number,
    default: 180
  }
})

const chartRef = ref(null)
let chart = null

// 根据数值获取颜色
function getColor(value, max) {
  const percent = value / max
  if (percent < 0.3) return '#67c23a'      // 低电量/低温 绿色
  if (percent < 0.7) return '#e6a23c'      // 中等 橙色
  return '#f56c6c'                          // 高 CPU/高温 红色
}

function initChart() {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)

  const color = getColor(props.value, props.max)

  const option = {
    backgroundColor: 'transparent',
    series: [
      {
        type: 'gauge',
        startAngle: 200,
        endAngle: -20,
        min: 0,
        max: props.max,
        splitNumber: 0,
        radius: '90%',
        center: ['50%', '55%'],
        itemStyle: {
          color: color
        },
        progress: {
          show: true,
          width: 20,
          itemStyle: {
            color: color
          }
        },
        pointer: {
          show: true,
          length: '60%',
          width: 5,
          itemStyle: {
            color: '#303133'
          }
        },
        axisLine: {
          show: true,
          lineStyle: {
            width: 20,
            color: [[1, 'rgba(255, 255, 255, 0.6)']]
          }
        },
        anchor: {
          show: true,
          size: 10,
          itemStyle: {
            color: '#fff',
            borderColor: '#303133'
          }
        },
        axisTick: {
          show: false
        },
        splitLine: {
          show: false
        },
        title: {
          show: false
        },
        detail: {
          show: false
        },
        data: [
          {
            value: props.value
          }
        ]
      }
    ]
  }

  chart.setOption(option)
}

function updateChart() {
  if (!chart) return
  const color = getColor(props.value, props.max)
  chart.setOption({
    series: [
      {
        itemStyle: { color },
        progress: { itemStyle: { color } },
        data: [{ value: props.value }]
      }
    ]
  })
}

watch(() => props.value, () => {
  updateChart()
})

onMounted(() => {
  initChart()
  window.addEventListener('resize', () => {
    chart && chart.resize()
  })
})
</script>

<style scoped>
.gauge-container {
  text-align: center;
}
</style>
