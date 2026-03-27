// src/utils/auth.js
// 检查系统是否已初始化
import {useLoginStore} from "@/stores/login.js";

export async function checkSystemInitialized() {
    try {
        const response = await window.$request.get('/sys/init/check')
        return response.is_initialized
    } catch (error) {
        console.error('检查系统初始化状态失败:', error)
        return false
    }
}

// 初始化系统
export async function initializeSystem(password) {
    try {
        const response = await window.$request.post('/sys/init/setup', { password })
        window.$message.success('系统初始化成功！')
        return true
    } catch (error) {
        const msg = error.response?.data?.detail || '初始化失败'
        window.$message.error(msg)
        return false
    }
}

// 登录系统
export async function loginSystem(password) {
    try {
        const response = await window.$request.post('/sys/login', { password })
        
        console.log('登录响应:', response)
        
        // 注意：request.js 拦截器在 code === 200 时只返回 data
        // 所以 response 实际上是 { token: "xxx", remaining_attempts: null }
        if (response && response.token) {
            localStorage.setItem('admin_token', response.token)
            console.log('Token已保存:', response.token)
            return {
                success: true,
                remaining_attempts: response.remaining_attempts
            }
        }
        
        // 失败响应：拦截器会抛出异常，不会到这里
        console.log('登录失败，无token')
        return {
            success: false,
            message: '登录失败'
        }
    } catch (error) {
        // 异常响应：error.response.data = { code: 422, message: "密码错误", data: "..." }
        const errorData = error.response?.data
        const msg = errorData?.message || errorData?.detail || '登录失败'
        console.error('登录失败:', error)
        return {
            success: false,
            message: msg,
            detail: errorData?.data
        }
    }
}

// 重置密码
export async function resetPassword(oldPassword, newPassword) {
    try {
        const response = await window.$request.post('/sys/resetPassword', { 
            old_password: oldPassword,
            password: newPassword 
        })
        clearAuthToken()
        window.$message.success('修改成功，请重新登录！')
        useLoginStore().openLoginDialog()
        return true
    } catch (error) {
        const msg = error.response?.data?.detail || '修改失败'
        window.$message.error(msg)
        return false
    }
}

// 退出登录
export function logoutSystem() {
    localStorage.removeItem('admin_token')
    window.$message.success('已退出登录')
}

// 获取当前 token
export function getAuthToken() {
    return localStorage.getItem('admin_token')
}

// 清除 token
export function clearAuthToken() {
    localStorage.removeItem('admin_token')
}
