<template>
  <n-card title="🐳 Docker 管理" class="mb-6">
    <!-- 节点选择 -->
    <n-space align="center" style="margin-bottom: 16px" :wrap="true">
      <n-text>选择节点：</n-text>
      <n-select
        v-model:value="selectedNodeId"
        :options="nodeOptions"
        placeholder="请选择节点"
        style="min-width: 120px; max-width: 200px; flex: 1"
        @update:value="loadDockerData"
      />
      <n-button v-if="selectedNodeId" @click="loadDockerData" :loading="loading">
        刷新
      </n-button>
    </n-space>

    <template v-if="selectedNodeId">
      <!-- Tab 切换 -->
      <n-tabs v-model:value="activeTab" type="line" @update:value="handleTabChange" :size="isMobile ? 'small' : 'medium'">
        <!-- 容器列表 -->
        <n-tab-pane name="containers" tab="容器列表">
          <n-data-table
            :columns="containerColumns"
            :data="containers"
            :loading="loading"
            :row-key="row => row.id"
            :size="isMobile ? 'small' : 'medium'"
          />
        </n-tab-pane>

        <!-- Compose 项目 -->
        <n-tab-pane name="compose" tab="Compose 项目">
          <n-space style="margin-bottom: 12px" :wrap="true">
            <n-button type="primary" @click="createComposeProject" :size="isMobile ? 'small' : 'medium'">
              新建项目
            </n-button>
          </n-space>
          <n-data-table
            :columns="composeColumns"
            :data="composeProjects"
            :loading="loading"
            :row-key="row => row.path"
            :size="isMobile ? 'small' : 'medium'"
          />
        </n-tab-pane>

        <!-- 操作日志 -->
        <n-tab-pane name="logs" tab="操作日志">
          <n-data-table
            :columns="logColumns"
            :data="operationLogs"
            :loading="loadingLogs"
            :row-key="row => row.id"
            :size="isMobile ? 'small' : 'medium'"
          />
        </n-tab-pane>
      </n-tabs>
    </template>

    <n-empty v-else description="请先选择一个节点" />

    <!-- 日志弹窗 - WebSocket 实时 -->
    <n-modal v-model:show="showLogs" preset="card" title="📋 容器日志（实时）" :style="{ width: modalWidth }">
      <n-space vertical>
        <n-space align="center" :wrap="true">
          <n-switch v-model:value="logsFollowing" @update:value="toggleLogsFollow">
            <template #checked>实时跟踪</template>
            <template #unchecked>暂停</template>
          </n-switch>
          <n-button size="small" @click="clearLogs">清空</n-button>
        </n-space>
        <div class="logs-container">
          <pre ref="logsRef" class="logs-content">{{ containerLogs }}</pre>
        </div>
      </n-space>
    </n-modal>

    <!-- Compose 编辑器弹窗 -->
    <n-modal v-model:show="showComposeEditor" preset="card" :title="composeEditorTitle" :style="{ width: modalWidth }">
      <n-space vertical>
        <n-form-item label="项目路径">
          <n-input v-model:value="composePath" placeholder="/opt/docker-compose/myapp" />
        </n-form-item>
        <n-form-item label="docker-compose.yml">
          <div :style="{ width: '100%', height: editorHeight }">
            <MonacoEditor
              v-model:value="composeContent"
              language="yaml"
              :options="{
                minimap: { enabled: false },
                fontSize: isMobile.value ? 12 : 14,
                lineNumbers: 'on'
              }"
            />
          </div>
        </n-form-item>
        <n-space justify="end" :wrap="true">
          <n-button @click="showComposeEditor = false">取消</n-button>
          <n-button type="primary" @click="saveComposeFile" :loading="saving">保存</n-button>
          <n-button type="success" @click="composeUp" :loading="saving">保存并启动</n-button>
        </n-space>
      </n-space>
    </n-modal>

    <!-- 终端弹窗 -->
    <n-modal v-model:show="showTerminal" preset="card" title="💻 容器终端" :style="{ width: modalWidth }">
      <div class="terminal-container" tabindex="0" ref="terminalContainer" @keydown="handleTerminalKeydown">
        <pre ref="terminalRef" class="terminal-output">{{ terminalOutput }}</pre>
      </div>
      <n-space style="margin-top: 12px" :wrap="true">
        <n-text depth="3">直接输入命令，按回车执行</n-text>
        <n-button @click="showTerminal = false">关闭</n-button>
      </n-space>
    </n-modal>
  </n-card>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, h, nextTick } from 'vue'
