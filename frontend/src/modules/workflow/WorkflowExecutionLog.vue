<template>
  <div class="workflow-execution-log">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <n-space align="center">
        <n-button quaternary @click="goBack">
          <template #icon>
            <n-icon><ArrowBackIcon /></n-icon>
          </template>
          返回
        </n-button>
        <n-divider vertical />
        <n-icon size="20" color="#18a058"><DocumentIcon /></n-icon>
        <n-text strong>{{ workflowName }}</n-text>
        <n-divider vertical />
        <n-tag :type="executionStatus === 'success' ? 'success' : (executionStatus === 'failed' ? 'error' : 'info')" size="medium">
          <template #icon>
            <n-icon v-if="executionStatus === 'success'"><CheckmarkCircleIcon /></n-icon>
            <n-icon v-else-if="executionStatus === 'failed'"><CloseCircleIcon /></n-icon>
            <n-icon v-else><TimeIcon /></n-icon>
          </template>
          {{ executionStatus === 'success' ? '执行成功' : (executionStatus === 'failed' ? '执行失败' : '执行中') }}
        </n-tag>
        <n-divider vertical />
        <n-space align="center" size="small">
          <n-icon size="16" color="#666"><TimeIcon /></n-icon>
          <n-text depth="3" style="font-size: 12px;">
            开始: {{ formatTime(execution.start_time) }}
            <span v-if="execution.end_time"> | 结束: {{ formatTime(execution.end_time) }}</span>
          </n-text>
        </n-space>
        <n-divider vertical />
        <n-button quaternary @click="zoomIn">
          <template #icon>
            <n-icon><AddIcon /></n-icon>
          </template>
          放大
        </n-button>
        <n-button quaternary @click="zoomOut">
          <template #icon>
            <n-icon><RemoveIcon /></n-icon>
          </template>
          缩小
        </n-button>
        <n-button quaternary @click="fitView">
          <template #icon>
            <n-icon><ExpandIcon /></n-icon>
          </template>
          适应
        </n-button>
      </n-space>
    </div>

    <div class="editor-body">
      <!-- 画布 -->
      <div class="canvas" ref="canvasRef">
        <VueFlow
          v-model:nodes="nodes"
          v-model:edges="edges"
          :min-zoom="0.2"
          :max-zoom="4"
          :fit-view-on-init="true"
          :fit-view-options="{ padding: 0.2, minZoom: 0.2, maxZoom: 1 }"
          @node-click="onNodeClick"
          @edge-click="onEdgeClick"
          :nodes-draggable="false"
          :nodes-connectable="false"
          :elements-selectable="false"
        >
          <Background />
          <Controls />

          <template #node-start="props">
            <div 
              class="wf-node start" 
              :class="{ 
                'executed': getNodeStatus(props.id) !== 'none',
                'success': getNodeStatus(props.id) === 'success',
                'failed': getNodeStatus(props.id) === 'failed',
                'running': getNodeStatus(props.id) === 'running',
                'selected': selectedId === props.id
              }"
            >
              <div class="content">🚀 {{ props.data.label }}</div>
              <div v-if="getNodeStatus(props.id) !== 'none'" class="status-badge">
                <n-tag :type="getNodeStatus(props.id) === 'success' ? 'success' : (getNodeStatus(props.id) === 'failed' ? 'error' : 'info')" size="small">
                  {{ getNodeStatusLabel(props.id) }}
                </n-tag>
              </div>
              <Handle type="source" :position="Position.Right" />
            </div>
          </template>

          <template #node-task="props">
            <div 
              class="wf-node task" 
              :class="{ 
                'executed': getNodeStatus(props.id) !== 'none',
                'success': getNodeStatus(props.id) === 'success',
                'failed': getNodeStatus(props.id) === 'failed',
                'running': getNodeStatus(props.id) === 'running',
                'selected': selectedId === props.id
              }"
            >
              <Handle type="target" :position="Position.Left" />
              <div class="content">⚙️ {{ props.data.label }}</div>
              <div v-if="getNodeStatus(props.id) !== 'none'" class="status-badge">
                <n-tag :type="getNodeStatus(props.id) === 'success' ? 'success' : (getNodeStatus(props.id) === 'failed' ? 'error' : 'info')" size="small">
                  {{ getNodeStatusLabel(props.id) }}
                </n-tag>
              </div>
              <Handle type="source" :position="Position.Right" />
            </div>
          </template>

          <template #node-condition="props">
            <div 
              class="wf-node condition" 
              :class="{ 
                'executed': getNodeStatus(props.id) !== 'none',
                'success': getNodeStatus(props.id) === 'success',
                'failed': getNodeStatus(props.id) === 'failed',
                'running': getNodeStatus(props.id) === 'running',
                'selected': selectedId === props.id
              }"
            >
              <Handle type="target" :position="Position.Left" />
              <div class="content">🔷 {{ props.data.label }}</div>
              <div v-if="getNodeStatus(props.id) !== 'none'" class="status-badge">
                <n-tag :type="getNodeStatus(props.id) === 'success' ? 'success' : (getNodeStatus(props.id) === 'failed' ? 'error' : 'info')" size="small">
                  {{ getNodeStatusLabel(props.id) }}
                </n-tag>
              </div>
              <Handle type="source" :position="Position.Right" />
            </div>
          </template>

          <template #node-wait="props">
            <div 
              class="wf-node wait" 
              :class="{ 
                'executed': getNodeStatus(props.id) !== 'none',
                'success': getNodeStatus(props.id) === 'success',
                'failed': getNodeStatus(props.id) === 'failed',
                'running': getNodeStatus(props.id) === 'running',
                'selected': selectedId === props.id
              }"
            >
              <Handle type="target" :position="Position.Left" />
              <div class="content">⏱️ {{ props.data.label }}</div>
              <div v-if="getNodeStatus(props.id) !== 'none'" class="status-badge">
                <n-tag :type="getNodeStatus(props.id) === 'success' ? 'success' : (getNodeStatus(props.id) === 'failed' ? 'error' : 'info')" size="small">
                  {{ getNodeStatusLabel(props.id) }}
                </n-tag>
              </div>
              <Handle type="source" :position="Position.Right" />
            </div>
          </template>

          <template #node-and="props">
            <div 
              class="wf-node and" 
              :class="{ 
                'executed': getNodeStatus(props.id) !== 'none',
                'success': getNodeStatus(props.id) === 'success',
                'failed': getNodeStatus(props.id) === 'failed',
                'running': getNodeStatus(props.id) === 'running',
                'selected': selectedId === props.id
              }"
            >
              <Handle type="target" :position="Position.Left" />
              <div class="content">🔗 {{ props.data.label }}</div>
              <div v-if="getNodeStatus(props.id) !== 'none'" class="status-badge">
                <n-tag :type="getNodeStatus(props.id) === 'success' ? 'success' : (getNodeStatus(props.id) === 'failed' ? 'error' : 'info')" size="small">
                  {{ getNodeStatusLabel(props.id) }}
                </n-tag>
              </div>
              <Handle type="source" :position="Position.Right" />
            </div>
          </template>

          <template #node-or="props">
            <div 
              class="wf-node or" 
              :class="{ 
                'executed': getNodeStatus(props.id) !== 'none',
                'success': getNodeStatus(props.id) === 'success',
                'failed': getNodeStatus(props.id) === 'failed',
                'running': getNodeStatus(props.id) === 'running',
                'selected': selectedId === props.id
              }"
            >
              <Handle type="target" :position="Position.Left" />
              <div class="content">🔀 {{ props.data.label }}</div>
              <div v-if="getNodeStatus(props.id) !== 'none'" class="status-badge">
                <n-tag :type="getNodeStatus(props.id) === 'success' ? 'success' : (getNodeStatus(props.id) === 'failed' ? 'error' : 'info')" size="small">
                  {{ getNodeStatusLabel(props.id) }}
                </n-tag>
              </div>
              <Handle type="source" :position="Position.Right" />
            </div>
          </template>

          <template #node-notification="props">
            <div 
              class="wf-node notification" 
              :class="{ 
                'executed': getNodeStatus(props.id) !== 'none',
                'success': getNodeStatus(props.id) === 'success',
                'failed': getNodeStatus(props.id) === 'failed',
                'running': getNodeStatus(props.id) === 'running',
                'selected': selectedId === props.id
              }"
            >
              <Handle type="target" :position="Position.Left" />
              <div class="content">📢 {{ props.data.label }}</div>
              <div v-if="getNodeStatus(props.id) !== 'none'" class="status-badge">
                <n-tag :type="getNodeStatus(props.id) === 'success' ? 'success' : (getNodeStatus(props.id) === 'failed' ? 'error' : 'info')" size="small">
                  {{ getNodeStatusLabel(props.id) }}
                </n-tag>
              </div>
              <Handle type="source" :position="Position.Right" />
            </div>
          </template>

          <template #node-end="props">
            <div 
              class="wf-node end" 
              :class="{ 
                'executed': getNodeStatus(props.id) !== 'none',
                'success': getNodeStatus(props.id) === 'success',
                'failed': getNodeStatus(props.id) === 'failed',
                'running': getNodeStatus(props.id) === 'running',
                'selected': selectedId === props.id
              }"
            >
              <Handle type="target" :position="Position.Left" />
              <div class="content">🏁 {{ props.data.label }}</div>
              <div v-if="getNodeStatus(props.id) !== 'none'" class="status-badge">
                <n-tag :type="getNodeStatus(props.id) === 'success' ? 'success' : (getNodeStatus(props.id) === 'failed' ? 'error' : 'info')" size="small">
                  {{ getNodeStatusLabel(props.id) }}
                </n-tag>
              </div>
            </div>
          </template>
        </VueFlow>
      </div>

      <!-- 右侧节点详情面板 -->
      <div class="right-panel" v-if="selectedNodeExecution">
        <n-card title="节点执行详情" size="small">
          <template #header-extra>
            <n-tag :type="selectedNodeExecution.status === 'success' ? 'success' : (selectedNodeExecution.status === 'failed' ? 'error' : 'info')" size="small">
              <template #icon>
                <n-icon v-if="selectedNodeExecution.status === 'success'"><CheckmarkCircleIcon /></n-icon>
                <n-icon v-else-if="selectedNodeExecution.status === 'failed'"><CloseCircleIcon /></n-icon>
                <n-icon v-else><TimeIcon /></n-icon>
              </template>
              {{ selectedNodeExecution.status === 'success' ? '成功' : (selectedNodeExecution.status === 'failed' ? '失败' : '进行中') }}
            </n-tag>
          </template>
          <n-descriptions :column="1" size="small" bordered>
            <n-descriptions-item label="节点名称">
              <n-space align="center">
                <n-icon size="16" color="#2080f0"><DocumentIcon /></n-icon>
                <n-text>{{ selectedNodeExecution.node_name }}</n-text>
              </n-space>
            </n-descriptions-item>
            <n-descriptions-item label="节点类型">
              <n-tag type="info" size="small">{{ selectedNodeExecution.node_type }}</n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="节点ID">
              <n-code :code="selectedNodeExecution.node_id" language="text" size="tiny" />
            </n-descriptions-item>
            <n-descriptions-item label="开始时间">
              <n-space align="center">
                <n-icon size="14" color="#666"><TimeIcon /></n-icon>
                <n-text depth="2">{{ formatTime(selectedNodeExecution.start_time) }}</n-text>
              </n-space>
            </n-descriptions-item>
            <n-descriptions-item label="结束时间">
              <n-space align="center">
                <n-icon size="14" color="#666"><TimeIcon /></n-icon>
                <n-text depth="2">{{ selectedNodeExecution.end_time ? formatTime(selectedNodeExecution.end_time) : '进行中' }}</n-text>
              </n-space>
            </n-descriptions-item>
            <n-descriptions-item label="执行时长">
              <n-tag :type="selectedNodeExecution.end_time ? 'default' : 'info'" size="small">
                {{ selectedNodeExecution.end_time ? calculateDuration(selectedNodeExecution.start_time, selectedNodeExecution.end_time) : '进行中' }}
              </n-tag>
            </n-descriptions-item>
          </n-descriptions>

          <div v-if="selectedNodeExecution.output" style="margin-top: 12px;">
            <n-space align="center" style="margin-bottom: 8px">
              <n-icon size="16" color="#18a058"><CheckmarkCircleIcon /></n-icon>
              <n-text strong style="font-size: 13px;">输出结果</n-text>
            </n-space>
            <n-code :code="selectedNodeExecution.output" language="text" :word-wrap="true" />
          </div>

          <div v-if="selectedNodeExecution.error" style="margin-top: 12px;">
            <n-space align="center" style="margin-bottom: 8px">
              <n-icon size="16" color="#d03050"><CloseCircleIcon /></n-icon>
              <n-text strong style="font-size: 13px;">错误信息</n-text>
            </n-space>
            <n-alert type="error" size="small" :bordered="false">
              {{ selectedNodeExecution.error }}
            </n-alert>
          </div>

          <div v-if="selectedNodeExecution.logs && selectedNodeExecution.logs.length > 0" style="margin-top: 12px;">
            <n-space align="center" style="margin-bottom: 8px">
              <n-icon size="16" color="#2080f0"><DocumentIcon /></n-icon>
              <n-text strong style="font-size: 13px;">执行日志</n-text>
              <n-tag size="tiny" type="info">{{ selectedNodeExecution.logs.length }} 条</n-tag>
            </n-space>
            <n-timeline size="small">
              <n-timeline-item
                v-for="(log, index) in selectedNodeExecution.logs"
                :key="index"
                :type="getLogType(log.type)"
                :time="log.timestamp"
              >
                <div 
                  style="padding: 6px 10px; background: #fafafa; border-radius: 6px; border-left: 3px solid #ccc;"
                  :style="{
                    'border-left-color': getLogBorderColor(log.type),
                    'background': getLogBackgroundColor(log.type)
                  }"
                >
                  <n-space align="center" style="margin-bottom: 4px">
                    <n-tag :type="getLogType(log.type)" size="tiny">
                      {{ getLogTypeLabel(log.type) }}
                    </n-tag>
                  </n-space>
                  <n-text 
                    depth="3" 
                    style="font-size: 12px; line-height: 1.6;"
                    :style="{
                      'font-weight': isNodeInfoLog(log.message) ? 'bold' : 'normal',
                      'color': isNodeInfoLog(log.message) ? '#2080f0' : ''
                    }"
                  >
                    {{ log.message }}
                  </n-text>
                </div>
              </n-timeline-item>
            </n-timeline>
          </div>
        </n-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { VueFlow, useVueFlow, Handle, Position } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import {
  ArrowBackOutline as ArrowBackIcon,
  DocumentOutline as DocumentIcon,
  CheckmarkCircleOutline as CheckmarkCircleIcon,
  CloseCircleOutline as CloseCircleIcon,
  TimeOutline as TimeIcon,
  AddOutline as AddIcon,
  RemoveOutline as RemoveIcon,
  ExpandOutline as ExpandIcon
} from '@vicons/ionicons5'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'

