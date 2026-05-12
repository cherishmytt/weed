<template>
  <div class="imu-attitude-container">
    <!-- 左侧：机器人 + 角度显示 -->
    <div class="left-panel">
      <!-- 机器人模型 -->
      <div class="robot-3d-container">
        <div class="robot-scene" :style="sceneTransform">
          <!-- 地面参考线 -->
          <div class="ground-reference">
            <div class="ground-line"></div>
            <div class="ground-grid">
              <div v-for="i in 5" :key="'h'+i" class="grid-line horizontal" :style="{ top: `${(i - 3) * 20}px` }"></div>
              <div v-for="i in 5" :key="'v'+i" class="grid-line vertical" :style="{ left: `${(i - 3) * 20}px` }"></div>
            </div>
          </div>
          
          <!-- 机器人模型 -->
          <div class="robot-model">
            <div class="robot-body">
              <div class="lidar">
                <div class="lidar-ring"></div>
                <div class="lidar-dot"></div>
              </div>
              <div class="main-body">
                <div class="body-top"></div>
                <div class="body-center"></div>
                <div class="body-bottom"></div>
              </div>
              <div class="sensor-left"></div>
              <div class="sensor-right"></div>
            </div>
            <div class="wheel wheel-front-left"></div>
            <div class="wheel wheel-front-right"></div>
            <div class="wheel wheel-back-left"></div>
            <div class="wheel wheel-back-right"></div>
            <div class="direction-arrow"></div>
          </div>
        </div>
      </div>
      
      <!-- 角度显示 -->
      <div class="angle-display-container">
        <div class="angle-item">
          <span class="angle-label">横滚角</span>
          <span class="angle-value roll">{{ roll.toFixed(1) }}°</span>
        </div>
        <div class="angle-item">
          <span class="angle-label">俯仰角</span>
          <span class="angle-value pitch">{{ pitch.toFixed(1) }}°</span>
        </div>
      </div>
    </div>
    
    <!-- 右侧：数据面板 -->
    <div class="data-panel" v-if="imu.accel || imu.gyro || imu.mag">
      <!-- 加速度卡片 -->
      <div class="data-card accel-card" v-if="imu.accel">
        <div class="card-header">
          <span class="card-title">加速度</span>
        </div>
        <div class="card-grid">
          <div class="axis-item">
            <span class="axis-label">X</span>
            <span class="axis-value">{{ (imu.accel.x || 0).toFixed(2) }}</span>
            <span class="axis-unit">m/s²</span>
          </div>
          <div class="axis-item">
            <span class="axis-label">Y</span>
            <span class="axis-value">{{ (imu.accel.y || 0).toFixed(2) }}</span>
            <span class="axis-unit">m/s²</span>
          </div>
          <div class="axis-item">
            <span class="axis-label">Z</span>
            <span class="axis-value">{{ (imu.accel.z || 0).toFixed(2) }}</span>
            <span class="axis-unit">m/s²</span>
          </div>
        </div>
      </div>
      
      <!-- 角速度卡片 -->
      <div class="data-card gyro-card" v-if="imu.gyro">
        <div class="card-header">
          <span class="card-title">角速度</span>
        </div>
        <div class="card-grid">
          <div class="axis-item">
            <span class="axis-label">X</span>
            <span class="axis-value">{{ (imu.gyro.x || 0).toFixed(4) }}</span>
            <span class="axis-unit">rad/s</span>
          </div>
          <div class="axis-item">
            <span class="axis-label">Y</span>
            <span class="axis-value">{{ (imu.gyro.y || 0).toFixed(4) }}</span>
            <span class="axis-unit">rad/s</span>
          </div>
          <div class="axis-item" v-if="typeof imu.gyro.z !== 'undefined'">
            <span class="axis-label">Z</span>
            <span class="axis-value">{{ (imu.gyro.z || 0).toFixed(4) }}</span>
            <span class="axis-unit">rad/s</span>
          </div>
        </div>
      </div>
      
      <!-- 磁场卡片 -->
      <div class="data-card mag-card" v-if="imu.mag">
        <div class="card-header">
          <div class="card-icon mag-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
            </svg>
          </div>
          <span class="card-title">磁场</span>
        </div>
        <div class="card-grid">
          <div class="axis-item">
            <span class="axis-label">X</span>
            <span class="axis-value">{{ (imu.mag.x || 0).toFixed(2) }}</span>
            <span class="axis-unit">μT</span>
          </div>
          <div class="axis-item">
            <span class="axis-label">Y</span>
            <span class="axis-value">{{ (imu.mag.y || 0).toFixed(2) }}</span>
            <span class="axis-unit">μT</span>
          </div>
          <div class="axis-item">
            <span class="axis-label">Z</span>
            <span class="axis-value">{{ (imu.mag.z || 0).toFixed(2) }}</span>
            <span class="axis-unit">μT</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  imu: {
    type: Object,
    default: () => ({})
  }
})

const roll = computed(() => props.imu?.roll || 0)
const pitch = computed(() => props.imu?.pitch || 0)

const sceneTransform = computed(() => ({
  transform: `rotateX(${-pitch.value}deg) rotateZ(${roll.value}deg)`
}))
</script>

<style scoped>
.imu-attitude-container {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  justify-content: space-between;
  width: 100%;
  padding: 0;
  gap: 24px;
}

.left-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  flex: 0 0 180px;
  gap: 8px;
  padding-top: 16px;
}

/* 角度显示容器 */
.angle-display-container {
  display: flex;
  gap: 16px;
  justify-content: center;
  width: 100%;
}

