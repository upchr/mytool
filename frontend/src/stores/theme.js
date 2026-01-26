// stores/theme.js
import { defineStore } from 'pinia'
import { ref, computed, onScopeDispose } from 'vue'
import { darkTheme } from 'naive-ui'

const STORAGE_KEY = 'app-theme-preference'

export const useThemeStore = defineStore('theme', () => {
    // 用户手动设置的主题偏好（'dark' | 'light' | null）
    const userPreference = ref(localStorage.getItem(STORAGE_KEY))

    // 系统当前主题
    const systemIsDark = ref(window.matchMedia('(prefers-color-scheme: dark)').matches)

    // 最终生效的主题（用于 Naive UI）
    const theme = computed(() => {
        if (userPreference.value === 'dark') return darkTheme
        if (userPreference.value === 'light') return null
        // 跟随系统
        return systemIsDark.value ? darkTheme : null
    })

    // 监听系统主题变化
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const onSystemChange = (e) => {
        systemIsDark.value = e.matches
        // 系统变化时自动清除用户偏好
        clearUserPreference()
    }

    mediaQuery.addEventListener('change', onSystemChange)
    onScopeDispose(() => {
        mediaQuery.removeEventListener('change', onSystemChange)
    })

    // 切换主题（用户操作）
    const toggleTheme = () => {
        const current = userPreference.value || (systemIsDark.value ? 'dark' : 'light')
        const next = current === 'dark' ? 'light' : 'dark'
        setUserPreference(next)
    }

    // 设置用户偏好
    const setUserPreference = (preference) => {
        userPreference.value = preference
        localStorage.setItem(STORAGE_KEY, preference)
    }

    // 清除用户偏好（恢复跟随系统）
    const clearUserPreference = () => {
        userPreference.value = null
        localStorage.removeItem(STORAGE_KEY)
    }

    return {
        theme,
        toggleTheme,
        isDark: computed(() => theme.value?.name === 'dark')
    }
})
