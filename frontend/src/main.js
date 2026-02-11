// src/main.js
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './assets/main.css'

// 👇 引入 Naive UI 核心
import { createDiscreteApi } from 'naive-ui'

// 创建 Vue App
const app = createApp(App)

// 1️⃣ 挂载 Pinia
import { createPinia } from 'pinia'
const pinia = createPinia()
app.use(pinia)

// 2️⃣ 挂载 Router
app.use(router)

// 3️⃣ 创建离散 API，并传入 app，这样能继承全局主题
const { message, notification, dialog } = createDiscreteApi(
    ['message', 'notification', 'dialog'],
    { app } // 🔹关键：传入 app
)
// 挂载到全局
window.$message = message
window.$notification = notification
window.$dialog = dialog

// 4️⃣ 挂载 axios 请求工具
import request from '@/utils/request'
window.$request = request

// 5️⃣ 挂载复制工具
import { copyWithMessage } from '@/utils/clipboard'
window.$copyCode = copyWithMessage

// 6️⃣ 挂载主题 store
import { useThemeStore } from '@/stores/theme'
const themeStore = useThemeStore()
window.$themeStore = themeStore

// 7️⃣ 挂载 App
app.mount('#app')