const router = useRouter()
const route = useRoute()
const { zoomIn, zoomOut, fitView } = useVueFlow()

const workflowId = computed(() => route.query.workflowId)
const executionId = computed(() => route.query.executionId ? parseInt(route.query.executionId) : null)

const workflowName = ref('')
const execution = ref({})
const nodeExecutions = ref([])
const nodes = ref([])
const edges = ref([])
const selectedId = ref(null)
const selectedNodeExecution = ref(null)

const executionStatus = computed(() => {
  return execution.value.status || 'running'
})

const getNodeStatus = (nodeId) => {
  const nodeExec = nodeExecutions.value.find(n => n.node_id === nodeId)
  if (!nodeExec) return 'none'
  return nodeExec.status
}

const getNodeStatusLabel = (nodeId) => {
  const status = getNodeStatus(nodeId)
  if (status === 'success') return '成功'
  if (status === 'failed') return '失败'
  if (status === 'running') return '进行中'
  return ''
}

const getEdgeStyle = (edge) => {
  const sourceStatus = getNodeStatus(edge.source)
  const targetStatus = getNodeStatus(edge.target)
  
  if (sourceStatus === 'success' && targetStatus !== 'none') {
    return {
      stroke: '#18a058',
      strokeWidth: 3,
      opacity: 1
    }
  } else if (sourceStatus === 'success') {
    return {
      stroke: '#18a058',
      strokeWidth: 2,
      opacity: 0.8
    }
  } else if (sourceStatus === 'failed') {
    return {
      stroke: '#d03050',
      strokeWidth: 2,
      opacity: 1
    }
  } else if (sourceStatus === 'running') {
    return {
      stroke: '#2080f0',
      strokeWidth: 2,
      opacity: 1
    }
  }
  
  return {
    stroke: '#ccc',
    strokeWidth: 1,
    opacity: 0.5
  }
}

