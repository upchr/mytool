// src/main.js
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './assets/main.css'
// 👇 引入 Naive UI 核心
import { createDiscreteApi } from 'naive-ui'

const app = createApp(App)

// 👇 创建离散 API（Message, Notification, Dialog 等）
const { message, notification, dialog } = createDiscreteApi(['message', 'notification', 'dialog'])

// 挂载到全局属性（方便在组件中通过 getCurrentInstance 使用）
app.config.globalProperties.$message = message
app.config.globalProperties.$notification = notification
app.config.globalProperties.$dialog = dialog

app.use(router)
app.mount('#app')
