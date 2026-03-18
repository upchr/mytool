<template>
  <div class="workflow-editor">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <n-space>
        <n-button @click="handleSave" type="primary" :loading="saving">
          <template #icon><n-icon><SaveOutline /></n-icon></template>
          保存工作流
        </n-button>
        <n-button @click="handleTrigger" v-if="workflowId">
          <template #icon><n-icon><PlayOutline /></n-icon></template>
          执行
        </n-button>
        <n-divider vertical />
        <n-button-group>
          <n-button @click="zoomIn"><n-icon><AddOutline /></n-icon></n-button>
          <n-button @click="zoomOut"><n-icon><RemoveOutline /></n-icon></n-button>
          <n-button @click="fitView"><n-icon><ExpandOutline /></n-icon></n-button>
        </n-button-group>
        <n-divider vertical />
        <n-tag type="info">拖拽左侧节点到画布</n-tag>
      </n-space>
    </div>

    <div class="editor-container">
      <!-- 左侧节点面板 -->
      <div class="node-panel">
        <n-card title="节点类型" size="small">
          <n-space vertical>
            <div
              v-for="nodeType in nodeTypes"
              :key="nodeType.type"
              class="node-item"
              draggable="true"
              @dragstart="onDragStart($event, nodeType)"
            >
              <span class="node-icon">{{ nodeType.icon }}</span>
              <div class="node-info">
                <span class="node-name">{{ nodeType.label }}</span>
                <span class="node-desc">{{ nodeType.desc }}</span>
              </div>
            </div>
          </n-space>
        </n-card>
        
        <n-card title="操作提示" size="small" style="margin-top: 12px">
          <n-text depth="3" style="font-size: 12px">
            • 拖拽节点到画布添加<br>
            • 点击节点编辑配置<br>
            • 拖拽端口连线<br>
            • 按 Delete 删除选中
          </n-text>
        </n-card>
      </div>

      <!-- 中间画布 -->
      <div class="canvas-area" ref="vueFlowWrapper">
        <VueFlow
          v-model:nodes="nodes"
          v-model:edges="edges"
          :default-viewport="{ zoom: 1, x: 0, y: 0 }"
          :min-zoom="0.2"
          :max-zoom="4"
          fit-view-on-init
          @node-click="onNodeClick"
          @edge-click="onEdgeClick"
          @nodes-change="onNodesChange"
          @connect="onConnect"
          @dragover="onDragOver"
          @drop="onDrop"
        >
          <Background :gap="20" pattern-color="#e0e0e0" />
          <Controls />
          <MiniMap />

          <!-- 自定义节点 -->
          <template #node-task="nodeProps">
            <WorkflowNode v-bind="nodeProps" type="task" @edit="editNode(nodeProps.id)" @delete="deleteNode(nodeProps.id)" />
          </template>
          <template #node-condition="nodeProps">
            <WorkflowNode v-bind="nodeProps" type="condition" @edit="editNode(nodeProps.id)" @delete="deleteNode(nodeProps.id)" />
          </template>
          <template #node-wait="nodeProps">
            <WorkflowNode v-bind="nodeProps" type="wait" @edit="editNode(nodeProps.id)" @delete="deleteNode(nodeProps.id)" />
          </template>
          <template #node-notification="nodeProps">
            <WorkflowNode v-bind="nodeProps" type="notification" @edit="editNode(nodeProps.id)" @delete="deleteNode(nodeProps.id)" />
          </template>
        </VueFlow>
      </div>

      <!-- 右侧属性面板 -->
      <div class="property-panel">
        <n-card title="属性配置" size="small" v-if="selectedNode">
          <template #header-extra>
            <n-button size="tiny" quaternary @click="selectedNode = null">×</n-button>
          </template>
          
          <n-form label-placement="top" size="small">
            <n-form-item label="节点名称">
              <n-input v-model:value="selectedNodeData.label" placeholder="节点名称" />
            </n-form-item>
            
            <!-- Task 节点配置 -->
            <template v-if="selectedNodeType === 'task'">
              <n-form-item label="任务ID">
                <n-input-number v-model:value="selectedNodeData.config.job_id" :min="1" style="width: 100%" />
                <n-text depth="3" style="font-size: 11px">要执行的定时任务ID</n-text>
              </n-form-item>
              <n-form-item label="超时时间(秒)">
                <n-input-number v-model:value="selectedNodeData.config.max_wait_seconds" :min="10" :max="3600" style="width: 100%" />
              </n-form-item>
            </template>
            
            <!-- Condition 节点配置 -->
            <template v-if="selectedNodeType === 'condition'">
              <n-form-item label="条件表达式">
                <n-input v-model:value="selectedNodeData.config.expression" type="textarea" :autosize="{ minRows: 2 }" placeholder="{{outputs.node1.status}} == 'success'" />
                <n-text depth="3" style="font-size: 11px">支持变量: {{outputs.节点ID.字段}}</n-text>
              </n-form-item>
            </template>
            
            <!-- Wait 节点配置 -->
            <template v-if="selectedNodeType === 'wait'">
              <n-form-item label="等待时间(秒)">
                <n-input-number v-model:value="selectedNodeData.config.seconds" :min="1" :max="3600" style="width: 100%" />
              </n-form-item>
            </template>
            
            <!-- Notification 节点配置 -->
            <template v-if="selectedNodeType === 'notification'">
              <n-form-item label="通知标题">
                <n-input v-model:value="selectedNodeData.config.title" placeholder="标题" />
              </n-form-item>
              <n-form-item label="通知内容">
                <n-input v-model:value="selectedNodeData.config.content" type="textarea" :autosize="{ minRows: 2 }" placeholder="内容，支持 {{outputs.xxx}} 变量" />
              </n-form-item>
            </template>
          </n-form>
        </n-card>
        
        <n-card v-else title="属性配置" size="small">
          <n-empty description="点击节点查看属性" />
        </n-card>
      </div>
    </div>

    <!-- 触发确认 -->
    <n-modal v-model:show="showTriggerModal" preset="card" title="执行工作流" style="width: 400px">
      <p>确定要执行工作流吗？</p>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showTriggerModal = false">取消</n-button>
          <n-button type="primary" @click="doTrigger" :loading="triggering">执行</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import { SaveOutline, PlayOutline, AddOutline, RemoveOutline, ExpandOutline } from '@vicons/ionicons5'
