<template>
  <n-card title="🐳 Docker 管理" class="mb-6">
    <!-- 节点选择 -->
    <n-space align="center" style="margin-bottom: 16px">
      <n-text>选择节点：</n-text>
      <n-select
        v-model:value="selectedNodeId"
        :options="nodeOptions"
        placeholder="请选择节点"
        style="width: 200px"
        @update:value="loadDockerData"
      />
      <n-button v-if="selectedNodeId" @click="loadDockerData" :loading="loading">
        刷新
      </n-button>
    </n-space>

    <template v-if="selectedNodeId">
      <!-- Tab 切换 -->
      <n-tabs v-model:value="activeTab" type="line">
        <!-- 容器列表 -->
        <n-tab-pane name="containers" tab="容器列表">
          <n-data-table
            :columns="containerColumns"
            :data="containers"
            :loading="loading"
            :row-key="row => row.id"
          />
        </n-tab-pane>

        <!-- Compose 项目 -->
        <n-tab-pane name="compose" tab="Compose 项目">
          <n-space style="margin-bottom: 12px">
            <n-button type="primary" @click="createComposeProject">
              新建项目
            </n-button>
          </n-space>
          <n-data-table
            :columns="composeColumns"
            :data="composeProjects"
            :loading="loading"
            :row-key="row => row.path"
          />
        </n-tab-pane>
      </n-tabs>
    </template>

    <n-empty v-else description="请先选择一个节点" />

    <!-- 日志弹窗 - WebSocket 实时 -->
    <n-modal v-model:show="showLogs" preset="card" title="📋 容器日志（实时）" style="width: 80vw">
      <n-space vertical>
        <n-space align="center">
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
    <n-modal v-model:show="showComposeEditor" preset="card" :title="composeEditorTitle" style="width: 80vw">
      <n-space vertical>
        <n-form-item label="项目路径">
          <n-input v-model:value="composePath" placeholder="/opt/docker-compose/myapp" />
        </n-form-item>
        <n-form-item label="docker-compose.yml">
          <div style="width: 100%; height: 400px">
            <MonacoEditor
              v-model:value="composeContent"
              language="yaml"
              :options="{
                minimap: { enabled: false },
                fontSize: 14,
                lineNumbers: 'on'
              }"
            />
          </div>
        </n-form-item>
        <n-space justify="end">
          <n-button @click="showComposeEditor = false">取消</n-button>
          <n-button type="primary" @click="saveComposeFile" :loading="saving">保存</n-button>
          <n-button type="success" @click="composeUp" :loading="saving">保存并启动</n-button>
        </n-space>
      </n-space>
    </n-modal>

    <!-- 终端弹窗 -->
    <n-modal v-model:show="showTerminal" preset="card" title="💻 容器终端" style="width: 80vw">
      <div class="terminal-container" tabindex="0" ref="terminalContainer" @keydown="handleTerminalKeydown">
        <pre ref="terminalRef" class="terminal-output">{{ terminalOutput }}</pre>
      </div>
      <n-space style="margin-top: 12px">
        <n-text depth="3">直接输入命令，按回车执行</n-text>
        <n-button @click="showTerminal = false">关闭</n-button>
      </n-space>
    </n-modal>
  </n-card>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, h, nextTick } from 'vue'
import { NButton, NTag, NSpace, NPopconfirm, NIcon } from 'naive-ui'
import { Play, StopCircle, Refresh, TrashOutline, TerminalOutline, DocumentTextOutline, CreateOutline } from '@vicons/ionicons5'
import MonacoEditor from '@/components/MonacoEditor.vue'

// 节点相关
const nodes = ref([])
const selectedNodeId = ref(null)
const nodeOptions = computed(() =>
  nodes.value
    .filter(n => n.is_active)
    .map(n => ({ label: n.name, value: n.id }))
)

// 数据
const containers = ref([])
const composeProjects = ref([])
const loading = ref(false)
const activeTab = ref('containers')

// 日志 - WebSocket
const showLogs = ref(false)
const containerLogs = ref('')
const logsRef = ref(null)
const logsFollowing = ref(true)
const logsWs = ref(null)
const currentContainerId = ref('')

// Compose 编辑器
const showComposeEditor = ref(false)
const composePath = ref('')
const composeContent = ref('')
const isNewCompose = ref(false)
const saving = ref(false)

// 终端 - WebSocket
const showTerminal = ref(false)
const terminalRef = ref(null)
const terminalContainer = ref(null)
const terminalOutput = ref('')
const terminalWs = ref(null)
const terminalInputBuffer = ref('')

// 加载节点列表
const loadNodes = async () => {
  try {
    const res = await window.$request.get('/nodes/only_active/false')
    nodes.value = res
  } catch (error) {
    window.$message.error('加载节点失败')
  }
}

