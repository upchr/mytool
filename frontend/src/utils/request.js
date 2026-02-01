import axios from 'axios'

// 创建实例
const service = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
    timeout: 10000,
    withCredentials: true // 如需跨域携带 cookie
})

// 请求拦截器
service.interceptors.request.use(
    (config) => {
        // 可添加 token
        // const token = localStorage.getItem('token')
        // if (token) config.headers.Authorization = `Bearer ${token}`
        return config
    },
    (error) => Promise.reject(error)
)

// 响应拦截器
service.interceptors.response.use(
    (response) => {
        const { code, message, data } = response.data

        if (code === 200) {
            return data // 直接返回 data，调用方无需 .data.data
        } else {
            window.$message.error(message || '请求失败')
            return Promise.reject(new Error(message))
        }
    },
    (error) => {
        if (error.response) {
            const { status, data } = error.response
            let msg = '请求失败'
            if (status === 401) {
                msg = '未授权，请重新登录'
                // 可跳转登录页
            } else if (status === 403) {
                msg = '权限不足'
            } else if (status === 422 && data?.message) {
                msg = data.message
            } else if (data?.message) {
                msg = data.message
            }
            window.$message.error(msg)
        } else if (error.code === 'ECONNABORTED') {
            window.$message.error('请求超时')
        } else {
            window.$message.error('网络异常，请检查连接')
        }
        return Promise.reject(error)
    }
)

export default service