import { NButton, NTag, NSpace, NPopconfirm, NIcon, NDropdown } from 'naive-ui'
import { Play, StopCircle, Refresh, TrashOutline, TerminalOutline, DocumentTextOutline, CreateOutline, EllipsisHorizontalOutline } from '@vicons/ionicons5'
import MonacoEditor from '@/components/MonacoEditor.vue'
import { dockerApi } from './api'

// ========== 响应式屏幕宽度 ==========
const screenWidth = ref(window.innerWidth)
const isMobile = computed(() => screenWidth.value < 768)
const isTablet = computed(() => screenWidth.value >= 768 && screenWidth.value < 1024)

// 弹窗响应式宽度
const modalWidth = computed(() => {
  if (isMobile.value) return '95vw'
  if (isTablet.value) return '70vw'
  return '80vw'
})

// 编辑器响应式高度
const editorHeight = computed(() => {
  if (isMobile.value) return '300px'
  return '400px'
})

// 监听窗口大小变化
const handleResize = () => {
  screenWidth.value = window.innerWidth
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

// ========== 节点相关 ==========
const nodes = ref([])
const selectedNodeId = ref(null)
const nodeOptions = computed(() =>
  nodes.value
    .filter(n => n.is_active)
    .map(n => ({ label: n.name, value: n.id }))
)

// ========== 数据 ==========
const containers = ref([])
const composeProjects = ref([])
const operationLogs = ref([])
const loading = ref(false)
const loadingLogs = ref(false)
const activeTab = ref('containers')

// ========== 日志 - WebSocket ==========
const showLogs = ref(false)
const containerLogs = ref('')
const logsRef = ref(null)
const logsFollowing = ref(true)
const logsWs = ref(null)
const currentContainerId = ref('')

// ========== Compose 编辑器 ==========
const showComposeEditor = ref(false)
const composePath = ref('')
const composeContent = ref('')
const isNewCompose = ref(false)
const saving = ref(false)

// ========== 终端 - WebSocket ==========
const showTerminal = ref(false)
const terminalRef = ref(null)
const terminalContainer = ref(null)
const terminalOutput = ref('')
const terminalWs = ref(null)

// ========== 加载节点列表 ==========
const loadNodes = async () => {
  try {
    const res = await window.$request.get('/nodes/only_active/false')
    nodes.value = res || []
  } catch (error) {
    console.error('加载节点失败:', error)
    window.$message.error('加载节点失败')
  }
}

// ========== 加载 Docker 数据 ==========
const loadDockerData = async () => {
  if (!selectedNodeId.value) return
  
  loading.value = true
  try {
    // 并行加载容器和 Compose 项目
    const [containersRes, composeRes] = await Promise.all([
      dockerApi.getContainers(selectedNodeId.value),
      dockerApi.getComposeProjects(selectedNodeId.value)
    ])
    containers.value = containersRes || []
    composeProjects.value = composeRes || []
  } catch (error) {
    console.error('加载数据失败:', error)
    window.$message.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

// ========== 加载操作日志 ==========
const loadOperationLogs = async () => {
  if (!selectedNodeId.value) return
  
  loadingLogs.value = true
  try {
    const res = await dockerApi.getOperationLogs(selectedNodeId.value, 100)
    operationLogs.value = res || []
  } catch (error) {
    console.error('加载操作日志失败:', error)
    window.$message.error('加载操作日志失败')
  } finally {
    loadingLogs.value = false
  }
}

// ========== 容器操作 ==========
const handleContainerAction = async (containerId, action) => {
  try {
    const res = await dockerApi.containerActionAsync(
      selectedNodeId.value,
      containerId,
      action
    )
    window.$message.success(res.message || `容器 ${containerId} 正在${action}...`)
    
    // 延迟刷新列表
    setTimeout(() => loadContainers(), 1500)
  } catch (error) {
    console.error('容器操作失败:', error)
    window.$message.error(`操作失败: ${error.message || error}`)
  }
}

// ========== 加载容器列表 ==========
const loadContainers = async () => {
  try {
    const res = await dockerApi.getContainers(selectedNodeId.value)
    containers.value = res || []
  } catch (error) {
    console.error('加载容器失败:', error)
  }
}

// ========== 查看日志 - WebSocket 实时 ==========
const viewLogs = (containerId) => {
  currentContainerId.value = containerId
  containerLogs.value = ''
  showLogs.value = true
  logsFollowing.value = true
  
  startLogsStream(containerId)
}

const startLogsStream = (containerId) => {
  // 关闭旧连接
  if (logsWs.value) {
    logsWs.value.close()
  }
  
  logsWs.value = dockerApi.createLogsWebSocket(
    selectedNodeId.value,
    containerId,
    200,
    true
  )
  
  logsWs.value.onopen = () => {
    console.log('日志 WebSocket 已连接')
  }
  
  logsWs.value.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.log) {
        containerLogs.value += data.log
        // 自动滚动到底部
        nextTick(() => {
          if (logsRef.value) {
            logsRef.value.scrollTop = logsRef.value.scrollHeight
          }
        })
      } else if (data.done) {
        containerLogs.value += '\n[日志流结束]\n'
      } else if (data.error) {
        containerLogs.value += `\n[错误: ${data.error}]\n`
      }
    } catch (e) {
      containerLogs.value += event.data
    }
  }
  
  logsWs.value.onerror = (error) => {
    console.error('日志 WebSocket 错误:', error)
  }
  
  logsWs.value.onclose = () => {
    console.log('日志 WebSocket 已关闭')
  }
}