import WorkflowNode from './WorkflowNode.vue'

const props = defineProps({
  workflowId: { type: String, default: '' },
  initialData: { type: Object, default: () => ({ nodes: [], edges: [] }) }
})

const emit = defineEmits(['save', 'trigger'])

const { zoomIn, zoomOut, fitView, addNodes, addEdges, removeNodes, removeEdges, findNode, updateNode } = useVueFlow()

const vueFlowWrapper = ref(null)
const saving = ref(false)
const triggering = ref(false)
const showTriggerModal = ref(false)
const selectedNode = ref(null)

const nodes = ref([])
const edges = ref([])

const nodeTypes = [
  { type: 'task', label: '任务', icon: '⚙️', desc: '执行定时任务' },
  { type: 'condition', label: '条件', icon: '🔷', desc: '条件判断分支' },
  { type: 'wait', label: '等待', icon: '⏱️', desc: '等待指定时间' },
  { type: 'notification', label: '通知', icon: '📢', desc: '发送通知消息' }
]

const selectedNodeData = computed(() => {
  if (!selectedNode.value) return { config: {} }
  const node = findNode(selectedNode.value)
  return node?.data || { config: {} }
})

const selectedNodeType = computed(() => {
  if (!selectedNode.value) return ''
  const node = findNode(selectedNode.value)
  return node?.type || ''
})

let nodeIdCounter = 1
let draggedType = null

onMounted(() => {
  if (props.initialData?.nodes?.length > 0) {
    nodes.value = props.initialData.nodes.map(n => ({
      id: n.id,
      type: n.type,
      position: n.position || { x: 100, y: 100 },
      data: { label: n.name || n.id, config: n.config || getDefaultConfig(n.type) }
    }))
    nodeIdCounter = Math.max(...props.initialData.nodes.map(n => parseInt(n.id.replace('node-', '')) || 0)) + 1
  }
  
  if (props.initialData?.edges?.length > 0) {
    edges.value = props.initialData.edges.map(e => ({
      id: `edge-${e.source}-${e.target}`,
      source: e.source,
      target: e.target,
      animated: true,
      label: e.condition || ''
    }))
  }
})

