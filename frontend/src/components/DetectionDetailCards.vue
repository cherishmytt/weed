<template>
  <div class="floating-cards-container">
    <transition-group name="card-appear">
      <div 
        v-for="cardId in openCards" 
        :key="cardId" 
        class="floating-card"
        :style="getCardStyle(cardId)"
        v-loading="loadingCards[cardId]"
        @mousedown="startDrag($event, cardId)"
      >
        <div class="card-header" @mousedown.stop="startDrag($event, cardId)">
          <span class="card-title">检测记录 #{{ cardId }}</span>
          <el-button 
            type="danger" 
            icon="el-icon-close" 
            circle 
            size="small"
            @click.stop="closeCard(cardId)"
          />
        </div>
        
        <div v-if="cardDetails[cardId]" class="card-content">
          <div class="image-row">
            <div class="image-box">
              <div class="image-label">原始图像</div>
              <el-image
                :src="cardDetails[cardId].imageUrl"
                fit="contain"
                :preview-src-list="[cardDetails[cardId].imageUrl]"
                class="detail-image"
              />
            </div>
            <div class="image-box">
              <div class="image-label">检测结果标注</div>
              <el-image
                :src="cardDetails[cardId].resultUrl"
                fit="contain"
                :preview-src-list="[cardDetails[cardId].resultUrl]"
                class="detail-image"
              />
            </div>
          </div>

          <div class="stats-row">
            <div class="stat-item">
              <span class="stat-label">杂草数量</span>
              <span class="stat-value">{{ cardDetails[cardId].weedCount }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">作物数量</span>
              <span class="stat-value">{{ cardDetails[cardId].cropCount }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">推理耗时</span>
              <span class="stat-value">{{ cardDetails[cardId].inferenceTime }} ms</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">检测时间</span>
              <span class="stat-value">{{ cardDetails[cardId].detectedAt }}</span>
            </div>
          </div>

          <div v-if="cardDetails[cardId].detections && cardDetails[cardId].detections.length > 0" class="detections-section">
            <div class="section-title">检测目标 ({{ cardDetails[cardId].detections.length }})</div>
            <div class="detections-list">
              <div 
                v-for="(detection, index) in cardDetails[cardId].detections" 
                :key="index"
                class="detection-item"
              >
                <el-tag :type="detection.classId === 8 || detection.class === 'weed' ? 'danger' : 'success'" size="small">
                  {{ detection.className }}
                </el-tag>
                <span class="detection-confidence">{{ (detection.confidence * 100).toFixed(1) }}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition-group>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { getDetectionDetail } from '@/api/detection'

const openCards = ref([])
const cardDetails = ref({})
const loadingCards = ref({})
const cardPositions = ref({})
const draggingCard = ref(null)
const dragOffset = ref({ x: 0, y: 0 })

const STORAGE_KEY = 'detection-detail-cards'
const POSITIONS_KEY = 'detection-card-positions'

function saveCardsToStorage() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(openCards.value))
}

function loadCardsFromStorage() {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) {
    openCards.value = JSON.parse(saved)
  }
}

function savePositionsToStorage() {
  localStorage.setItem(POSITIONS_KEY, JSON.stringify(cardPositions.value))
}

function loadPositionsFromStorage() {
  const saved = localStorage.getItem(POSITIONS_KEY)
  if (saved) {
    cardPositions.value = JSON.parse(saved)
  }
}

function getCardStyle(cardId) {
  const position = cardPositions.value[cardId]
  if (position) {
    return {
      position: 'absolute',
      left: position.x + 'px',
      top: position.y + 'px'
    }
  }
  return {
    position: 'absolute',
    left: '20px',
    top: '20px'
  }
}

function startDrag(event, cardId) {
  if (event.button !== 0) return
  
  draggingCard.value = cardId
  const card = event.currentTarget
  const rect = card.getBoundingClientRect()
  dragOffset.value = {
    x: event.clientX - rect.left,
    y: event.clientY - rect.top
  }
  
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}

function onDrag(event) {
  if (!draggingCard.value) return
  
  const container = document.querySelector('.floating-cards-container')
  if (!container) return
  
  const containerRect = container.getBoundingClientRect()
  let x = event.clientX - containerRect.left - dragOffset.value.x
  let y = event.clientY - containerRect.top - dragOffset.value.y
  
  x = Math.max(0, Math.min(x, containerRect.width - 380))
  y = Math.max(0, Math.min(y, containerRect.height - 300))
  
  cardPositions.value[draggingCard.value] = { x, y }
}

function stopDrag() {
  if (draggingCard.value) {
    savePositionsToStorage()
  }
  draggingCard.value = null
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}

function closeCard(cardId) {
  const index = openCards.value.indexOf(cardId)
  if (index > -1) {
    openCards.value.splice(index, 1)
    delete cardDetails.value[cardId]
    delete loadingCards.value[cardId]
    delete cardPositions.value[cardId]
    saveCardsToStorage()
    savePositionsToStorage()
  }
}

async function loadCardDetail(cardId) {
  if (loadingCards.value[cardId]) return
  
  loadingCards.value[cardId] = true
  try {
    const res = await getDetectionDetail(cardId)
    if (res.code === 200) {
      cardDetails.value[cardId] = res.data
    }
  } finally {
    loadingCards.value[cardId] = false
  }
}

function addCard(cardId) {
  if (!openCards.value.includes(cardId)) {
    openCards.value.push(cardId)
    saveCardsToStorage()
    loadCardDetail(cardId)
  }
}

loadCardsFromStorage()
loadPositionsFromStorage()
openCards.value.forEach(cardId => {
  loadCardDetail(cardId)
})

watch(() => openCards.value, () => {
  saveCardsToStorage()
}, { deep: true })

defineExpose({
  addCard,
  openCards
})
</script>

<style scoped>
.floating-cards-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  pointer-events: none;
}

.floating-card {
  position: absolute;
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  overflow: hidden;
  transition: box-shadow 0.3s ease, transform 0.3s ease;
  pointer-events: auto;
  cursor: move;
  width: 380px;
}

.floating-card:hover {
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 16px 16px 0 0;
}

.card-title {
  font-weight: 600;
  font-size: 14px;
}

.card-content {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 400px;
  overflow-y: auto;
}

.image-row {
  display: flex;
  gap: 8px;
}

.image-box {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.image-label {
  font-size: 11px;
  font-weight: 600;
  color: #666;
  text-align: center;
}

.detail-image {
  width: 100%;
  height: 100px;
  border-radius: 8px;
  border: 1px solid #EBEEF5;
  object-fit: cover;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.stat-item {
  background: #f5f7fa;
  padding: 8px;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-label {
  font-size: 10px;
  color: #909399;
}

.stat-value {
  font-size: 12px;
  font-weight: 600;
  color: #303133;
}

.detections-section {
  margin-top: 4px;
}

.section-title {
  font-size: 11px;
  font-weight: 600;
  color: #666;
  margin-bottom: 6px;
}

.detections-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detection-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 8px;
  background: #f9fafc;
  border-radius: 6px;
}

.detection-confidence {
  font-size: 11px;
  color: #67c23a;
  font-weight: 600;
}

.card-appear-enter-active,
.card-appear-leave-active {
  transition: all 0.3s ease;
}

.card-appear-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.card-appear-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

.card-appear-move {
  transition: transform 0.3s ease;
}
</style>