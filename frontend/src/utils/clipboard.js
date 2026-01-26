// utils/clipboard.js
/**
 * 复制文本到剪贴板（兼容移动端和 HTTP 环境）
 * @param {string} text - 要复制的文本
 * @returns {Promise<boolean>} - 是否复制成功
 */
export const copyToClipboard = async (text) => {
    if (!text) {
        console.warn('copyToClipboard: text is empty')
        return false
    }

    try {
        // 方案 A: 现代 API (HTTPS 环境)
        if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(text)
            return true
        }

        // 方案 B: 降级方案（创建临时 textarea）
        const textArea = document.createElement('textarea')
        textArea.value = text

        // 避免滚动跳动和视觉闪烁
        textArea.style.position = 'fixed'
        textArea.style.left = '-9999px'
        textArea.style.top = '-9999px'
        textArea.style.opacity = '0'
        textArea.setAttribute('readonly', '')

        document.body.appendChild(textArea)
        textArea.focus()
        textArea.select()

        const success = document.execCommand('copy')
        document.body.removeChild(textArea)

        return success
    } catch (error) {
        console.error('复制失败:', error)
        return false
    }
}

/**
 * 复制文本并显示 Naive UI 消息
 * @param {string} text - 要复制的文本
 * @param {Event} event - 事件对象（用于 stopPropagation）
 */
export const copyWithMessage = async (text, event=undefined) => {
    if (event) {
        event.stopPropagation?.()
    }

    const success = await copyToClipboard(text)

    if (success) {
        window.$message?.success('已复制到剪贴板')
    } else {
        window.$message?.error('复制失败，请手动复制')
    }

    return success
}