const toggleLogsFollow = (value) => {
  // 暂停/恢复日志接收
}

const clearLogs = () => {
  containerLogs.value = ''
}

// ========== 打开终端 ==========
const openTerminal = async (containerId) => {
  currentContainerId.value = containerId
  terminalOutput.value = ''
  showTerminal.value = true
  
  await nextTick()
  
  startTerminal(containerId)
  
  terminalContainer.value?.focus()
}

const startTerminal = (containerId) => {
  // 关闭旧连接
  if (terminalWs.value) {
    terminalWs.value.close()
  }
  
  terminalWs.value = dockerApi.createTerminalWebSocket(
    selectedNodeId.value,
    containerId,
    'sh'
  )
  
  terminalWs.value.onopen = () => {
    console.log('终端 WebSocket 已连接')
    terminalOutput.value += '[已连接到容器终端]\n'
  }
  
  terminalWs.value.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.output) {
        terminalOutput.value += data.output
        nextTick(() => {
          if (terminalRef.value) {
            terminalRef.value.scrollTop = terminalRef.value.scrollHeight
          }
        })
      } else if (data.error) {
        terminalOutput.value += `\n[错误: ${data.error}]\n`
      }
    } catch (e) {
      terminalOutput.value += event.data
    }
  }
  
  terminalWs.value.onerror = (error) => {
    console.error('终端 WebSocket 错误:', error)
    window.$message.error('终端连接失败')
  }
  
  terminalWs.value.onclose = () => {
    console.log('终端 WebSocket 已关闭')
    terminalOutput.value += '\n[连接已关闭]\n'
  }
}

// ========== 处理终端键盘输入 ==========
const handleTerminalKeydown = (e) => {
  if (!terminalWs.value || terminalWs.value.readyState !== WebSocket.OPEN) {
    return
  }
  
  e.preventDefault()
  
  let input = ''
  
  // 处理特殊键
  if (e.key === 'Enter') {
    input = '\r'
  } else if (e.key === 'Backspace') {
    input = '\b'
  } else if (e.key === 'Tab') {
    input = '\t'
  } else if (e.key === 'ArrowUp') {
    input = '\x1b[A'
  } else if (e.key === 'ArrowDown') {
    input = '\x1b[B'
  } else if (e.key === 'ArrowRight') {
    input = '\x1b[C'
  } else if (e.key === 'ArrowLeft') {
    input = '\x1b[D'
  } else if (e.ctrlKey) {
    const key = e.key.toLowerCase()
    if (key === 'c') {
      input = '\x03'
    } else if (key === 'd') {
      input = '\x04'
    } else if (key === 'l') {
      input = '\x0c'
    } else if (key === 'z') {
      input = '\x1a'
    }
  } else if (e.key.length === 1) {
    input = e.key
  }
  
  if (input) {
    terminalWs.value.send(JSON.stringify({ input }))
  }
}