const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const calculateDuration = (startTime, endTime) => {
  if (!startTime || !endTime) return ''
  const start = new Date(startTime)
  const end = new Date(endTime)
  const diff = end - start
  
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  
  if (hours > 0) {
    return `${hours}小时${minutes % 60}分钟`
  } else if (minutes > 0) {
    return `${minutes}分钟${seconds % 60}秒`
  } else {
    return `${seconds}秒`
  }
}

const getLogType = (type) => {
  const typeMap = {
    'info': 'default',
    'success': 'success',
    'failed': 'error',
    'error': 'error',
    'warning': 'warning',
    'condition': 'info',
    'route': 'info'
  }
  return typeMap[type] || 'default'
}

const getLogTypeLabel = (type) => {
  const labelMap = {
    'info': '信息',
    'success': '成功',
    'failed': '失败',
    'error': '错误',
    'warning': '警告',
    'condition': '条件',
    'route': '路由'
  }
  return labelMap[type] || type
}

const getLogBorderColor = (type) => {
  const colorMap = {
    'info': '#2080f0',
    'success': '#18a058',
    'failed': '#d03050',
    'error': '#d03050',
    'warning': '#f0a020',
    'condition': '#2080f0',
    'route': '#8a2be2'
  }
  return colorMap[type] || '#ccc'
}

