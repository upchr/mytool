<template>
  <div class="workflow-editor">
    <div class="toolbar">
      <n-space>
        <n-button type="primary" @click="handleSave" :loading="saving">
          <template #icon>
            <ion-icon :icon="saveOutline" />
          </template>
          保存
        </n-button>
        <n-button @click="handleTrigger" v-if="workflowId">
          <template #icon>
            <ion-icon :icon="playOutline" />
          </template>
          触发执行
        </n-button>
        <n-button @click="handleZoomIn">
          <template #icon>
            <ion-icon :icon="addOutline" />
          </template>
          放大
        </n-button>
        <n-button @click="handleZoomOut">
          <template #icon>
            <ion-icon :icon="removeOutline" />
          </template>
          缩小
        </n-button>
        <n-button @click="handleFitView">
          <template #icon>
            <ion-icon :icon="expandOutline" />
          </template>
          适应视图
        </n-button>
      </n-space>
    </div>

    <div class="editor-container">
      <!-- 节点面板 -->
      <div class="node-panel">
        <n-card title="节点" size="small">
          <n-space vertical>
            <div
              v-for="nodeType in nodeTypes"
              :key="nodeType.type"
              class="node-item"
              draggable="true"
              @dragstart="handleDragStart($event, nodeType)"
            >
              <n-icon :component="nodeType.icon" />
              <span>{{ nodeType.label }}</span>
            </div>
          </n-space>
        </n-card>
      </div>

      <!-- 画布区域 -->
      <div class="canvas-area">
        <VueFlow
          v-model:nodes="nodes"
          v-model:edges="edges"
          :default-zoom="1"
          :min-zoom="0.2"
          :max-zoom="4"
          @drop="handleDrop"
          @dragover="handleDragOver"
          @node-click="handleNodeClick"
        >
          <Background pattern-color="#aaa" :gap="16" />
          <Controls />
          <MiniMap />

          <template #node-task="{ data, id }">
            <WorkflowNode
              :data="data"
              :id="id"
              type="task"
              @delete="handleDeleteNode(id)"
              @config="handleConfigNode(id)"
            />
          </template>

          <template #node-condition="{ data, id }">
            <WorkflowNode
              :data="data"
              :id="id"
              type="condition"
              @delete="handleDeleteNode(id)"
              @config="handleConfigNode(id)"
            />
          </template>

          <template #node-wait="{ data, id }">
            <WorkflowNode
              :data="data"
              :id="id"
              type="wait"
              @delete="handleDeleteNode(id)"
              @config="handleConfigNode(id)"
            />
          </template>

          <template #node-notification="{ data, id }">
            <WorkflowNode
              :data="data"
              :id="id"
              type="notification"
              @delete="handleDeleteNode(id)"
              @config="handleConfigNode(id)"
            />
          </template>
        </VueFlow>
      </div>

      <!-- 属性面板 -->
      <div class="property-panel" v-if="selectedNode">
        <n-card title="节点属性" size="small" :bordered="false">
          <n-form :model="selectedNodeData" label-placement="left" label-width="80">
            <n-form-item label="名称">
              <n-input v-model:value="selectedNodeData.name" />
            </n-form-item>

            <template v-if="selectedNodeType === 'task'">
              <n-form-item label="任务ID">
                <n-input-number v-model:value="selectedNodeData.config.job_id" />
              </n-form-item>
              <n-form-item label="超时(秒)">
                <n-input-number v-model:value="selectedNodeData.config.max_wait_seconds" :min="30" />
              </n-form-item>
            </template>

            <template v-if="selectedNodeType === 'condition'">
              <n-form-item label="条件表达式">
                <n-input
                  v-model:value="selectedNodeData.config.expression"
                  type="textarea"
                  placeholder="{{inputs.count}} > 5"
                />
              </n-form-item>
            </template>

            <template v-if="selectedNodeType === 'wait'">
              <n-form-item label="等待(秒)">
                <n-input-number v-model:value="selectedNodeData.config.seconds" :min="1" />
              </n-form-item>
            </template>

            <template v-if="selectedNodeType === 'notification'">
              <n-form-item label="标题">
                <n-input v-model:value="selectedNodeData.config.title" />
              </n-form-item>
              <n-form-item label="内容">
                <n-input
                  v-model:value="selectedNodeData.config.content"
                  type="textarea"
                />
              </n-form-item>
            </template>
          </n-form>
        </n-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import {
  saveOutline,
  playOutline,
  addOutline,
  removeOutline,
  expandOutline,
  constructOutline,
  hourglassOutline,
  notificationsOutline
} from '@vicons/ionicons5'
import { useMessage } from 'naive-ui'
import WorkflowNode from './WorkflowNode.vue'

