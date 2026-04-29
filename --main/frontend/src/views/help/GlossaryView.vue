<template>
  <div class="glossary-page">
    <aside class="glossary-nav glass-panel">
      <div class="nav-head">
        <strong>分类导航</strong>
        <span>{{ totalVisibleTerms }} 个术语</span>
      </div>

      <div class="nav-list">
        <button
          v-for="group in filteredGroups"
          :key="group.id"
          class="nav-item"
          :class="{ active: activeGroup === group.id }"
          @click="scrollToGroup(group.id)"
        >
          <span>{{ group.title }}</span>
          <small>{{ group.items.length }}</small>
        </button>
      </div>

      <div class="hotword-panel">
        <div class="hotword-head">
          <strong>热词速览</strong>
          <span>点击可筛选</span>
        </div>
        <div class="hotword-cloud">
          <button
            v-for="word in hotWords"
            :key="word.label"
            class="hotword-chip"
            :class="`level-${word.level}`"
            @click="applyHotword(word.label)"
          >
            {{ word.label }}
          </button>
        </div>
      </div>
    </aside>

    <section class="glossary-main glass-panel">
      <div class="main-toolbar">
        <h2>系统术语说明</h2>
        <el-input v-model="searchKeyword" clearable placeholder="搜索术语、字段或功能" class="search-input">
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <div ref="contentRef" class="content-scroll" @scroll="handleScroll">
        <section
          v-for="group in filteredGroups"
          :key="group.id"
          :ref="setSectionRef(group.id)"
          class="term-group"
        >
          <div class="group-head">
            <div>
              <h3>{{ group.title }}</h3>
              <span>{{ group.description }}</span>
            </div>
            <em>{{ group.items.length }} 项</em>
          </div>

          <el-collapse v-model="openedTerms" class="term-collapse">
            <el-collapse-item v-for="item in group.items" :key="item.id" :name="item.id" class="term-item">
              <template #title>
                <div class="term-title">
                  <strong>{{ item.term }}</strong>
                  <div class="term-aliases">
                    <span v-for="alias in item.aliases" :key="alias" class="alias-chip">{{ alias }}</span>
                  </div>
                </div>
              </template>

              <div class="term-body">
                <p>{{ item.summary }}</p>
                <p v-for="detail in item.details" :key="detail">{{ detail }}</p>
                <div v-if="item.keywords?.length" class="keyword-row">
                  <span>关键词</span>
                  <div class="keyword-list">
                    <i v-for="keyword in item.keywords" :key="keyword">{{ keyword }}</i>
                  </div>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>
        </section>

        <el-empty v-if="!filteredGroups.length" description="没有匹配到相关术语" />
      </div>
    </section>
  </div>
</template>

<script setup>
import { Search } from '@element-plus/icons-vue'
import { computed, nextTick, onMounted, ref, watch } from 'vue'

import { GLOSSARY_GROUPS, flattenGlossaryTerms } from '@/data/glossary'

const searchKeyword = ref('')
const activeGroup = ref(GLOSSARY_GROUPS[0]?.id || '')
const openedTerms = ref([])
const contentRef = ref(null)
const sectionRefs = {}

const normalizeText = (value) => (value || '').trim().toLowerCase()

const withTermIds = (groups) =>
  groups.map((group) => ({
    ...group,
    items: group.items.map((item) => ({
      ...item,
      id: `${group.id}-${item.term.toLowerCase().replace(/[^a-z0-9\u4e00-\u9fa5]+/gi, '-')}`,
    })),
  }))

const filteredGroups = computed(() => {
  const keyword = normalizeText(searchKeyword.value)
  if (!keyword) {
    return withTermIds(GLOSSARY_GROUPS)
  }

  return withTermIds(GLOSSARY_GROUPS)
    .map((group) => ({
      ...group,
      items: group.items.filter((item) =>
        [
          group.title,
          item.term,
          ...(item.aliases || []),
          ...(item.keywords || []),
          item.summary,
          ...(item.details || []),
        ]
          .filter(Boolean)
          .join(' ')
          .toLowerCase()
          .includes(keyword),
      ),
    }))
    .filter((group) => group.items.length)
})

