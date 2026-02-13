<!-- src/components/DownloadModal.vue -->
<template>
  <DialogForm
      ref="dialogRef"
      dialogPreset="card"
      v-model:visible="visible"
      type="warning"
      title="导出完成"
      :mask-closable="false"
      :closable="false"
      style="width: 10vw;height: 22vh"
  >
    <n-space vertical align="center">
      <n-text>请点击下方按钮下载文件</n-text>
    </n-space>
    <template #action="{ formData }">
      <n-space justify="center">
        <n-button @click="close" >
          取消
        </n-button>
        <a
            :href="dataUrl"
            :download="filename"
            style="text-decoration: none; width: 100%; text-align: center;"
        >
          <n-button type="info">
            下载
          </n-button>
        </a>
      </n-space>
    </template>
  </DialogForm>
</template>

<script setup>
import { defineProps, defineEmits, computed } from 'vue'
import { NSpace, NButton} from 'naive-ui'
import DialogForm from "@/components/DialogForm.vue";

const props = defineProps({
  visible: {
    type: Boolean,
    required: true
  },
  dataUrl: {
    type: String,
    default: ''
  },
  filename: {
    type: String,
    default: 'export.json'
  }
})

const emit = defineEmits(['update:visible'])

// 计算属性确保 visible 状态同步
const visible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

const close = () => {
  visible.value = false
}
</script>

<style scoped>
/* 如果需要额外样式，可以在这里添加 */
/* 但 Naive UI 组件已经包含了完整的主题支持 */
</style>