// ========== Compose 相关 ==========
const composeEditorTitle = computed(() =>
  isNewCompose.value ? '新建 Compose 项目' : `编辑: ${composePath.value}`
)

const createComposeProject = () => {
  isNewCompose.value = true
  composePath.value = ''
  composeContent.value = `version: '3.8'

services:
  app:
    image: nginx:latest
    ports:
      - "80:80"
    restart: unless-stopped
`
  showComposeEditor.value = true
}

const editComposeProject = async (project) => {
  isNewCompose.value = false
  composePath.value = project.path
  
  try {
    const res = await dockerApi.getComposeFile(selectedNodeId.value, project.path)
    composeContent.value = res.content
    showComposeEditor.value = true
  } catch (error) {
    console.error('加载文件失败:', error)
    window.$message.error('加载文件失败')
  }
}

const saveComposeFile = async () => {
  if (!composePath.value) {
    window.$message.warning('请输入项目路径')
    return
  }
  
  saving.value = true
  try {
    await dockerApi.saveComposeFile(
      selectedNodeId.value,
      composePath.value,
      composeContent.value
    )
    window.$message.success('保存成功')
    showComposeEditor.value = false
    loadDockerData()
  } catch (error) {
    console.error('保存失败:', error)
    window.$message.error('保存失败')
  } finally {
    saving.value = false
  }
}

const composeUp = async () => {
  await saveComposeFile()
  if (!showComposeEditor.value) {
    await handleComposeAction(composePath.value, 'up')
  }
}

const handleComposeAction = async (path, action) => {
  try {
    const res = await dockerApi.composeAction(selectedNodeId.value, path, action)
    window.$message.success(res.message || '操作成功')
    loadDockerData()
  } catch (error) {
    console.error('Compose 操作失败:', error)
    window.$message.error(`操作失败: ${error.message || error}`)
  }
}

// ========== 清理 WebSocket 连接 ==========
onUnmounted(() => {
  if (logsWs.value) {
    logsWs.value.close()
  }
  if (terminalWs.value) {
    terminalWs.value.close()
  }
})

// ========== 表格列定义 ==========
// 容器操作下拉菜单
const getContainerActionDropdown = (row) => [
  {
    label: row.state === 'running' ? '停止' : '启动',
    key: 'toggle',
    icon: () => h(NIcon, null, { default: () => h(row.state === 'running' ? StopCircle : Play) }),
    props: {
      onClick: () => handleContainerAction(row.id, row.state === 'running' ? 'stop' : 'start')
    }
  },
  {
    label: '重启',
    key: 'restart',
    icon: () => h(NIcon, null, { default: () => h(Refresh) }),
    props: {
      onClick: () => handleContainerAction(row.id, 'restart')
    }
  },
  {
    label: '日志',
    key: 'logs',
    icon: () => h(NIcon, null, { default: () => h(DocumentTextOutline) }),
    props: {
      onClick: () => viewLogs(row.id)
    }
  },
  {
    label: '终端',
    key: 'terminal',
    icon: () => h(NIcon, null, { default: () => h(TerminalOutline) }),
    props: {
      onClick: () => openTerminal(row.id)
    }
  },
  {
    type: 'divider'
  },
  {
    label: '删除',
    key: 'remove',
    icon: () => h(NIcon, null, { default: () => h(TrashOutline) }),
    props: {
      onClick: () => {
        window.$dialog.warning({
          title: '确认删除',
          content: '确定要删除此容器吗？',
          positiveText: '确定',
          negativeText: '取消',
          onPositiveClick: () => handleContainerAction(row.id, 'remove')
        })
      }
    }
  }
]

