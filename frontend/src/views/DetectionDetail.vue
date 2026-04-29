<template>
  <div class="detail-cards-container">
    <div v-if="openCards.length === 0" class="empty-state">
      <el-empty description="没有打开的详情卡片">
        <el-button type="primary" @click="goToRecords">返回检测记录列表</el-button>
      </el-empty>
    </div>
    
    <div v-else class="cards-grid">
      <div 
        v-for="cardId in openCards" 
        :key="cardId" 
        class="detail-card glass-panel"
        v-loading="loadingCards[cardId]"
      >
        <div class="card-header-content">
          <span class="card-title">检测记录 #{{ cardId }}</span>
          <el-button 
            type="danger"
            icon="Close"
            circle 
            size="small"
            @click="closeCard(cardId)"
          />
        </div>
        
        <div v-if="cardDetails[cardId]" class="card-content">
          <el-row :gutter="10">
            <el-col :span="12">
              <div class="image-container">
                <div class="image-label">原始图像</div>
                <!-- 替换为可点击预览 -->
                <div 
                  @click="openPreview(cardDetails[cardId].imageUrl)"
                  style="cursor: pointer; width: 100%; max-height: 250px; border: 1px solid var(--line-soft); border-radius: var(--radius-sm); background: var(--bg-input); overflow: hidden;"
                >
                  <img
                    :src="cardDetails[cardId].imageUrl"
                    style="width: 100%; height: 100%; object-fit: contain;"
                  />
                </div>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="image-container">
                <div class="image-label">检测结果标注</div>
                <!-- 替换为可点击预览 -->
                <div 
                  @click="openPreview(cardDetails[cardId].resultUrl)"
                  style="cursor: pointer; width: 100%; max-height: 250px; border: 1px solid var(--line-soft); border-radius: var(--radius-sm); background: var(--bg-input); overflow: hidden;"
                >
                  <img
                    :src="cardDetails[cardId].resultUrl"
                    style="width: 100%; height: 100%; object-fit: contain;"
                  />
                </div>
              </div>
            </el-col>
          </el-row>

          <div class="stats-container">
            <el-descriptions :column="4" border size="small">
              <el-descriptions-item label="杂草数量">{{ cardDetails[cardId].weedCount }}</el-descriptions-item>
              <el-descriptions-item label="作物数量">{{ cardDetails[cardId].cropCount }}</el-descriptions-item>
              <el-descriptions-item label="推理耗时">{{ cardDetails[cardId].inferenceTime }} ms</el-descriptions-item>
              <el-descriptions-item label="检测时间">{{ cardDetails[cardId].detectedAt }}</el-descriptions-item>
            </el-descriptions>
          </div>

          <div v-if="cardDetails[cardId].detections && cardDetails[cardId].detections.length > 0" class="detections-container">
            <div class="section-title">检测目标列表 (共 {{ cardDetails[cardId].detections.length }} 个目标)</div>
            <el-table :data="cardDetails[cardId].detections" border size="small" max-height="200">
              <el-table-column label="类别" width="80">
                <template #default="{ row }">
                  <el-tag :type="row.class === 'weed' ? 'danger' : 'success'" size="small">
                    {{ row.className }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="confidence" label="置信度" width="80">
                <template #default="{ row }">
                  {{ (row.confidence * 100).toFixed(1) }}%
                </template>
              </el-table-column>
              <el-table-column prop="depth" label="深度 (m)" width="80" />
              <el-table-column label="边界框" width="140">
                <template #default="{ row }">
                  [{{ row.bbox?.join(', ') }}]
                </template>
              </el-table-column>
              <el-table-column label="三维坐标" width="140">
                <template #default="{ row }">
                  <div v-if="row.position3d">
                    ({{ row.position3d.x.toFixed(3) }}, {{ row.position3d.y.toFixed(3) }}, {{ row.position3d.z.toFixed(3) }})
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>
    </div>

    <!-- 全局最高层级图片预览（解决遮挡） -->
    <div
      v-if="previewVisible"
      @click="previewVisible = false"
      style="
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.92);
        z-index: 999999 !important;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: zoom-out;
        padding: 20px;
      "
    >
      <img
        :src="previewUrl"
        style="
          max-width: 96%;
          max-height: 96vh;
          object-fit: contain;
        "
        @click.stop
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getDetectionDetail } from '@/api/detection'
import { Close } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const openCards = ref([])
const cardDetails = ref({})
const loadingCards = ref({})

// 图片预览
const previewVisible = ref(false)
const previewUrl = ref('')
const openPreview = (url) => {
  previewUrl.value = url
  previewVisible.value = true
}

const STORAGE_KEY = 'detection-detail-cards'

function saveCardsToStorage() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(openCards.value))
}

function loadCardsFromStorage() {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) {
    openCards.value = JSON.parse(saved)
  }
}

function goToRecords() {
  router.push('/detection')
}

function closeCard(cardId) {
  const index = openCards.value.indexOf(cardId)
  if (index > -1) {
    openCards.value.splice(index, 1)
    delete cardDetails.value[cardId]
    delete loadingCards.value[cardId]
    saveCardsToStorage()
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

onMounted(() => {
  loadCardsFromStorage()
  const id = parseInt(route.query.id)
  if (id) {
    addCard(id)
  } else {
    openCards.value.forEach(cardId => {
      loadCardDetail(cardId)
    })
  }
})

watch(() => route.query.id, (newId) => {
  if (newId) {
    const id = parseInt(newId)
    addCard(id)
  }
})
</script>

<style scoped>
.detail-cards-container {
  padding: 20px;
  min-height: 100vh;
  background: var(--app-background);
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(500px, 1fr));
  gap: 20px;
}

.detail-card {
  padding: 20px;
}

.card-header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.card-title {
  font-weight: 600;
  font-size: 16px;
  color: var(--text-primary);
}

.card-content {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.image-container {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.image-label {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-secondary);
}

.detail-image {
  width: 100%;
  max-height: 250px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-sm);
  background: var(--bg-input);
}

.stats-container {
  margin-top: 10px;
}

.detections-container {
  margin-top: 10px;
}

.section-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 10px;
}
</style>