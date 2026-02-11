// src/main.js
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './assets/main.css'

// Pinia
import { createPinia } from 'pinia'
const pinia = createPinia()

// 创建 Vue App
const app = createApp(App)
app.use(pinia)
app.use(router)

// 全局挂载 Naive UI 离散组件
import { setupDiscreteApi } from '@/utils/message.js'
setupDiscreteApi(app)

// 挂载 axios 请求工具
import request from '@/utils/request'
window.$request = request

// 挂载复制工具
import { copyWithMessage } from '@/utils/clipboard'
window.$copyCode = copyWithMessage

// 挂载主题 store
import { useThemeStore } from '@/stores/theme'
window.$themeStore = useThemeStore()

// 挂载 App
app.mount('#app')
