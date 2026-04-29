import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store/user'
import Login from '@/views/Login.vue'
import Dashboard from '@/views/Dashboard.vue'
import StatusHistory from '@/views/StatusHistory.vue'
import TrajectoryMap from '@/views/TrajectoryMap.vue'
import YoloDetection from '@/views/YoloDetection.vue'
import DetectionRecords from '@/views/DetectionRecords.vue'
import LaserControlPanel from '@/views/LaserControlPanel.vue'
import LaserLogs from '@/views/LaserLogs.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true, title: '仪表盘' }
  },
  {
    path: '/status',
    name: 'StatusHistory',
    component: StatusHistory,
    meta: { requiresAuth: true, title: '状态历史' }
  },
  {
    path: '/trajectory',
    name: 'TrajectoryMap',
    component: TrajectoryMap,
    meta: { requiresAuth: true, title: '轨迹地图' }
  },
  {
    path: '/yolo-detection',
    name: 'YoloDetection',
    component: YoloDetection,
    meta: { requiresAuth: true, title: 'YOLO在线检测' }
  },
  {
    path: '/detection',
    name: 'DetectionRecords',
    component: DetectionRecords,
    meta: { requiresAuth: true, title: '检测记录' }
  },
  {
    path: '/laser',
    name: 'LaserControl',
    component: LaserControlPanel,
    meta: { requiresAuth: true, title: '激光控制', requiresAdmin: true }
  },
  {
    path: '/laser-logs',
    name: 'LaserLogs',
    component: LaserLogs,
    meta: { requiresAuth: true, title: '激光操作日志', requiresAdmin: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next('/login')
  } else if (to.meta.requiresAdmin && userStore.role.toUpperCase() !== 'ADMIN') {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
