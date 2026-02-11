// src/utils/request.js
import axios from 'axios'
import {clearAuthToken, getAuthToken} from './auth'
import { useLoginStore } from '@/stores/login.js'

let isHandling401 = false


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
        if (response.config.responseType === 'blob') {
            return response;
        }
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
            const { status, data } = error.response
            let msg = `${data.message}:${data.data}`
            const loginStore = useLoginStore()
            if (status === 403 && data?.detail === "系统未初始化") {
                // 触发初始化弹框
                loginStore.openInitDialog()
                // window.dispatchEvent(new CustomEvent('showInitDialog'))
            } else if (status === 401) {
                console.log(isHandling401)
                if (!isHandling401) {
                    isHandling401 = true
                    clearAuthToken()
                    setTimeout(() => {
                        loginStore.openLoginDialog()
                        // window.dispatchEvent(new CustomEvent('showLoginDialog'))
                        isHandling401=false
                    }, 450)
                    window.$message.error(msg)
                }
                return Promise.reject(error)
            } else if (status === 403) {
                // msg = '权限不足'
            }
            window.$message.error(msg)
        } else {
            window.$message.error('网络异常，请检查连接')
        }
        return Promise.reject(error)
    }
)

// 导出文件功能
const exportFile = async (url, params = {}, fileName = 'export.json') => {
    try {
        // 发送请求，获取 Blob 格式的数据
        const response = await service.get(url, {
            params: params,      // 如果需要传递查询参数，使用 params
            responseType: 'blob' // 设置响应类型为 Blob
        });
        debugger

        // 创建一个临时的下载链接
        const urlBlob = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = urlBlob;
        link.setAttribute('download', fileName); // 设置文件名
        document.body.appendChild(link);
        link.click();  // 模拟点击下载
        document.body.removeChild(link); // 下载完成后移除链接

        window.URL.revokeObjectURL(urlBlob);  // 释放 Blob 对象
        window.$message.success('导出成功');
    } catch (error) {
        const errorMessage = error.response?.data?.detail || error.message || '导出失败';
        window.$message.error(`导出失败: ${errorMessage}`);
    }
};

export default {
    ...service,
    exportFile
};

