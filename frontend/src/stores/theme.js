// stores/theme.js
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { darkTheme, useOsTheme } from 'naive-ui'

export const useThemeStore = defineStore('theme', () => {
    const osTheme = useOsTheme()
    const theme = ref(null)

    const initTheme = () => {
        theme.value = osTheme.value === 'dark' ? darkTheme : null
    }

    const toggleTheme = () => {
        theme.value = theme.value?.name === 'dark' ? null : darkTheme
    }

    return { theme, initTheme, toggleTheme }
})
