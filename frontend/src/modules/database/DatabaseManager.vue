<template>
  <n-card title="数据库管理" :bordered="false">
    <n-space vertical :size="24">
      <!-- 导出功能 -->
      <n-card :bordered="false">
        <template #header>
          <n-space align="center">
            <n-icon><CloudDownloadOutline /></n-icon>
            <span>导出数据</span>
          </n-space>
        </template>

        <n-space vertical>
          <p class="text-gray-600">选择要导出的模块，或导出全部数据</p>

          <n-checkbox-group v-model:value="selectedExportModules">
            <n-space>
              <n-checkbox v-for="module in modules" :key="module.value" :value="module.value">
                {{ module.label }}
              </n-checkbox>
            </n-space>
          </n-checkbox-group>

          <n-space justify="end" class="mt-4">
            <n-button @click="exportAll">导出全部</n-button>
            <n-button type="primary" @click="exportSelected" :disabled="selectedExportModules.length === 0">
              导出选中
            </n-button>
          </n-space>
        </n-space>
      </n-card>

      <!-- 清除功能 -->
      <n-card :bordered="false">
        <template #header>
          <n-space align="center">
            <n-icon><TrashOutline /></n-icon>
            <span>清除数据</span>
          </n-space>
        </template>

        <n-space vertical>
          <p class="text-gray-600">选择要清除的模块数据</p>

          <n-checkbox-group v-model:value="selectedClearModules">
            <n-space>
              <n-checkbox v-for="module in modules" :key="module.value" :value="module.value">
                {{ module.label }}
              </n-checkbox>
            </n-space>
          </n-checkbox-group>

          <n-space justify="end" class="mt-4">
            <n-popconfirm
                @positive-click="clearSelected"
                negative-text="取消"
                positive-text="确认清除"
                :show-icon="false"
            >
              <template #trigger>
                <n-button type="error" :disabled="selectedClearModules.length === 0">
                  清除选中模块
                </n-button>
              </template>
              确定要清除选中模块的数据吗？此操作不可逆！
            </n-popconfirm>
          </n-space>
        </n-space>
      </n-card>

      <!-- 清空所有功能 -->
      <n-card :bordered="false">
        <template #header>
          <n-space align="center">
            <n-icon><CloseCircleOutline /></n-icon>
            <span>清空所有数据</span>
          </n-space>
        </template>

        <n-space vertical>
          <p class="text-gray-600">
            清空数据库中所有业务数据。
          </p>

          <n-form-item label-placement="left" label-width="120">
            <span style="margin-right: 10px">
              不保留系统表
            </span>
            <n-switch v-model:value="keepWhitelist">
              <template #checked-icon>
                <n-icon :component="ArrowForwardOutline" />
              </template>
              <template #unchecked-icon>
                <n-icon :component="ArrowBackOutline" />
              </template>
            </n-switch>
            <span style="margin-left: 10px">
              保留系统用户表等
            </span>
          </n-form-item>

          <n-space justify="end">
            <n-popconfirm
                @positive-click="clearAll"
                negative-text="取消"
                positive-text="确认清空"
                :show-icon="false"
            >
              <template #trigger>
                <n-button type="error">清空所有数据</n-button>
              </template>
              确定要清空所有数据吗？此操作不可逆！
            </n-popconfirm>
          </n-space>
        </n-space>
      </n-card>

      <!-- 导入功能 -->
      <n-card :bordered="false">
        <template #header>
          <n-space align="center">
            <n-icon><CloudUploadOutline /></n-icon>
            <span>导入数据</span>
          </n-space>
        </template>

        <n-space vertical>
          <p class="text-gray-600">
            上传之前导出的 JSON 文件进行数据还原。
            <br/>
            <span class="text-red-500 font-medium">注意：只会覆盖文件中包含的表数据</span>
          </p>

          <n-upload
              ref="uploadRef"
              :default-upload="false"
              @before-upload="handleBeforeUpload"
              :file-list="fileList"
              list-type="text"
              accept=".json"
          >
            <n-button type="primary">选择文件</n-button>
          </n-upload>

          <n-space justify="end" class="mt-4">
            <n-button type="success" @click="importData" :disabled="!selectedFile">
              导入数据
            </n-button>
          </n-space>
        </n-space>
      </n-card>
    </n-space>
  </n-card>
