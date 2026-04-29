<template>
  <div class="layout-shell">
    <aside class="sidebar glass-panel">
      <div class="brand">
        <span class="brand-dot"></span>
        <strong class="brand-line">激光除草机器人</strong>
      </div>

      <el-menu
        router
        class="menu"
        :default-active="$route.path"
        background-color="transparent"
        text-color="var(--menu-text)"
        active-text-color="var(--accent-cyan)"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataLine /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/status">
          <el-icon><Timer /></el-icon>
          <span>状态历史</span>
        </el-menu-item>
        <el-menu-item index="/trajectory">
          <el-icon><Location /></el-icon>
          <span>轨迹地图</span>
        </el-menu-item>
        <el-menu-item index="/yolo-detection">
          <el-icon><Search /></el-icon>
          <span>YOLO在线检测</span>
        </el-menu-item>
        <el-menu-item index="/detection">
          <el-icon><Picture /></el-icon>
          <span>检测记录</span>
        </el-menu-item>
        <el-menu-item v-if="userStore.role === 'ADMIN'" index="/laser">
          <el-icon><Lightning /></el-icon>
          <span>激光控制</span>
        </el-menu-item>
        <el-menu-item v-if="userStore.role === 'ADMIN'" index="/laser-logs">
          <el-icon><List /></el-icon>
          <span>操作日志</span>
        </el-menu-item>
      </el-menu>

      <div class="user-info">
        <div class="user-detail-item">
          <span class="label">用户名:</span>
          <span class="value">{{ userStore.username }}</span>
        </div>
        <div class="user-detail-item">
          <span class="label">角色:</span>
          <span class="value">{{ userStore.role || '用户' }}</span>
        </div>
        <el-button class="ghost-btn" @click="handleLogout">
          <span>退出登录</span>
        </el-button>
      </div>
    </aside>

    <div class="main">
      <header class="topbar glass-panel">
        <div>
          <h1>{{ pageTitle }}</h1>
        </div>
      </header>

      <main class="content">
        <div class="content-inner">
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { DataLine, Location, Search, Picture, Lightning, List, Timer } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import { logout } from '@/api/auth'

const userStore = useUserStore()
const router = useRouter()
const route = useRoute()

const pageTitle = computed(() => {
  const titles = {
    '/dashboard': '仪表盘',
    '/status': '状态历史',
    '/trajectory': '轨迹地图',
    '/yolo-detection': 'YOLO在线检测',
    '/detection': '检测记录',
    '/laser': '激光控制',
    '/laser-logs': '操作日志'
  }
  return titles[route.path] || '激光除草机器人'
})

async function handleLogout() {
  await logout()
  userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<style scoped>
.layout-shell {
  display: grid;
  grid-template-columns: 268px minmax(0, 1fr);
  gap: 16px;
  height: 100vh;
  padding: 16px;
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
  font-size: 17px;
  white-space: nowrap;
  font-weight: 700;
  letter-spacing: 0.03em;
  color: var(--text-primary);
}

.menu {
  flex: 1;
  min-height: 0;
  border-right: none;
}

.menu :deep(.el-menu-item) {
  color: var(--menu-text) !important;
  font-weight: 500;
  border-radius: 14px;
  margin: 6px 0;
}

.menu :deep(.el-menu-item:hover) {
  color: var(--text-primary) !important;
  background: var(--interactive-hover) !important;
}

.menu :deep(.el-menu-item.is-active) {
  color: var(--accent-cyan) !important;
  background: var(--interactive-hover) !important;
}

.menu :deep(.el-menu-item .el-icon) {
  color: var(--text-secondary) !important;
}

.menu :deep(.el-menu-item:hover .el-icon) {
  color: var(--text-primary) !important;
}

.menu :deep(.el-menu-item.is-active .el-icon) {
  color: var(--accent-cyan) !important;
}

.user-info {
  padding-top: 16px;
  border-top: 1px solid var(--line-soft);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.user-detail-item {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.user-detail-item .label {
  color: var(--text-secondary);
}

.user-detail-item .value {
  color: var(--text-primary);
  font-weight: 500;
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
  font-weight: 700;
  letter-spacing: 0.03em;
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

@media (max-width: 1180px) {
  .layout-shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    display: none;
  }
}
</style>