const getLogBackgroundColor = (type) => {
  const bgMap = {
    'info': '#f0f9ff',
    'success': '#e8f5e9',
    'failed': '#fff1f0',
    'error': '#fff1f0',
    'warning': '#fffbe6',
    'condition': '#f0f9ff',
    'route': '#f5f0ff'
  }
  return bgMap[type] || '#fafafa'
}

const isNodeInfoLog = (message) => {
  return message.includes('前置节点:') || message.includes('后置节点:')
}

const onNodeClick = (event) => {
  const nodeId = event.node.id
  selectedId.value = nodeId
  selectedNodeExecution.value = nodeExecutions.value.find(n => n.node_id === nodeId) || null
}

const onEdgeClick = (event) => {
  console.log('Edge clicked:', event.edge)
}

const goBack = () => {
  router.back()
}

const loadData = async () => {
  if (!workflowId.value || !executionId.value) {
    window.$message.error('参数错误：缺少 workflowId 或 executionId')
    return
  }
  
  try {
    const [workflowRes, executionRes, nodesRes] = await Promise.all([
      window.$request.get(`/workflows/${workflowId.value}`),
      window.$request.get(`/workflows/executions/${executionId.value}`),
      window.$request.get(`/workflows/executions/${executionId.value}/nodes`)
    ])
    
    workflowName.value = workflowRes.name || ''
    execution.value = executionRes || {}
    nodeExecutions.value = nodesRes || []
    
    nodes.value = (workflowRes.nodes || []).map(node => ({
      ...node,
      type: node.type || 'task',
      position: node.position || { x: 0, y: 0 },
      data: node.data || { label: node.data?.label || node.data?.name || node.name || node.id }
    }))
    
    edges.value = (workflowRes.edges || []).map(edge => ({
      ...edge,
      style: getEdgeStyle(edge),
      animated: getNodeStatus(edge.source) === 'running'
    }))
  } catch (e) {
    window.$message.error('加载数据失败')
    console.error(e)
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.workflow-execution-log {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f5f5;
}

.toolbar {
  background: white;
  padding: 12px 16px;
  border-bottom: 1px solid #e0e0e0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.editor-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.canvas {
  flex: 1;
  background: white;
  position: relative;
}

.right-panel {
  width: 400px;
  background: white;
  border-left: 1px solid #e0e0e0;
  overflow-y: auto;
  padding: 16px;
}

.wf-node {
  padding: 8px 12px;
  border-radius: 8px;
  background: white;
  border: 2px solid #e0e0e0;
  min-width: 100px;
  max-width: 160px;
  text-align: center;
  position: relative;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.wf-node:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

.wf-node.executed {
  border-color: #18a058;
}

.wf-node.executed.success {
  border-color: #52c41a;
  background: linear-gradient(135deg, #f6ffed 0%, #fff 100%);
}

.wf-node.executed.failed {
  border-color: #ff4d4f;
  background: linear-gradient(135deg, #fff2f0 0%, #fff 100%);
}

.wf-node.executed.running {
  border-color: #1890ff;
  background: linear-gradient(135deg, #e6f7ff 0%, #fff 100%);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(32, 128, 240, 0.3);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(32, 128, 240, 0);
  }
}

.wf-node.selected {
  border-color: #2080f0;
  box-shadow: 0 0 0 3px rgba(32, 128, 240, 0.3);
  transform: scale(1.02);
}

.wf-node .content {
  font-size: 13px;
  font-weight: 500;
  color: #333;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding: 0 4px;
}

.wf-node .status-badge {
  margin-top: 6px;
}

.wf-node .status-badge :deep(.n-tag) {
  font-size: 11px;
  padding: 2px 6px;
  height: 20px;
  line-height: 16px;
}

.wf-node.start {
  background: linear-gradient(135deg, #e6fffa 0%, #fff 100%);
  color: #333;
  border-color: #52c41a;
}

.wf-node.start.executed {
  background: linear-gradient(135deg, #e6fffa 0%, #fff 100%);
  border: 2px solid #52c41a;
}

.wf-node.start.executed.failed {
  background: linear-gradient(135deg, #e6fffa 0%, #fff 100%);
  border: 2px solid #ff4d4f;
}

.wf-node.end {
  background: linear-gradient(135deg, #ffe8e6 0%, #fff 100%);
  color: #333;
  border-color: #ff4d4f;
}

.wf-node.end.executed {
  background: linear-gradient(135deg, #ffe8e6 0%, #fff 100%);
  border: 2px solid #18a058;
}

.wf-node.end.executed.failed {
  background: linear-gradient(135deg, #ffe8e6 0%, #fff 100%);
  border: 2px solid #d03050;
}

.wf-node.task {
  background: linear-gradient(135deg, #e3f2fd 0%, #fff 100%);
  color: #333;
  border-color: #1890ff;
}

.wf-node.task.executed {
  background: linear-gradient(135deg, #e3f2fd 0%, #fff 100%);
  border: 2px solid #18a058;
}

.wf-node.task.executed.failed {
  background: linear-gradient(135deg, #e3f2fd 0%, #fff 100%);
  border: 2px solid #d03050;
}

.wf-node.condition {
  background: linear-gradient(135deg, #ffe3e3 0%, #fff 100%);
  color: #333;
  border-color: #fa8c16;
}

.wf-node.condition.executed {
  background: linear-gradient(135deg, #ffe3e3 0%, #fff 100%);
  border: 2px solid #18a058;
}

.wf-node.condition.executed.failed {
  background: linear-gradient(135deg, #ffe3e3 0%, #fff 100%);
  border: 2px solid #d03050;
}

.wf-node.wait {
  background: linear-gradient(135deg, #f5f5f5 0%, #fff 100%);
  color: #333;
  border-color: #8c8c8c;
}

.wf-node.wait.executed {
  background: linear-gradient(135deg, #f5f5f5 0%, #fff 100%);
  border: 2px solid #18a058;
}

.wf-node.wait.executed.failed {
  background: linear-gradient(135deg, #f5f5f5 0%, #fff 100%);
  border: 2px solid #d03050;
}

.wf-node.and {
  background: linear-gradient(135deg, #d4f8e8 0%, #fff 100%);
  color: #333;
  border-color: #13c2c2;
}

.wf-node.and.executed {
  background: linear-gradient(135deg, #d4f8e8 0%, #fff 100%);
  border: 2px solid #18a058;
}

.wf-node.and.executed.failed {
  background: linear-gradient(135deg, #d4f8e8 0%, #fff 100%);
  border: 2px solid #d03050;
}

.wf-node.or {
  background: linear-gradient(135deg, #f8e8d4 0%, #fff 100%);
  color: #333;
  border-color: #eb2f96;
}

.wf-node.or.executed {
  background: linear-gradient(135deg, #f8e8d4 0%, #fff 100%);
  border: 2px solid #18a058;
}

.wf-node.or.executed.failed {
  background: linear-gradient(135deg, #f8e8d4 0%, #fff 100%);
  border: 2px solid #d03050;
}

.wf-node.notification {
  background: linear-gradient(135deg, #e8d4f8 0%, #fff 100%);
  color: #333;
  border-color: #722ed1;
}

.wf-node.notification.executed {
  background: linear-gradient(135deg, #e8d4f8 0%, #fff 100%);
  border: 2px solid #18a058;
}

.wf-node.notification.executed.failed {
  background: linear-gradient(135deg, #e8d4f8 0%, #fff 100%);
  border: 2px solid #d03050;
}
</style>