// 加载 Docker 数据
const loadDockerData = async () => {
  if (!selectedNodeId.value) return
  
  loading.value = true
  try {
    // 并行加载，使用快速接口
    const [containersRes, composeRes] = await Promise.all([
      window.$request.get(`/docker/nodes/${selectedNodeId.value}/containers`),
      window.$request.get(`/docker/nodes/${selectedNodeId.value}/compose`)
    ])
    containers.value = containersRes || []
    composeProjects.value = composeRes || []
  } catch (error) {
    window.$message.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

// 容器操作 - 异步立即返回
const handleContainerAction = async (containerId, action) => {
  try {
    // 使用异步接口
    const res = await window.$request.post(`/docker/nodes/${selectedNodeId.value}/containers/action/async`, {
      action,
      container_id: containerId
    })
    window.$message.success(res.message || `容器 ${containerId} 正在${action}...`)
    
    // 延迟刷新列表
    setTimeout(() => loadContainers(), 1500)
  } catch (error) {
    window.$message.error(`操作失败: ${error.message || error}`)
  }
}

// 加载容器列表
const loadContainers = async () => {
  try {
    const res = await window.$request.get(`/docker/nodes/${selectedNodeId.value}/containers`)
    containers.value = res || []
  } catch (error) {
    console.error('加载容器失败:', error)
  }
}

// 查看日志 - WebSocket 实时
const viewLogs = async (containerId) => {
  currentContainerId.value = containerId
  containerLogs.value = ''
  showLogs.value = true
  logsFollowing.value = true
  
  // 启动 WebSocket 连接
  startLogsStream(containerId)
}

const startLogsStream = (containerId) => {
  // 关闭旧连接
  if (logsWs.value) {
    logsWs.value.close()
  }
  
  const wsProtocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${wsProtocol}//${location.host}/api/docker/nodes/${selectedNodeId.value}/containers/${containerId}/logs/stream?tail=200&follow=true`
  
  logsWs.value = new WebSocket(wsUrl)
  
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
      // 如果不是 JSON，直接追加
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
  // 暂停/恢复日志接收可以在这里实现
}

const clearLogs = () => {
  containerLogs.value = ''
}

// 打开终端
const openTerminal = async (containerId) => {
  currentContainerId.value = containerId
  terminalOutput.value = ''
  terminalInputBuffer.value = ''
  showTerminal.value = true
  
  // 等待 DOM 更新
  await nextTick()
  
  // 启动 WebSocket 终端
  startTerminal(containerId)
  
  // 聚焦到终端容器
  terminalContainer.value?.focus()
}

const startTerminal = (containerId) => {
  // 关闭旧连接
  if (terminalWs.value) {
    terminalWs.value.close()
  }
  
  const wsProtocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${wsProtocol}//${location.host}/api/docker/nodes/${selectedNodeId.value}/containers/${containerId}/terminal`
  
  terminalWs.value = new WebSocket(wsUrl)
  
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

// 处理终端键盘输入
const handleTerminalKeydown = (e) => {
  if (!terminalWs.value || terminalWs.value.readyState !== WebSocket.OPEN) {
    return
  }
  
  // 阻止默认行为
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
    // Ctrl 组合键
    const key = e.key.toLowerCase()
    if (key === 'c') {
      input = '\x03'  // Ctrl+C
    } else if (key === 'd') {
      input = '\x04'  // Ctrl+D
    } else if (key === 'l') {
      input = '\x0c'  // Ctrl+L
    } else if (key === 'z') {
      input = '\x1a'  // Ctrl+Z
    }
  } else if (e.key.length === 1) {
    // 普通字符
    input = e.key
  }
  
  if (input) {
    terminalWs.value.send(JSON.stringify({ input }))
  }
}

// Compose 相关
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
    const res = await window.$request.get(
      `/docker/nodes/${selectedNodeId.value}/compose/file`,
      { params: { path: project.path } }
    )
    composeContent.value = res.content
    showComposeEditor.value = true
  } catch (error) {
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
    await window.$request.post(
      `/docker/nodes/${selectedNodeId.value}/compose/file`,
      { path: composePath.value, content: composeContent.value }
    )
    window.$message.success('保存成功')
    showComposeEditor.value = false
    loadDockerData()
  } catch (error) {
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
    const res = await window.$request.post(
      `/docker/nodes/${selectedNodeId.value}/compose/action`,
      { action, path }
    )
    window.$message.success(res.message || '操作成功')
    loadDockerData()
  } catch (error) {
    window.$message.error(`操作失败: ${error.message || error}`)
  }
}

// 清理 WebSocket 连接
onUnmounted(() => {
  if (logsWs.value) {
    logsWs.value.close()
  }
  if (terminalWs.value) {
    terminalWs.value.close()
  }
})

// 表格列定义
const containerColumns = [
  {
    title: '容器 ID',
    key: 'id',
    width: 120
  },
  {
    title: '名称',
    key: 'name',
    width: 150,
    ellipsis: { tooltip: true }
  },
  {
    title: '镜像',
    key: 'image',
    width: 200,
    ellipsis: { tooltip: true }
  },
  {
    title: '状态',
    key: 'state',
    width: 100,
    render: (row) => h(NTag, {
      type: row.state === 'running' ? 'success' : 'warning'
    }, { default: () => row.status })
  },
  {
    title: '端口',
    key: 'ports',
    width: 150,
    ellipsis: { tooltip: true }
  },
  {
    title: '操作',
    key: 'actions',
    width: 280,
    render: (row) => h(NSpace, {}, {
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
]

const composeColumns = [
  {
    title: '项目名称',
    key: 'name',
    width: 200
  },
  {
    title: '路径',
    key: 'path',
    width: 300,
    ellipsis: { tooltip: true }
  },
  {
    title: '服务数',
    key: 'services',
    width: 80
  },
  {
    title: '状态',
    key: 'status',
    width: 100
  },
  {
    title: '操作',
    key: 'actions',
    width: 300,
    render: (row) => h(NSpace, {}, {
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
]

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
</style>
