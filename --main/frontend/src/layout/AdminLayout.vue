<template>
  <div class="layout-shell" :class="{ collapsed: uiStore.sidebarCollapsed }">
    <aside class="sidebar glass-panel">
      <div class="brand">
        <span class="brand-dot"></span>
        <strong v-show="!uiStore.sidebarCollapsed" class="brand-line">全球野火监测平台</strong>
      </div>

      <el-menu
        router
        class="menu"
        :default-active="route.path"
        :collapse="uiStore.sidebarCollapsed"
        background-color="transparent"
        text-color="var(--menu-text)"
        active-text-color="var(--accent-cyan)"
      >
        <el-menu-item index="/overview"><el-icon><Grid /></el-icon><span>平台总览</span></el-menu-item>
        <el-menu-item index="/data"><el-icon><FolderOpened /></el-icon><span>数据管理</span></el-menu-item>
        <el-menu-item v-if="authStore.isAdmin" index="/sync-management"><el-icon><Refresh /></el-icon><span>数据同步</span></el-menu-item>
        <el-menu-item index="/analysis"><el-icon><PieChart /></el-icon><span>数据分析</span></el-menu-item>
        <el-menu-item index="/country-analysis"><el-icon><Histogram /></el-icon><span>国家专题</span></el-menu-item>
        <el-menu-item index="/map"><el-icon><Location /></el-icon><span>三维地图</span></el-menu-item>
        <el-menu-item index="/screen"><el-icon><Monitor /></el-icon><span>数据大屏</span></el-menu-item>
        <el-menu-item index="/glossary"><el-icon><Reading /></el-icon><span>术语说明</span></el-menu-item>
        <el-menu-item v-if="authStore.isAdmin" index="/users"><el-icon><User /></el-icon><span>用户管理</span></el-menu-item>
      </el-menu>

      <button class="collapse-btn" @click="uiStore.toggleSidebar()">
        <el-icon :size="16"><component :is="uiStore.sidebarCollapsed ? 'Expand' : 'Fold'" /></el-icon>
        <span v-show="!uiStore.sidebarCollapsed">收起导航</span>
      </button>
    </aside>

    <div class="main">
      <header class="topbar glass-panel">
        <div>
          <h1>{{ route.meta?.title || '全球野火火点监测与时空分析平台' }}</h1>
        </div>
        <div class="topbar-actions">
          <span class="user-name">{{ authStore.profile?.username }}</span>
          <el-button class="ghost-btn" @click="uiStore.toggleTheme()">
            <el-icon><component :is="uiStore.themeMode === 'dark' ? 'Sunny' : 'Moon'" /></el-icon>
            <span>{{ uiStore.themeMode === 'dark' ? '浅色' : '深色' }}</span>
          </el-button>
          <el-button class="ghost-btn" @click="$router.push('/screen')">大屏</el-button>
          <el-button @click="logout">退出</el-button>
        </div>
      </header>

      <main class="content" :class="{ immersive: route.meta?.immersive }">
        <div class="content-inner" :class="{ immersive: route.meta?.immersive }">
          <router-view v-slot="{ Component, route: currentRoute }">
            <keep-alive>
              <component
                :is="Component"
                v-if="currentRoute.meta?.cache !== false"
                :key="currentRoute.name || currentRoute.path"
              />
            </keep-alive>
            <component
              :is="Component"
              v-if="currentRoute.meta?.cache === false"
              :key="currentRoute.fullPath"
            />
          </router-view>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { useOverviewStore } from '@/stores/overview'
import { useUiStore } from '@/stores/ui'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const uiStore = useUiStore()
const overviewStore = useOverviewStore()

const logout = () => {
  authStore.clearSession()
  router.push('/login')
}

onMounted(() => {
  overviewStore.load().catch(() => {})
})
</script>

<style scoped>
.layout-shell {
  display: grid;
  grid-template-columns: 268px minmax(0, 1fr);
  gap: 16px;
  height: 100vh;
  padding: 16px;
  transition: grid-template-columns 0.28s ease;
}

.layout-shell.collapsed {
  grid-template-columns: 92px minmax(0, 1fr);
}

.layout-shell.collapsed .brand {
  justify-content: center;
  padding-inline: 0;
}

.sidebar {
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 14px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 54px;
  padding: 6px 8px 18px;
}

.brand-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  flex: none;
  background: linear-gradient(135deg, var(--accent-orange), var(--accent-cyan));
  box-shadow: 0 0 18px rgba(255, 141, 67, 0.66);
}

.brand-line {
  font-size: 18px;
  white-space: nowrap;
}

.menu {
  flex: 1;
  min-height: 0;
  border-right: none;
}

.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 44px;
  margin-top: 8px;
  color: var(--text-secondary);
  border-radius: 14px;
  border: 1px solid var(--line-soft);
  background: var(--bg-button-default);
  cursor: pointer;
  transition: all 0.24s ease;
}

.collapse-btn:hover {
  color: var(--text-primary);
  border-color: var(--line-strong);
}

.main {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
  min-height: 0;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 22px;
}

.topbar h1 {
  margin: 0;
  font-size: 24px;
  color: var(--text-primary);
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-name {
  color: var(--text-secondary);
}

.content {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.content-inner {
  height: 100%;
  overflow: auto;
  padding-right: 2px;
}

.content-inner.immersive {
  overflow: hidden;
}

@media (max-width: 1180px) {
  .layout-shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    display: none;
  }
}
</style>