const getDefaultConfig = (type) => {
  switch (type) {
    case 'task': return { job_id: null, max_wait_seconds: 300 }
    case 'condition': return { expression: 'True' }
    case 'wait': return { seconds: 5 }
    case 'notification': return { title: '通知', content: '' }
    default: return {}
  }
}

// 拖拽
const onDragStart = (event, nodeType) => {
  draggedType = nodeType
  event.dataTransfer.effectAllowed = 'move'
}

const onDragOver = (event) => {
  event.preventDefault()
  event.dataTransfer.dropEffect = 'move'
}

const onDrop = (event) => {
  if (!draggedType) return
  
  const bounds = vueFlowWrapper.value.getBoundingClientRect()
  const position = {
    x: event.clientX - bounds.left - 100,
    y: event.clientY - bounds.top - 40
  }
  
  const newNode = {
    id: `node-${nodeIdCounter++}`,
    type: draggedType.type,
    position,
    data: { 
      label: `${draggedType.label}节点`, 
      config: getDefaultConfig(draggedType.type) 
    }
  }
  
  addNodes([newNode])
  draggedType = null
}

// 节点操作
const onNodeClick = (event) => {
  selectedNode.value = event.node.id
}

const editNode = (nodeId) => {
  selectedNode.value = nodeId
}

const deleteNode = (nodeId) => {
  removeNodes([nodeId])
  if (selectedNode.value === nodeId) selectedNode.value = null
}

const onEdgeClick = (event) => {
  if (confirm('删除这条连线？')) {
    removeEdges([event.edge.id])
  }
}

// 连线
const onConnect = (connection) => {
  addEdges([{
    id: `edge-${connection.source}-${connection.target}`,
    source: connection.source,
    target: connection.target,
    animated: true
  }])
}

// 更新节点数据
watch([selectedNodeData], () => {
  if (selectedNode.value && selectedNodeData.value) {
    updateNode(selectedNode.value, (node) => ({
      ...node,
      data: { ...selectedNodeData.value }
    }))
  }
}, { deep: true })

// 保存
const handleSave = async () => {
  saving.value = true
  try {
    const workflowData = {
      nodes: nodes.value.map(n => ({
        id: n.id,
        type: n.type,
        name: n.data.label,
        config: n.data.config,
        position: n.position
      })),
      edges: edges.value.map(e => ({
        source: e.source,
        target: e.target,
        condition: e.label || 'success'
      }))
    }
    emit('save', workflowData)
  } finally {
    saving.value = false
  }
}

// 执行
const handleTrigger = () => {
  showTriggerModal.value = true
}

const doTrigger = async () => {
  triggering.value = true
  try {
    emit('trigger')
    showTriggerModal.value = false
  } finally {
    triggering.value = false
  }
}

// 导出数据
const getData = () => ({
  nodes: nodes.value.map(n => ({
    id: n.id,
    type: n.type,
    name: n.data.label,
    config: n.data.config,
    position: n.position
  })),
  edges: edges.value.map(e => ({
    source: e.source,
    target: e.target,
    condition: e.label || 'success'
  }))
})

defineExpose({ getData })
</script>

<style scoped>
.workflow-editor {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.toolbar {
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
}

.editor-container {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.node-panel {
  width: 220px;
  background: #fff;
  border-right: 1px solid #e0e0e0;
  padding: 12px;
  overflow-y: auto;
}

.node-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: #fafafa;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  cursor: grab;
  transition: all 0.2s;
}

.node-item:hover {
  border-color: #18a058;
  background: #f0fff4;
  transform: translateX(2px);
}

.node-item:active {
  cursor: grabbing;
}

.node-icon {
  font-size: 24px;
}

.node-info {
  display: flex;
  flex-direction: column;
}

.node-name {
  font-weight: 500;
  font-size: 13px;
}

.node-desc {
  font-size: 11px;
  color: #999;
}

.canvas-area {
  flex: 1;
  background: #fff;
}

.property-panel {
  width: 280px;
  background: #fff;
  border-left: 1px solid #e0e0e0;
  padding: 12px;
  overflow-y: auto;
}
</style>

<style>
/* Vue Flow 全局样式 */
.vue-flow {
  background: #fafafa;
}

.vue-flow__node {
  border-radius: 8px;
}
</style>
