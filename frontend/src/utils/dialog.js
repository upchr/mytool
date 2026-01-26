// utils/dialog.js
import { h, ref } from 'vue'
import { NInput } from 'naive-ui'

export const prompt = (options = {}) => {
    const {
        title = '请输入',
        placeholder = '请输入内容',
        defaultValue = '',
        validate = (value) => !!value.trim(),
        validateMessage = '输入不能为空'
    } = options

    return new Promise((resolve, reject) => {
        const inputValue = ref(defaultValue)
        let dialogInstance = null

        // 提交函数
        const submit = () => {
            if (!validate(inputValue.value)) {
                window.$message.warning(validateMessage)
                return false // 返回 false 阻止关闭对话框
            }
            resolve(inputValue.value) // 这里返回输入的值
            return true // 返回 true 允许关闭对话框
        }

        // 创建对话框
        dialogInstance = window.$dialog.success({
            title,
            content: () =>
                h(NInput, {
                    placeholder,
                    value: inputValue.value,
                    onUpdateValue: (value) => {
                        inputValue.value = value
                    },
                    autofocus: true,
                    // 监听回车键
                    onKeyup: (e) => {
                        if (e.key === 'Enter') {
                            const canClose = submit()
                            if (canClose && dialogInstance) {
                                // 延迟关闭以确保 resolve 先执行
                                setTimeout(() => {
                                    dialogInstance.destroy?.()
                                }, 10)
                            }
                        }
                    }
                }),
            positiveText: '确定',
            negativeText: '取消',
            onPositiveClick: submit, // 点击确定按钮调用 submit
            onNegativeClick: () => {
                reject(new Error('cancelled'))
            },
            // 对话框关闭后的回调
            onAfterLeave: () => {
                // 可选：清理资源
            }
        })
    })
}