</template>

<script setup>
import {ref, onMounted} from 'vue'
import {
  CloudDownloadOutline,
  TrashOutline,
  CloseCircleOutline,
  CloudUploadOutline, ArrowForwardOutline, ArrowBackOutline
} from '@vicons/ionicons5'
import {formatDate} from '@/utils/date.js'
// 模块配置（与后端 MODULE_TABLES 保持一致）
const modules = ref([
 /* { value: 'nodes', label: '节点管理' },
  { value: 'jobs', label: '任务管理' },
  { value: 'credentials', label: '凭据模板' },
  { value: 'notifications', label: '通知配置' }*/
])

const selectedExportModules = ref([])
const selectedClearModules = ref([])
const keepWhitelist = ref(true)
const uploadRef = ref(null)
const fileList = ref([])
const selectedFile = ref(null)


//models
const getModels = async () => {
  modules.value = await window.$request.get(`/database/models`)
}

// 导出全部
const exportAll = async () => {
  try {
    await window.$request.exportFile('/database/export', {}, `database_export_all_${formatDate()}.json`)
  } catch (error) {
    window.$message.error(`导出失败`)
  }
}

// 导出选中模块
const exportSelected = async () => {
  if (selectedExportModules.value.length === 0) {
    window.$message.warning('请选择要导出的模块')
    return
  }

  try {
    const params = new URLSearchParams()
    selectedExportModules.value.forEach(module => {
      params.append('modules', module)
    })
    const moduleName = selectedExportModules.value.join('_')
    await window.$request.exportFile('/database/export', params, `database_export_${moduleName}_${formatDate()}.json`);
  } catch (error) {
    window.$message.error(`导出失败`)
  }
}

// 清除选中模块
const clearSelected = async () => {
  if (selectedClearModules.value.length === 0) {
    window.$message.warning('请选择要清除的模块')
    return
  }

  try {
    const params = new URLSearchParams()
    selectedClearModules.value.forEach(module => {
      params.append('modules', module)
    })

    await window.$request.delete(`/database/clear?${params.toString()}`)
    window.$message.success('清除成功')
    selectedClearModules.value = []
  } catch (error) {
    window.$message.error(`清除失败: ${error.response?.data?.detail || error.message}`)
  }
}

// 清空所有数据
const clearAll = async () => {
  try {
    const params = new URLSearchParams()
    params.append('keep_whitelist', keepWhitelist.value.toString())

    await window.$request.delete(`/database/clear?${params.toString()}`)
    window.$message.success('清空成功')
  } catch (error) {
    window.$message.error(`清空失败: ${error.response?.data?.detail || error.message}`)
  }
}

// 文件上传处理
const handleBeforeUpload = ({ file }) => {
  if (!file.name.endsWith('.json')) {
    window.$message.error('只支持 JSON 文件')
    return false
  }

  if (file.file.size > 50 * 1024 * 1024) {
    window.$message.error('文件大小不能超过 50MB')
    return false
  }

  selectedFile.value = file.file
  fileList.value = [file]
  return false // 阻止自动上传
}

// 导入数据
const importData = async () => {
  if (!selectedFile.value) {
    window.$message.warning('请选择要导入的文件')
    return
  }

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    const response = await window.$request.post('/database/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    window.$message.success('导入成功')
    fileList.value = []
    selectedFile.value = null

    // 可选：显示备份文件信息
    if (response.backup_file) {
      window.$dialog.info({
        title: '导入完成',
        content: `数据已成功导入\n备份文件: ${response.backup_file}`,
        positiveText: '确定'
      })
    }
  } catch (error) {
    window.$message.error(`导入失败`)
  }
}


onMounted(async () => {
  await getModels()
})
</script>

<style scoped>
.text-gray-600 {
  color: var(--text-color-2);
  font-size: 14px;
}

.ml-1 {
  margin-left: 4px;
}

.mt-4 {
  margin-top: 16px;
}

.ml-2 {
  margin-left: 8px;
}
</style>