.angle-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 10px;
  min-width: 70px;
}

.angle-label {
  font-size: 11px;
  color: var(--text-secondary);
  font-weight: 500;
}

.angle-value {
  font-size: 20px;
  font-weight: 700;
  font-family: var(--font-family);
  letter-spacing: -0.3px;
}

.angle-value.roll {
  color: #59d6ff;
  text-shadow: 0 0 8px rgba(89, 214, 255, 0.4);
}

.angle-value.pitch {
  color: #39d398;
  text-shadow: 0 0 8px rgba(57, 211, 152, 0.4);
}

/* 3D 机器人容器 */
.robot-3d-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.robot-scene {
  width: 180px;
  height: 180px;
  perspective: 500px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.1s ease-out;
}

/* 地面参考 */
.ground-reference {
  position: absolute;
  width: 120px;
  height: 120px;
  pointer-events: none;
}

.ground-line {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 2px;
  background: rgba(255, 255, 255, 0.5);
  box-shadow: 0 0 4px rgba(255, 255, 255, 0.2);
}

.ground-grid {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 80px;
  height: 80px;
  transform: translate(-50%, -50%);
}

.grid-line {
  position: absolute;
  background: rgba(255, 255, 255, 0.15);
}

.grid-line.horizontal {
  left: 0;
  right: 0;
  height: 1px;
}

.grid-line.vertical {
  top: 0;
  bottom: 0;
  width: 1px;
}

/* 机器人模型 */
.robot-model {
  position: relative;
  width: 100px;
  height: 80px;
  transform-style: preserve-3d;
  transition: transform 0.1s ease-out;
}

.robot-body {
  position: absolute;
  top: 12px;
  left: 50%;
  transform: translateX(-50%);
  width: 50px;
  height: 38px;
}

.lidar {
  position: absolute;
  top: -10px;
  left: 50%;
  transform: translateX(-50%);
  width: 25px;
  height: 10px;
}

.lidar-ring {
  width: 100%;
  height: 8px;
  border: 2px solid #4FC3F7;
  border-radius: 50%;
  background: rgba(79, 195, 247, 0.25);
}

.lidar-dot {
  position: absolute;
  top: 50%;
  right: 0;
  width: 5px;
  height: 5px;
  background: #4FC3F7;
  border-radius: 50%;
  transform: translateY(-50%);
  box-shadow: 0 0 5px #4FC3F7;
}

.main-body {
  position: absolute;
  top: 12px;
  left: 50%;
  transform: translateX(-50%);
  width: 45px;
  height: 25px;
}

.body-top {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 40px;
  height: 8px;
  background: linear-gradient(135deg, #66BB6A 0%, #43A047 100%);
  border-radius: 3px 3px 0 0;
}

.body-center {
  position: absolute;
  top: 8px;
  left: 50%;
  transform: translateX(-50%);
  width: 45px;
  height: 10px;
  background: linear-gradient(135deg, #4CAF50 0%, #388E3C 100%);
}

.body-bottom {
  position: absolute;
  top: 18px;
  left: 50%;
  transform: translateX(-50%);
  width: 40px;
  height: 7px;
  background: linear-gradient(135deg, #388E3C 0%, #2E7D32 100%);
  border-radius: 0 0 3px 3px;
}

.sensor-left,
.sensor-right {
  position: absolute;
  top: 15px;
  width: 8px;
  height: 15px;
  background: #78909C;
  border-radius: 2px;
}

.sensor-left { left: -10px; }
.sensor-right { right: -10px; }

.wheel {
  position: absolute;
  width: 15px;
  height: 15px;
  background: linear-gradient(90deg, #37474F 0%, #263238 50%, #1A237E 100%);
  border-radius: 50%;
  border: 2px solid #546E7A;
}

.wheel-front-left { top: 45px; left: 10px; }
.wheel-front-right { top: 45px; right: 10px; }
.wheel-back-left { top: 58px; left: 10px; }
.wheel-back-right { top: 58px; right: 10px; }

.direction-arrow {
  position: absolute;
  top: 23px;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 0;
  border-left: 8px solid transparent;
  border-right: 8px solid transparent;
  border-bottom: 10px solid #FFC107;
}

/* 右侧数据面板 */
.data-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}

/* 数据卡片 */
.data-card {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  padding: 10px 12px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(8px);
}

.card-header {
  margin-bottom: 8px;
  text-align: left;
}

.card-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  font-family: var(--font-family);
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.axis-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 6px;
  background: transparent;
  border-radius: 0;
  min-height: 55px;
  justify-content: center;
}

.axis-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 4px;
  letter-spacing: 0.3px;
}

.axis-value {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  font-family: var(--font-family);
  letter-spacing: -0.3px;
  line-height: 1.1;
}

.axis-unit {
  font-size: 11px;
  color: var(--text-tertiary);
  margin-top: 3px;
  font-weight: 500;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .imu-attitude-container {
    flex-direction: column;
    gap: 16px;
  }
  
  .left-panel {
    flex: none;
    width: 100%;
    flex-direction: row;
    align-items: center;
    justify-content: space-around;
  }
  
  .angle-gauge-container {
    flex-direction: column;
    gap: 8px;
  }
  
  .gauge-ring {
    width: 80px;
    height: 80px;
  }
  
  .robot-scene {
    width: 140px;
    height: 140px;
  }
  
  .robot-model {
    width: 80px;
    height: 65px;
  }
  
  .card-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .axis-item {
    padding: 8px 6px;
    min-height: 55px;
  }
  
  .axis-value {
    font-size: 15px;
  }
}
</style>
