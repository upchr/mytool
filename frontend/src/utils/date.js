export function formatDate(date = new Date()) {
    const pad = (n) => String(n).padStart(2, '0')

    const y = date.getFullYear()
    const m = pad(date.getMonth() + 1)
    const d = pad(date.getDate())
    const h = pad(date.getHours())
    const mi = pad(date.getMinutes())
    const s = pad(date.getSeconds())

    return `${y}${m}${d}_${h}${mi}${s}`
}

export const formatDateNotice = (isoString) => {
    const date = new Date(isoString)
    return date.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    })
}
