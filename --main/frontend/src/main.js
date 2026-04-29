import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import 'element-plus/dist/index.css'
import 'cesium/Build/Cesium/Widgets/widgets.css'
import './styles/global.css'

import App from './App.vue'
import router from './router'
import { useUiStore } from './stores/ui'

const app = createApp(App)
const pinia = createPinia()

Object.entries(ElementPlusIconsVue).forEach(([key, component]) => {
  app.component(key, component)
})

app.use(pinia)
app.use(router)
app.use(ElementPlus)

useUiStore(pinia).initializeTheme()

app.mount('#app')