const containerColumns = computed(() => {
  const columns = []

  // 移动端不显示容器ID
  if (!isMobile.value) {
    columns.push({
      title: '容器 ID',
      key: 'id',
      width: 120
    })
  }

  columns.push({
    title: '名称',
    key: 'name',
    width: isMobile.value ? 100 : 150,
    ellipsis: { tooltip: true }
  })

  columns.push({
    title: '镜像',
    key: 'image',
    width: isMobile.value ? 150 : 200,
    ellipsis: { tooltip: true }
  })

  columns.push({
    title: '状态',
    key: 'state',
    width: isMobile.value ? 80 : 100,
    render: (row) => h(NTag, {
      type: row.state === 'running' ? 'success' : 'warning',
      size: isMobile.value ? 'small' : 'medium'
    }, { default: () => row.status })
  })

  // 移动端不显示端口
  if (!isMobile.value) {
    columns.push({
      title: '端口',
      key: 'ports',
      width: 150,
      ellipsis: { tooltip: true }
    })
  }

  columns.push({
    title: '操作',
    key: 'actions',
    width: isMobile.value ? 80 : 280,
    fixed: isMobile.value ? 'right' : undefined,
    render: (row) => {
      if (isMobile.value) {
        // 移动端显示下拉菜单
        return h(NButton, {
          size: 'small',
          circle: true,
          onClick: (e) => {
            e.stopPropagation()
          }
        }, {
          icon: () => h(NIcon, null, { default: () => h(EllipsisHorizontalOutline) }),
          default: () => null
        })
      } else {
        // 桌面端显示所有按钮
        return h(NSpace, {}, {
          default: () => [
            h(NButton, {
              size: 'small',
              type: row.state === 'running' ? 'warning' : 'success',
              onClick: () => handleContainerAction(row.id, row.state === 'running' ? 'stop' : 'start')
            }, {
              icon: () => h(NIcon, null, { default: () => h(row.state === 'running' ? StopCircle : Play) }),
              default: () => row.state === 'running' ? '停止' : '启动'
            }),
            h(NButton, {
              size: 'small',
              type: 'info',
              onClick: () => handleContainerAction(row.id, 'restart')
            }, {
              icon: () => h(NIcon, null, { default: () => h(Refresh) }),
              default: () => '重启'
            }),
            h(NButton, {
              size: 'small',
              onClick: () => viewLogs(row.id)
            }, {
              icon: () => h(NIcon, null, { default: () => h(DocumentTextOutline) }),
              default: () => '日志'
            }),
            h(NButton, {
              size: 'small',
              type: 'primary',
              onClick: () => openTerminal(row.id)
            }, {
              icon: () => h(NIcon, null, { default: () => h(TerminalOutline) }),
              default: () => '终端'
            }),
            h(NPopconfirm, {
              onPositiveClick: () => handleContainerAction(row.id, 'remove')
            }, {
              trigger: () => h(NButton, { size: 'small', type: 'error' }, {
                icon: () => h(NIcon, null, { default: () => h(TrashOutline) })
              }),
              default: () => '确定删除此容器？'
            })
          ]
        })
      }
    }
  })

  return columns
})

// Compose 操作下拉菜单
const getComposeActionDropdown = (row) => [
  {
    label: '启动',
    key: 'up',
    icon: () => h(NIcon, null, { default: () => h(Play) }),
    props: {
      onClick: () => handleComposeAction(row.path, 'up')
    }
  },
  {
    label: '停止',
    key: 'down',
    icon: () => h(NIcon, null, { default: () => h(StopCircle) }),
    props: {
      onClick: () => handleComposeAction(row.path, 'down')
    }
  },
  {
    label: '重启',
    key: 'restart',
    icon: () => h(NIcon, null, { default: () => h(Refresh) }),
    props: {
      onClick: () => handleComposeAction(row.path, 'restart')
    }
  },
  {
    type: 'divider'
  },
  {
    label: '编辑',
    key: 'edit',
    icon: () => h(NIcon, null, { default: () => h(CreateOutline) }),
    props: {
      onClick: () => editComposeProject(row)
    }
  }
]

