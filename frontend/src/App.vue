<template>
  <!-- 登录页面不显示侧边栏布局 -->
  <div id="app">
    <MainLayout v-if="$route.path !== '/login'" />
    <router-view v-else />
  </div>
</template>

<script setup>
import MainLayout from '@/layout/MainLayout.vue'
import { useRoute } from 'vue-router'

const route = useRoute()
</script>
