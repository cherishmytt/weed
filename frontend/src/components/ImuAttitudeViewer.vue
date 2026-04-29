<template>
  <div class="imu-attitude-container">
    <div class="attitude-display">
      <!-- 人工地平仪 -->
      <div class="artificial-horizon" :style="{ transform: `rotate(${roll}deg)` }">
        <div class="horizon-circle">
          <div class="horizon-line" :style="{ transform: `translateY(${-pitch * 2}px)` }"></div>
          <div class="horizon-scale">
            <div v-for="i in 12" :key="i" class="scale-mark" :style="{ transform: `rotate(${i * 30}deg)` }"></div>
          </div>
          <div class="center-mark"></div>
        </div>
      </div>
      
      <!-- 加速度数据 -->
      <div class="imu-data" v-if="imu.accel || imu.gyro || imu.mag">
        <!-- 加速度 -->
        <div class="data-section" v-if="imu.accel">
          <div class="section-title">加速度</div>
          <div class="data-grid">
            <div class="data-item">
              <span class="data-label">X:</span>
              <span class="data-value">{{ (imu.accel.x || 0).toFixed(2) }} m/s²</span>
            </div>
            <div class="data-item">
              <span class="data-label">Y:</span>
              <span class="data-value">{{ (imu.accel.y || 0).toFixed(2) }} m/s²</span>
            </div>
            <div class="data-item">
              <span class="data-label">Z:</span>
              <span class="data-value">
                {{ (imu.accel.z || 0).toFixed(2) }} m/s²
                <span class="g-label">G</span>
                <el-icon v-if="isGravityStable" class="stable-icon"><Check /></el-icon>
              </span>
            </div>
          </div>
        </div>
        
        <!-- 角速度 -->
        <div class="data-section" v-if="imu.gyro">
          <div class="section-title">角速度</div>
          <div class="data-grid">
            <div class="data-item">
              <span class="data-label">X:</span>
              <span class="data-value">{{ (imu.gyro.x || 0).toFixed(4) }} rad/s</span>
            </div>
            <div class="data-item">
              <span class="data-label">Y:</span>
              <span class="data-value">{{ (imu.gyro.y || 0).toFixed(4) }} rad/s</span>
            </div>
            <div class="data-item" v-if="typeof imu.gyro.z !== 'undefined'">
              <span class="data-label">Z:</span>
              <span class="data-value">{{ (imu.gyro.z || 0).toFixed(4) }} rad/s</span>
            </div>
          </div>
        </div>
        
        <!-- 磁场 -->
        <div class="data-section" v-if="imu.mag">
          <div class="section-title">磁场</div>
          <div class="data-grid">
            <div class="data-item">
              <span class="data-label">X:</span>
              <span class="data-value">{{ (imu.mag.x || 0).toFixed(2) }}</span>
            </div>
            <div class="data-item">
              <span class="data-label">Y:</span>
              <span class="data-value">{{ (imu.mag.y || 0).toFixed(2) }}</span>
            </div>
            <div class="data-item">
              <span class="data-label">Z:</span>
              <span class="data-value">{{ (imu.mag.z || 0).toFixed(2) }}</span>
            </div>
          </div>
        </div>
        
        <!-- 温度 -->
        <div class="data-section" v-if="typeof imu.temp === 'number'">
          <div class="section-title">温度</div>
          <div class="data-grid">
            <div class="data-item">
              <span class="data-label">IMU:</span>
              <span class="data-value">{{ imu.temp.toFixed(1) }}°C</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Check } from '@element-plus/icons-vue'

const props = defineProps({
  imu: {
    type: Object,
    default: () => ({})
  }
})

// 计算属性
const roll = computed(() => props.imu?.roll || 0)
const pitch = computed(() => props.imu?.pitch || 0)

const isGravityStable = computed(() => {
  if (!props.imu?.accel) return true
  const az = Math.abs(props.imu.accel.z || 0)
  return az > 9 && az < 10.5 // 重力加速度约 9.8 m/s²
})
</script>

<style scoped>
.imu-attitude-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px;
}

.attitude-display {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 16px;
  justify-content: center;
}

/* 人工地平仪 */
.artificial-horizon {
  width: 120px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.3s ease;
}

.horizon-circle {
  width: 100px;
  height: 100px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  position: relative;
  background: linear-gradient(to bottom, var(--primary-color) 0%, var(--primary-color) 50%, var(--success-color) 50%, var(--success-color) 100%);
  overflow: hidden;
}

.horizon-line {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 2px;
  background: #fff;
  box-shadow: 0 0 4px rgba(0, 0, 0, 0.3);
  transition: transform 0.3s ease;
}

.horizon-scale {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.scale-mark {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 2px;
  height: 12px;
  background: #fff;
  transform-origin: top center;
  transform: translate(-50%, -50%) rotate(0deg);
}

.center-mark {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 8px;
  height: 8px;
  background: #fff;
  border: 2px solid #333;
  border-radius: 50%;
  transform: translate(-50%, -50%);
}

/* IMU 数据 */
.imu-data {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  max-width: 280px;
}

.data-section {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
  text-align: center;
  font-family: var(--font-family);
}

.data-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
}

.data-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 6px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  font-size: 12px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

.data-label {
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 2px;
  font-size: 11px;
  font-family: var(--font-family);
}

.data-value {
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 12px;
  font-family: var(--font-family);
}

.g-label {
  font-size: 10px;
  color: var(--text-tertiary);
  font-weight: normal;
}

.stable-icon {
  color: var(--primary-color);
  font-size: 12px;
}

/* 人工地平仪样式调整 */
.horizon-circle {
  width: 100px;
  height: 100px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  position: relative;
  background: linear-gradient(to bottom, var(--primary-color) 0%, var(--primary-color) 50%, var(--success-color) 50%, var(--success-color) 100%);
  overflow: hidden;
}

.horizon-line {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 2px;
  background: rgba(255, 255, 255, 0.8);
  box-shadow: 0 0 4px rgba(0, 0, 0, 0.3);
  transition: transform 0.3s ease;
}

.scale-mark {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 2px;
  height: 12px;
  background: rgba(255, 255, 255, 0.8);
  transform-origin: top center;
  transform: translate(-50%, -50%) rotate(0deg);
}

.center-mark {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 8px;
  height: 8px;
  background: rgba(255, 255, 255, 0.9);
  border: 2px solid rgba(0, 0, 0, 0.3);
  border-radius: 50%;
  transform: translate(-50%, -50%);
}

/* 响应式调整 */
@media (max-width: 768px) {
  .artificial-horizon {
    width: 140px;
    height: 140px;
  }
  
  .horizon-circle {
    width: 120px;
    height: 120px;
  }
  
  .data-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .data-item {
    font-size: 12px;
    padding: 6px;
  }
  
  .data-value {
    font-size: 13px;
  }
}
</style>