const composeColumns = computed(() => {
  const columns = []

  columns.push({
    title: '项目名称',
    key: 'name',
    width: isMobile.value ? 120 : 200,
    ellipsis: { tooltip: true }
  })

  columns.push({
    title: '路径',
    key: 'path',
    width: isMobile.value ? 150 : 300,
    ellipsis: { tooltip: true }
  })

  // 移动端不显示服务数和状态
  if (!isMobile.value) {
    columns.push({
      title: '服务数',
      key: 'services',
      width: 80
    })

    columns.push({
      title: '状态',
      key: 'status',
      width: 100
    })
  }

  columns.push({
    title: '操作',
    key: 'actions',
    width: isMobile.value ? 80 : 300,
    fixed: isMobile.value ? 'right' : undefined,
    render: (row) => {
      if (isMobile.value) {
        // 移动端显示下拉菜单
        return h(NButton, {
          size: 'small',
          circle: true,
          onClick: (e) => {
            e.stopPropagation()
          }
        }, {
          icon: () => h(NIcon, null, { default: () => h(EllipsisHorizontalOutline) }),
          default: () => null
        })
      } else {
        // 桌面端显示所有按钮
        return h(NSpace, {}, {
          default: () => [
            h(NButton, {
              size: 'small',
              type: 'success',
              onClick: () => handleComposeAction(row.path, 'up')
            }, { default: () => '启动' }),
            h(NButton, {
              size: 'small',
              type: 'warning',
              onClick: () => handleComposeAction(row.path, 'down')
            }, { default: () => '停止' }),
            h(NButton, {
              size: 'small',
              type: 'info',
              onClick: () => handleComposeAction(row.path, 'restart')
            }, { default: () => '重启' }),
            h(NButton, {
              size: 'small',
              onClick: () => editComposeProject(row)
            }, {
              icon: () => h(NIcon, null, { default: () => h(CreateOutline) }),
              default: () => '编辑'
            })
          ]
        })
      }
    }
  })

  return columns
})

const logColumns = computed(() => {
  const columns = []

  // 移动端简化时间显示
  columns.push({
    title: '时间',
    key: 'created_at',
    width: isMobile.value ? 120 : 180,
    render: (row) => {
      const date = new Date(row.created_at)
      if (isMobile.value) {
        return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      }
      return date.toLocaleString('zh-CN')
    }
  })

  columns.push({
    title: '操作类型',
    key: 'operation_type',
    width: isMobile.value ? 80 : 100,
    ellipsis: { tooltip: true }
  })

  // 移动端合并操作和动作
  if (isMobile.value) {
    columns.push({
      title: '操作',
      key: 'action',
      width: 80
    })
  } else {
    columns.push({
      title: '操作',
      key: 'action',
      width: 100
    })

    columns.push({
      title: '目标',
      key: 'target',
      width: 200,
      ellipsis: { tooltip: true }
    })
  }

  columns.push({
    title: '状态',
    key: 'status',
    width: isMobile.value ? 60 : 80,
    render: (row) => h(NTag, {
      type: row.status === 'success' ? 'success' : 'error',
      size: isMobile.value ? 'small' : 'medium'
    }, { default: () => row.status === 'success' ? '成功' : '失败' })
  })

  columns.push({
    title: '消息',
    key: 'message',
    ellipsis: { tooltip: true }
  })

  return columns
})

// ========== 监听 Tab 切换 ==========
const handleTabChange = (name) => {
  if (name === 'logs' && operationLogs.value.length === 0) {
    loadOperationLogs()
  }
}

// ========== 初始化 ==========
onMounted(() => {
  loadNodes()
})
</script>

<style scoped>
.logs-container {
  background: #1e1e1e;
  border-radius: 4px;
  padding: 12px;
  max-height: 60vh;
  overflow: auto;
}

.logs-content {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  color: #d4d4d4;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
}

.terminal-container {
  background: #1e1e1e;
  border-radius: 4px;
  padding: 12px;
  min-height: 400px;
  outline: none;
  cursor: text;
}

.terminal-container:focus {
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.terminal-output {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
  color: #d4d4d4;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  min-height: 400px;
}

/* 移动端响应式样式 */
@media (max-width: 768px) {
  .logs-container {
    padding: 8px;
    max-height: 50vh;
  }

  .logs-content {
    font-size: 11px;
  }

  .terminal-container {
    padding: 8px;
    min-height: 300px;
  }

  .terminal-output {
    font-size: 12px;
    min-height: 300px;
  }
}

/* 平板响应式样式 */
@media (min-width: 769px) and (max-width: 1024px) {
  .logs-content {
    font-size: 12px;
  }

  .terminal-output {
    font-size: 13px;
  }
}
</style>
