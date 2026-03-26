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

    <!-- 日志弹窗 -->
    <n-modal v-model:show="showLogs" preset="card" title="📋 容器日志" style="width: 80vw">
      <n-space vertical>
        <n-input
          v-model:value="tailLines"
          type="number"
          placeholder="显示行数"
          style="width: 120px"
        >
          <template #prefix>行数：</template>
        </n-input>
        <n-code :code="containerLogs" language="text" style="max-height: 60vh; overflow: auto" />
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
      <div class="terminal-container">
        <div ref="terminalRef" class="terminal"></div>
      </div>
      <n-space style="margin-top: 12px">
        <n-button @click="showTerminal = false">关闭</n-button>
      </n-space>
    </n-modal>
  </n-card>
</template>

<script setup>
import { ref, computed, onMounted, h } from 'vue'
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

// 日志
const showLogs = ref(false)
const containerLogs = ref('')
const tailLines = ref(200)
const currentContainerId = ref('')

// Compose 编辑器
const showComposeEditor = ref(false)
const composePath = ref('')
const composeContent = ref('')
const isNewCompose = ref(false)
const saving = ref(false)

// 终端
const showTerminal = ref(false)
const terminalRef = ref(null)
let wsTerminal = null

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
    await Promise.all([loadContainers(), loadComposeProjects()])
  } finally {
    loading.value = false
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

// 加载 Compose 项目
const loadComposeProjects = async () => {
  try {
    const res = await window.$request.get(`/docker/nodes/${selectedNodeId.value}/compose`)
    composeProjects.value = res || []
  } catch (error) {
    console.error('加载 Compose 项目失败:', error)
  }
}

// 容器操作
const handleContainerAction = async (containerId, action) => {
  try {
    await window.$request.post(`/docker/nodes/${selectedNodeId.value}/containers/action`, {
      action,
      container_id: containerId
    })
    window.$message.success(`容器 ${containerId} 已${action}`)
    loadContainers()
  } catch (error) {
    window.$message.error(`操作失败: ${error.message || error}`)
  }
}

// 查看日志
const viewLogs = async (containerId) => {
  currentContainerId.value = containerId
  try {
    const res = await window.$request.get(
      `/docker/nodes/${selectedNodeId.value}/containers/${containerId}/logs`,
      { params: { tail: tailLines.value } }
    )
    containerLogs.value = res.logs || '无日志'
    showLogs.value = true
  } catch (error) {
    window.$message.error('获取日志失败')
  }
}

// 打开终端
const openTerminal = async (containerId) => {
  currentContainerId.value = containerId
  showTerminal.value = true
  
  // 等待 DOM 更新后初始化终端
  await new Promise(resolve => setTimeout(resolve, 100))
  initTerminal(containerId)
}

// 初始化终端 WebSocket
const initTerminal = (containerId) => {
  const wsUrl = `${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}/api/docker/nodes/${selectedNodeId.value}/containers/${containerId}/terminal`
  
  wsTerminal = new WebSocket(wsUrl)
  
  wsTerminal.onopen = () => {
    console.log('终端连接成功')
  }
  
  wsTerminal.onmessage = (event) => {
    if (terminalRef.value) {
      terminalRef.value.innerHTML += event.data
      terminalRef.value.scrollTop = terminalRef.value.scrollHeight
    }
  }
  
  wsTerminal.onerror = (error) => {
    console.error('终端错误:', error)
    window.$message.error('终端连接失败')
  }
  
  wsTerminal.onclose = () => {
    console.log('终端连接关闭')
  }
  
  // 键盘输入
  terminalRef.value?.addEventListener('keydown', (e) => {
    if (wsTerminal?.readyState === WebSocket.OPEN) {
      wsTerminal.send(JSON.stringify({ input: e.key }))
      e.preventDefault()
    }
  })
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
    loadComposeProjects()
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
.terminal-container {
  background: #1e1e1e;
  border-radius: 4px;
  padding: 12px;
  min-height: 400px;
}

.terminal {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
  color: #d4d4d4;
  white-space: pre-wrap;
  word-break: break-all;
  min-height: 400px;
  outline: none;
}
</style>
