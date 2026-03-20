<template>
  <div class="workflow-execution-log">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <n-space align="center">
        <n-button @click="goBack">← 返回</n-button>
        <n-divider vertical />
        <n-text strong>{{ workflowName }}</n-text>
        <n-divider vertical />
        <n-tag :type="executionStatus === 'success' ? 'success' : (executionStatus === 'failed' ? 'error' : 'info')">
          {{ executionStatus === 'success' ? '执行成功' : (executionStatus === 'failed' ? '执行失败' : '执行中') }}
        </n-tag>
        <n-divider vertical />
        <n-text depth="3" style="font-size: 12px;">
          开始时间: {{ formatTime(execution.start_time) }}
          <span v-if="execution.end_time"> | 结束时间: {{ formatTime(execution.end_time) }}</span>
        </n-text>
        <n-divider vertical />
        <n-button @click="zoomIn">放大</n-button>
        <n-button @click="zoomOut">缩小</n-button>
        <n-button @click="fitView">适应</n-button>
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
        <n-card title="📊 节点执行详情" size="small">
          <n-descriptions :column="1" size="small" bordered>
            <n-descriptions-item label="节点名称">{{ selectedNodeExecution.node_name }}</n-descriptions-item>
            <n-descriptions-item label="节点类型">{{ selectedNodeExecution.node_type }}</n-descriptions-item>
            <n-descriptions-item label="节点ID">{{ selectedNodeExecution.node_id }}</n-descriptions-item>
            <n-descriptions-item label="执行状态">
              <n-tag :type="selectedNodeExecution.status === 'success' ? 'success' : (selectedNodeExecution.status === 'failed' ? 'error' : 'info')">
                {{ selectedNodeExecution.status === 'success' ? '成功' : (selectedNodeExecution.status === 'failed' ? '失败' : '进行中') }}
              </n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="开始时间">{{ formatTime(selectedNodeExecution.start_time) }}</n-descriptions-item>
            <n-descriptions-item label="结束时间">{{ selectedNodeExecution.end_time ? formatTime(selectedNodeExecution.end_time) : '进行中' }}</n-descriptions-item>
            <n-descriptions-item label="执行时长">
              {{ selectedNodeExecution.end_time ? calculateDuration(selectedNodeExecution.start_time, selectedNodeExecution.end_time) : '进行中' }}
            </n-descriptions-item>
          </n-descriptions>

          <div v-if="selectedNodeExecution.output" style="margin-top: 12px;">
            <n-text depth="2" style="font-size: 12px; font-weight: bold; margin-bottom: 8px; display: block;">输出:</n-text>
            <n-code :code="selectedNodeExecution.output" language="text" :word-wrap="true" />
          </div>

          <div v-if="selectedNodeExecution.error" style="margin-top: 12px;">
            <n-alert type="error" size="small" title="错误信息">{{ selectedNodeExecution.error }}</n-alert>
          </div>

          <div v-if="selectedNodeExecution.logs && selectedNodeExecution.logs.length > 0" style="margin-top: 12px;">
            <n-text depth="2" style="font-size: 12px; font-weight: bold; margin-bottom: 8px; display: block;">执行日志:</n-text>
            <n-timeline size="small">
              <n-timeline-item
                v-for="(log, index) in selectedNodeExecution.logs"
                :key="index"
                :type="getLogType(log.type)"
                :time="log.timestamp"
              >
                <div 
                  style="padding: 4px 8px; background: #fafafa; border-radius: 4px; border-left: 3px solid #ccc;"
                  :style="{
                    'border-left-color': getLogBorderColor(log.type),
                    'background': getLogBackgroundColor(log.type)
                  }"
                >
                  <n-tag :type="getLogType(log.type)" size="tiny" style="margin-right: 8px;">
                    {{ getLogTypeLabel(log.type) }}
                  </n-tag>
                  <n-text 
                    depth="3" 
                    style="font-size: 12px;"
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
  border-radius: 6px;
  background: white;
  border: 2px solid #e0e0e0;
  min-width: 100px;
  max-width: 160px;
  text-align: center;
  position: relative;
  transition: all 0.3s;
  box-shadow: 0 2px 6px rgba(0,0,0,0.08);
}

.wf-node.executed {
  border-color: #18a058;
}

.wf-node.executed.success {
  border-color: #52c41a;
  background: #f6ffed;
}

.wf-node.executed.failed {
  border-color: #ff4d4f;
  background: #fff2f0;
}

.wf-node.executed.running {
  border-color: #1890ff;
  background: #e6f7ff;
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
  box-shadow: 0 0 0 2px rgba(32, 128, 240, 0.3);
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
  background: linear-gradient(135deg, #8b9dc3 0%, #a8c0d1 100%);
  color: white;
  border: none;
}

.wf-node.start.executed {
  background: linear-gradient(135deg, #8b9dc3 0%, #a8c0d1 100%);
  border: 2px solid #52c41a;
}

.wf-node.start.executed.failed {
  background: linear-gradient(135deg, #8b9dc3 0%, #a8c0d1 100%);
  border: 2px solid #ff4d4f;
}

.wf-node.end {
  background: linear-gradient(135deg, #d4a5a5 0%, #e8c4c4 100%);
  color: white;
  border: none;
}

.wf-node.end.executed {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  border: 2px solid #18a058;
}

.wf-node.end.executed.failed {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  border: 2px solid #d03050;
}

.wf-node.task {
  background: linear-gradient(135deg, #a8d8ea 0%, #c5e3f0 100%);
  color: #333;
  border: none;
}

.wf-node.task.executed {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  border: 2px solid #18a058;
}

.wf-node.task.executed.failed {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  border: 2px solid #d03050;
}

.wf-node.condition {
  background: linear-gradient(135deg, #f5d0c5 0%, #f8e1d8 100%);
  color: #333;
  border: none;
}

.wf-node.condition.executed {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
  border: 2px solid #18a058;
}

.wf-node.condition.executed.failed {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
  border: 2px solid #d03050;
}

.wf-node.wait {
  background: linear-gradient(135deg, #e8f5e9 0%, #f1f8f2 100%);
  color: #333;
  border: none;
}

.wf-node.wait.executed {
  background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
  border: 2px solid #18a058;
}

.wf-node.wait.executed.failed {
  background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
  border: 2px solid #d03050;
}

.wf-node.and {
  background: linear-gradient(135deg, #e1d5e7 0%, #f0e6f5 100%);
  color: #333;
  border: none;
}

.wf-node.and.executed {
  background: linear-gradient(135deg, #d299c2 0%, #fef9d7 100%);
  border: 2px solid #18a058;
}

.wf-node.and.executed.failed {
  background: linear-gradient(135deg, #d299c2 0%, #fef9d7 100%);
  border: 2px solid #d03050;
}

.wf-node.or {
  background: linear-gradient(135deg, #d4e5f7 0%, #e8f0fa 100%);
  color: #333;
  border: none;
}

.wf-node.or.executed {
  background: linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%);
  border: 2px solid #18a058;
}

.wf-node.or.executed.failed {
  background: linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%);
  border: 2px solid #d03050;
}

.wf-node.notification {
  background: linear-gradient(135deg, #f5e6d3 0%, #faf3e8 100%);
  color: #333;
  border: none;
}

.wf-node.notification.executed {
  background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
  border: 2px solid #18a058;
}

.wf-node.notification.executed.failed {
  background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
  border: 2px solid #d03050;
}
</style>
