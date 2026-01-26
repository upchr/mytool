// src/main.js
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './assets/main.css'
// 👇 引入 Naive UI 核心
import { createDiscreteApi } from 'naive-ui'

const app = createApp(App)

// 创建离散 API（Message, Notification, Dialog 等）
const { message, notification, dialog } = createDiscreteApi(['message', 'notification', 'dialog'])
// 挂载到全局
window.$message = message
window.$notification = notification
window.$dialog = dialog

// 复制
import { copyWithMessage} from '@/utils/clipboard'
window.$copyCode = copyWithMessage

// 引入并创建 Pinia 实例
import { createPinia } from 'pinia'
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.mount('#app')