const totalVisibleTerms = computed(() => filteredGroups.value.reduce((sum, group) => sum + group.items.length, 0))

const hotWords = computed(() => {
  const counter = new Map()
  flattenGlossaryTerms().forEach((item) => {
    ;[item.term, ...(item.aliases || []), ...(item.keywords || [])]
      .filter(Boolean)
      .forEach((word) => counter.set(word, (counter.get(word) || 0) + 1))
  })

  const ranked = [...counter.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], 'zh-CN'))
    .slice(0, 18)

  const max = ranked[0]?.[1] || 1
  return ranked.map(([label, count], index) => {
    const ratio = count / max
    let level = 1
    if (ratio >= 0.9) level = 5
    else if (ratio >= 0.75) level = 4
    else if (ratio >= 0.55) level = 3
    else if (ratio >= 0.35) level = 2
    return { label, count, level, index }
  })
})

const setSectionRef = (id) => (element) => {
  if (element) {
    sectionRefs[id] = element
  } else {
    delete sectionRefs[id]
  }
}

const handleScroll = () => {
  const container = contentRef.value
  if (!container || !filteredGroups.value.length) return

  const threshold = container.scrollTop + 32
  let current = filteredGroups.value[0].id

  filteredGroups.value.forEach((group) => {
    const section = sectionRefs[group.id]
    if (section && section.offsetTop <= threshold) {
      current = group.id
    }
  })

  activeGroup.value = current
}

const scrollToGroup = (groupId) => {
  const container = contentRef.value
  const section = sectionRefs[groupId]
  if (!container || !section) return

  activeGroup.value = groupId
  container.scrollTo({
    top: Math.max(section.offsetTop - 12, 0),
    behavior: 'smooth',
  })
}

const applyHotword = (word) => {
  searchKeyword.value = word
}

watch(
  filteredGroups,
  async (groups) => {
    await nextTick()
    if (!groups.length) {
      activeGroup.value = ''
      openedTerms.value = []
      return
    }

    if (!groups.some((group) => group.id === activeGroup.value)) {
      activeGroup.value = groups[0].id
    }

    if (normalizeText(searchKeyword.value)) {
      openedTerms.value = groups.flatMap((group) => group.items.map((item) => item.id))
    } else if (!openedTerms.value.length) {
      openedTerms.value = groups.map((group) => group.items[0]?.id).filter(Boolean)
    }

    handleScroll()
  },
  { immediate: true, deep: true },
)

onMounted(async () => {
  await nextTick()
  handleScroll()
})
</script>

<style scoped>
.glossary-page {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 18px;
  height: 100%;
  min-height: 0;
}

.glossary-nav,
.glossary-main {
  min-height: 0;
}

.glossary-nav {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 18px 16px;
}

.nav-head,
.hotword-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 10px;
}

.nav-head span,
.hotword-head span {
  color: var(--text-secondary);
  font-size: 13px;
}

.nav-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.nav-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  padding: 14px 16px;
  color: var(--text-secondary);
  border: 1px solid var(--line-soft);
  border-radius: 16px;
  background: var(--bg-elevated);
  cursor: pointer;
  transition: all 0.22s ease;
}

.nav-item:hover,
.nav-item.active {
  color: var(--text-primary);
  border-color: var(--line-strong);
  transform: translateX(4px);
}

.nav-item.active {
  background: linear-gradient(135deg, rgba(22, 73, 124, 0.28), rgba(10, 33, 55, 0.92));
  box-shadow: 0 14px 26px rgba(0, 0, 0, 0.18);
}

.nav-item small {
  min-width: 28px;
  padding: 4px 8px;
  text-align: center;
  border-radius: 999px;
  background: var(--bg-chip);
  color: var(--text-primary);
}

