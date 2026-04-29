import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/auth/LoginView.vue'),
      meta: { public: true, title: '系统登录' },
    },
    {
      path: '/',
      component: () => import('@/layout/AdminLayout.vue'),
      children: [
        { path: '', redirect: '/overview' },
        { path: 'overview', name: 'overview', component: () => import('@/views/dashboard/HomeView.vue'), meta: { title: '平台总览' } },
        { path: 'data-overview', redirect: '/analysis' },
        { path: 'data', name: 'data', component: () => import('@/views/data/DataManagementView.vue'), meta: { title: '数据管理' } },
        { path: 'sync-management', name: 'sync-management', component: () => import('@/views/system/SyncManagementView.vue'), meta: { admin: true, title: '数据同步' } },
        { path: 'analysis', name: 'analysis', component: () => import('@/views/analysis/AnalysisView.vue'), meta: { title: '数据分析' } },
        { path: 'country-analysis', name: 'country-analysis', component: () => import('@/views/analysis/CountryAnalysisView.vue'), meta: { title: '国家专题' } },
        { path: 'map', name: 'map', component: () => import('@/views/map/FireMapView.vue'), meta: { title: '三维地图', immersive: true, cache: false } },
        { path: 'glossary', name: 'glossary', component: () => import('@/views/help/GlossaryView.vue'), meta: { title: '术语说明' } },
        { path: 'fire-detail/:id', name: 'fire-detail', component: () => import('@/views/fire/FireDetailView.vue'), meta: { title: '火点详情', cache: false } },
        { path: 'users', name: 'users', component: () => import('@/views/system/UserManagementView.vue'), meta: { admin: true, title: '用户管理' } },
      ],
    },
    {
      path: '/screen',
      name: 'screen',
      component: () => import('@/views/screen/ScreenView.vue'),
      meta: { title: '数据大屏' },
    },
    {
      path: '/demo',
      name: 'demo',
      component: () => import('@/views/screen/ScreenView.vue'),
      meta: { title: '演示模式', demo: true },
    },
  ],
})

router.beforeEach(async (to) => {
  const store = useAuthStore()
  if (to.meta.public) {
    if (store.isLoggedIn && to.path === '/login') {
      return '/overview'
    }
    return true
  }
  if (!store.isLoggedIn) {
    return '/login'
  }
  if (!store.profile) {
    try {
      await store.fetchProfile()
    } catch (error) {
      store.clearSession()
      return '/login'
    }
  }
  if (to.meta.admin && !store.isAdmin) {
    return '/overview'
  }
  return true
})

export default router
