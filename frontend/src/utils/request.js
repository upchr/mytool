// src/utils/request.js
import axios from 'axios'
import {clearAuthToken, getAuthToken} from './auth'
import { useLoginStore } from '@/stores/login.js'

let isHandling = false


const service = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
    timeout: 10000,
    withCredentials: true
})

service.interceptors.request.use((config) => {
    // 跳过认证的路径
    const publicPaths = ['/sys/init/check', '/sys/init/setup', '/sys/login', '/sys/health']
    if (!publicPaths.some(path => config.url.includes(path))) {
        const token = getAuthToken()
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
    }
    return config
})

service.interceptors.response.use(
    (response) => {
        if (response.data) {
            const { code, message, data } = response.data
            if (code === 200) {
                return data
            }else {
                window.$message.error(`${message || '请求失败'}${data ? ': ' + data : ''}`)
                return Promise.reject(new Error(message))
            }
        }
    },
    (error) => {
        if (error.response) {
            const { status } = error.response
            let data = error.response.data

            if (data instanceof Blob) {
                return data.text().then(text => {
                    try {
                        const json = JSON.parse(text)
                        return handleAuthError(status, json, error)
                    } catch (e) {
                        // 不是 JSON，说明真的是文件流或异常二进制
                        window.$message.error('文件下载失败')
                        return Promise.reject(error)
                    }
                })
            }

            // 正常 JSON
            return handleAuthError(status, data, error)
        }
        window.$message.error('网络异常，请检查连接')
        return Promise.reject(error)
    }

)
function handleAuthError(status, data, error) {
    const loginStore = useLoginStore()
    const msg = `${data?.message || ''}${data?.data ? ':' + data.data : ''}`

    if (status === 401 || status === 403) {
        if (!isHandling) {
            isHandling = true
            clearAuthToken()

            setTimeout(() => {
                if (status === 403) {
                    loginStore.openInitDialog()
                } else {
                    loginStore.openLoginDialog()
                }
                isHandling = false
            }, 450)

            window.$message.error(msg || '未授权')
            return new Promise(() => {})
        }else{
            return Promise.reject(error)
        }
    }

    window.$message.error(msg || '请求失败')
    return Promise.reject(error)
}

// 导出文件功能
const exportFile = async (url, params = {}, fileNameD = 'export.json') => {
    try {
        const response = await service.get(url, { params })
        const { filename, content } = response

        // 创建 Data URL（注意格式！）
        const dataUrl = `application/json;charset=utf-8;base64,${content}`

        // 调用 App.vue 中的方法显示下载按钮
        if (typeof window.showDownloadModal === 'function') {
            window.showDownloadModal(dataUrl, filename || fileNameD)
        } else {
            const link = document.createElement('a')
            link.href = dataUrl
            link.setAttribute('download', (filename===''||filename===undefined)?fileNameD:filename);
            document.body.appendChild(link)
            window.$message.success('导出成功')
        }

    } catch (error) {
        const errorMessage = error.response?.data?.detail || error.message || '导出失败'
        window.$message.error(`导出失败: ${errorMessage}`)
    }
}

export default {
    ...service,
    exportFile
};