.hotword-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 16px;
  border-radius: 20px;
  border: 1px solid var(--line-soft);
  background:
    radial-gradient(circle at top right, rgba(89, 227, 255, 0.18), transparent 42%),
    linear-gradient(180deg, rgba(8, 18, 31, 0.92), rgba(5, 10, 18, 0.96));
}

.hotword-cloud {
  display: flex;
  align-content: flex-start;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px 12px;
}

.hotword-chip {
  padding: 0;
  color: var(--text-primary);
  border: none;
  background: transparent;
  cursor: pointer;
  text-shadow: 0 0 14px rgba(70, 191, 255, 0.16);
  transition: transform 0.22s ease, opacity 0.22s ease;
}

.hotword-chip:hover {
  transform: translateY(-2px) scale(1.04);
}

.hotword-chip.level-1 {
  font-size: 15px;
  opacity: 0.68;
}

.hotword-chip.level-2 {
  font-size: 18px;
  opacity: 0.78;
  color: #9ce5ff;
}

.hotword-chip.level-3 {
  font-size: 22px;
  opacity: 0.86;
  color: #7fd6ff;
}

.hotword-chip.level-4 {
  font-size: 27px;
  opacity: 0.94;
  color: #ffb366;
}

.hotword-chip.level-5 {
  font-size: 33px;
  font-weight: 700;
  color: #59e3ff;
}

.glossary-main {
  display: flex;
  flex-direction: column;
  padding: 18px 20px;
}

.main-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--line-soft);
}

.main-toolbar h2 {
  margin: 0;
  font-size: 24px;
}

.search-input {
  max-width: 340px;
  flex: 1;
}

.content-scroll {
  flex: 1;
  overflow: auto;
  min-height: 0;
  padding-right: 4px;
}

.term-group + .term-group {
  margin-top: 18px;
}

.group-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 12px;
}

.group-head h3 {
  margin: 0 0 6px;
  font-size: 18px;
}

.group-head span,
.group-head em {
  color: var(--text-secondary);
  font-style: normal;
}

.term-collapse {
  display: grid;
  gap: 12px;
}

.term-collapse :deep(.el-collapse-item) {
  border: 1px solid var(--line-soft);
  border-radius: 18px;
  overflow: hidden;
  background: var(--bg-elevated);
}

.term-collapse :deep(.el-collapse-item__header) {
  min-height: 66px;
  padding: 0 18px;
  color: var(--text-primary);
  background: transparent;
  border-bottom: none;
}

.term-collapse :deep(.el-collapse-item__wrap) {
  color: var(--text-primary);
  background: transparent;
  border-top: 1px solid var(--line-soft);
  border-bottom: none;
}

.term-collapse :deep(.el-collapse-item__content) {
  padding: 0;
}

.term-title {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  width: calc(100% - 18px);
}

.term-title strong {
  font-size: 16px;
}

.term-aliases,
.keyword-list {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.alias-chip,
.keyword-list i {
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid var(--line-soft);
  background: var(--bg-chip);
  color: var(--text-secondary);
  font-style: normal;
  font-size: 12px;
}

.term-body {
  padding: 16px 18px 18px;
}

.term-body p {
  margin: 0;
  line-height: 1.85;
  color: var(--text-secondary);
}

.term-body p + p {
  margin-top: 10px;
}

.keyword-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-top: 14px;
}

.keyword-row > span {
  min-width: 56px;
  color: var(--text-tertiary);
}

@media (max-width: 1180px) {
  .glossary-page {
    grid-template-columns: 1fr;
  }

  .glossary-nav {
    gap: 14px;
  }

  .nav-list {
    flex-direction: row;
    overflow: auto;
  }

  .nav-item {
    min-width: 180px;
  }

  .hotword-panel {
    min-height: 180px;
  }

  .main-toolbar {
    flex-direction: column;
    align-items: flex-start;
  }

  .search-input {
    max-width: none;
    width: 100%;
  }
}
</style>