const props = defineProps({
  workflowId: {
    type: String,
    default: ''
  },
  initialNodes: {
    type: Array,
    default: () => []
  },
  initialEdges: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['save', 'trigger'])

const message = useMessage()
const { zoomIn, zoomOut, fitView, addNodes, addEdges, removeNodes, findNode } = useVueFlow()

const nodes = ref([])
const edges = ref([])
const selectedNode = ref(null)
const saving = ref(false)

const nodeTypes = [
  { type: 'task', label: '任务', icon: constructOutline },
  { type: 'condition', label: '条件', icon: hourglassOutline },
  { type: 'wait', label: '等待', icon: hourglassOutline },
  { type: 'notification', label: '通知', icon: notificationsOutline }
]

const selectedNodeData = computed(() => {
  if (!selectedNode.value) return {}
  const node = findNode(selectedNode.value)
  return node?.data || {}
})

const selectedNodeType = computed(() => {
  if (!selectedNode.value) return ''
  const node = findNode(selectedNode.value)
  return node?.type || ''
})

let draggedNodeType = null

onMounted(() => {
  if (props.initialNodes.length > 0) {
    nodes.value = props.initialNodes.map((n, i) => ({
      id: n.id || `node-${i}`,
      type: n.type || 'task',
      position: n.position || { x: 100 + i * 200, y: 100 },
      data: {
        name: n.name || `节点 ${i + 1}`,
        config: n.config || {}
      }
    }))
  }
  
  if (props.initialEdges.length > 0) {
    edges.value = props.initialEdges.map((e, i) => ({
      id: e.id || `edge-${i}`,
      source: e.source,
      target: e.target,
      animated: true,
      data: { condition: e.condition || 'success' }
    }))
  }
})

const handleDragStart = (event, nodeType) => {
  draggedNodeType = nodeType
  event.dataTransfer.effectAllowed = 'move'
}

const handleDragOver = (event) => {
  event.preventDefault()
  event.dataTransfer.dropEffect = 'move'
}

const handleDrop = (event) => {
  if (!draggedNodeType) return
  
  const position = {
    x: event.clientX - 200,
    y: event.clientY - 100
  }
  
  const newNode = {
    id: `node-${Date.now()}`,
    type: draggedNodeType.type,
    position,
    data: {
      name: `${draggedNodeType.label} 节点`,
      config: getDefaultConfig(draggedNodeType.type)
    }
  }
  
  addNodes([newNode])
  draggedNodeType = null
}

const getDefaultConfig = (type) => {
  switch (type) {
    case 'task':
      return { job_id: null, max_wait_seconds: 300 }
    case 'condition':
      return { expression: '{{inputs.value}} > 0' }
    case 'wait':
      return { seconds: 5 }
    case 'notification':
      return { title: '通知', content: '' }
    default:
      return {}
  }
}

const handleNodeClick = (event) => {
  selectedNode.value = event.node.id
}

const handleDeleteNode = (nodeId) => {
  removeNodes([nodeId])
  if (selectedNode.value === nodeId) {
    selectedNode.value = null
  }
  edges.value = edges.value.filter(e => e.source !== nodeId && e.target !== nodeId)
}

const handleConfigNode = (nodeId) => {
  selectedNode.value = nodeId
}

const handleZoomIn = () => zoomIn()
const handleZoomOut = () => zoomOut()
const handleFitView = () => fitView()

const handleSave = async () => {
  saving.value = true
  try {
    const workflowNodes = nodes.value.map(n => ({
      id: n.id,
      type: n.type,
      name: n.data.name,
      config: n.data.config,
      position: n.position
    }))
    
    const workflowEdges = edges.value.map(e => ({
      id: e.id,
      source: e.source,
      target: e.target,
      condition: e.data?.condition || 'success'
    }))
    
    emit('save', {
      nodes: workflowNodes,
      edges: workflowEdges
    })
    
    message.success('保存成功')
  } catch (e) {
    message.error('保存失败: ' + e.message)
  } finally {
    saving.value = false
  }
}

const handleTrigger = () => {
  emit('trigger')
}
</script>

<style scoped>
.workflow-editor {
  height: 100%;
  display: flex;
  flex-direction: column;
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
  width: 200px;
  background: #f5f5f5;
  border-right: 1px solid #e0e0e0;
  padding: 12px;
  overflow-y: auto;
}

.node-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #fff;
  border-radius: 6px;
  cursor: grab;
  border: 1px solid #e0e0e0;
  transition: all 0.2s;
}

.node-item:hover {
  border-color: #18a058;
  background: #f0fff4;
}

.node-item:active {
  cursor: grabbing;
}

.canvas-area {
  flex: 1;
  position: relative;
}

.property-panel {
  width: 280px;
  background: #fff;
  border-left: 1px solid #e0e0e0;
  padding: 12px;
  overflow-y: auto;
}
</style>