<template>
  <n-card title="💾 数据管理" class="mb-6">
    <n-space justify="end" style="margin-bottom: 10px">
<!--      <n-popconfirm :negative-text="null"
                    positive-text="清空数据"
                    :positive-button-props="{ type: 'error', size: 'small'}"
                    @positive-click="clearDatabase"
      >
        <template #icon>
          <n-icon color="red">
            <DeleteIcon />
          </n-icon>
        </template>
        <template #trigger>
          <n-button type="error">清空数据</n-button>
        </template>
        一切都将一去杳然，任何人都无法将其捕获。
      </n-popconfirm>-->
      <n-button type="error"
          @click="clearData">
        清空数据
      </n-button>
      <n-button
          type="primary"
          @click="exportDatabase"
          :loading="exporting"
      >
        导出数据库
      </n-button>
    </n-space>

    <n-space vertical>

      <n-upload
          multiple
          directory-dnd
          @change="handleFileChange"
          accept=".json"
          :max="1"
      >
        <n-upload-dragger>
          <div style="margin-bottom: 12px">
            <n-icon size="48" :depth="3">
              <ArchiveIcon />
            </n-icon>
          </div>
          <n-text style="font-size: 16px">
            点击或者拖动文件到该区域来上传
          </n-text>
        </n-upload-dragger>
      </n-upload>


      <!-- 操作提示 -->
      <n-alert type="warning" class="mt-4">
        <template #icon>
          <n-icon><WarningOutline /></n-icon>
        </template>
        清除数据库，重新开始。清除前，系统会自动创建备份文件（应用data目录下）。
      </n-alert>
      <n-alert type="warning" class="mt-4">
        <template #icon>
          <n-icon><WarningOutline /></n-icon>
        </template>
        导入操作会<strong>覆盖当前数据库</strong>，系统会自动创建备份文件（应用data目录下）。
      </n-alert>
    </n-space>
  </n-card>
</template>

<script setup>
import {h, ref} from 'vue'
import {useMessage, useDialog,useNotification , NIcon} from 'naive-ui'
import { WarningOutline } from '@vicons/ionicons5'
import axios from 'axios'
import {
  ArchiveOutline as ArchiveIcon,
  FitnessOutline as DeleteIcon
} from '@vicons/ionicons5'

const message = useMessage()
const exporting = ref(false)
const importing = ref(false)
const selectedFile = ref(null)

// 导出数据库
const exportDatabase = async () => {
  try {
    exporting.value = true
    const response = await axios.get('/api/database/export', {
      responseType: 'blob'
    })

    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `database_export_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    message.success('数据库导出成功')
  } catch (error) {
    message.error(`导出失败: ${error.response?.data?.detail || error.message}`)
  } finally {
    exporting.value = false
  }
}
const notification = useNotification()

const dialog = useDialog()

function clearData() {
  dialog.error({
    title: '清空数据',
    content: '一切都将一去杳然，任何人都无法将其捕获。',
    positiveText: '清空',
    icon:renderIcon(DeleteIcon),
    onPositiveClick: () => {
      clearDatabase()
    }
  })
}
function renderIcon(icon) {
  return () => h(icon,  { color: 'red' });
}

// 清除数据库
const clearDatabase = async () => {
  try {
    const response = await axios.delete('/api/database/clear')
    notification.success({
      title: '清除成功！',
      content: `原库备份文件: ${response.data.backup_file}`,
      duration: 5000,
      keepAliveOnHover: true
    })
  } catch (error) {
    message.error(`清除失败: ${error.response?.data?.detail || error.message}`)
  }
}

// 处理文件选择
const handleFileChange = (data) => {
  if (data.fileList.length > 0) {
    selectedFile.value = data.fileList[0].file
  } else {
    selectedFile.value = null
  }
  importDatabase()
}

// 导入数据库
const importDatabase = async () => {
  if (!selectedFile.value) return

  try {
    importing.value = true

    const formData = new FormData()
    formData.append('file', selectedFile.value)

    const response = await axios.post('/api/database/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    notification.success({
      title: '导入成功！',
      content: `原库备份文件: ${response.data.backup_file}`,
      duration: 5000,
      keepAliveOnHover: true
    })
    selectedFile.value = null
  } catch (error) {
    message.error(`导入失败: ${error.response?.data?.detail || error.message}`)
  } finally {
    importing.value = false
  }
}
</script>
