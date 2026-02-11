// src/utils/message.js
import { createDiscreteApi, darkTheme, lightTheme } from 'naive-ui'
import { watch } from 'vue'
import { useThemeStore } from '@/stores/theme'

let discreteApi = null

export function setupDiscreteApi(app) {
    const themeStore = useThemeStore()

    const createApi = () => {
        const api = createDiscreteApi(
            ['message', 'notification', 'dialog'],
            {
                app,
                configProviderProps: {
                    theme: themeStore.isDark ? darkTheme : lightTheme
                }
            }
        )
        window.$message = api.message
        window.$notification = api.notification
        window.$dialog = api.dialog
        return api
    }

    // 首次创建
    if (!discreteApi) {
        discreteApi = createApi()
    }

    // 监听主题变化，重新创建
    watch(
        () => themeStore.isDark,
        () => {
            discreteApi = createApi()
        }
    )
}

export function getDiscreteApi() {
    return discreteApi
}
