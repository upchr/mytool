<template>
  <div class="workflow-editor">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <n-space>
        <n-button @click="handleSave" type="primary" :loading="saving">保存</n-button>
        <n-button @click="handleTrigger" v-if="workflowId">执行</n-button>
        <n-divider vertical />
        <n-button-group>
          <n-button @click="zoomIn">+</n-button>
          <n-button @click="zoomOut">-</n-button>
          <n-button @click="fitView">适应</n-button>
        </n-button-group>
        <n-tag type="info">拖拽左侧节点到画布</n-tag>
      </n-space>
    </div>

    <div class="editor-container">
      <!-- 左侧节点面板 -->
      <div class="node-panel">
        <n-card title="节点类型" size="small">
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
        </n-card>
      </div>

      <!-- 中间画布 -->
      <div class="canvas-area" ref="vueFlowWrapper">
        <VueFlow
          v-model:nodes="nodes"
          v-model:edges="edges"
          :min-zoom="0.2"
          :max-zoom="4"
          fit-view-on-init
          @node-click="onNodeClick"
          @connect="onConnect"
          @dragover.prevent
          @drop="onDrop"
        >
          <Background />
          <Controls />
          <MiniMap />

          <template #node-task="props">
            <div class="wf-node node-task" :class="{ selected: selectedNode === props.id }">
              <Handle type="target" :position="Position.Left" />
              <div class="node-content">
                <span class="icon">⚙️</span>
                <span>{{ props.data.label }}</span>
              </div>
              <Handle type="source" :position="Position.Right" />
            </div>
          </template>

          <template #node-condition="props">
            <div class="wf-node node-condition" :class="{ selected: selectedNode === props.id }">
              <Handle type="target" :position="Position.Left" />
              <div class="node-content">
                <span class="icon">🔷</span>
                <span>{{ props.data.label }}</span>
              </div>
              <Handle type="source" :position="Position.Right" />
            </div>
          </template>

          <template #node-wait="props">
            <div class="wf-node node-wait" :class="{ selected: selectedNode === props.id }">
              <Handle type="target" :position="Position.Left" />
              <div class="node-content">
                <span class="icon">⏱️</span>
                <span>{{ props.data.label }}</span>
              </div>
              <Handle type="source" :position="Position.Right" />
            </div>
          </template>

          <template #node-notification="props">
            <div class="wf-node node-notification" :class="{ selected: selectedNode === props.id }">
              <Handle type="target" :position="Position.Left" />
              <div class="node-content">
                <span class="icon">📢</span>
                <span>{{ props.data.label }}</span>
              </div>
              <Handle type="source" :position="Position.Right" />
            </div>
          </template>
        </VueFlow>
      </div>

      <!-- 右侧属性面板 -->
      <div class="property-panel">
        <n-card title="节点属性" size="small" v-if="selectedNode">
          <n-form label-placement="top" size="small">
            <n-form-item label="名称">
              <n-input v-model:value="selectedNodeData.label" />
            </n-form-item>
          </n-form>
          <n-space>
            <n-button size="small" type="error" @click="deleteSelectedNode">删除节点</n-button>
          </n-space>
        </n-card>
        <n-card v-else title="节点属性" size="small">
          <n-empty description="点击节点编辑" />
        </n-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { VueFlow, useVueFlow, Position, Handle } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'

const props = defineProps({
  workflowId: { type: String, default: '' },
  initialData: { type: Object, default: () => ({ nodes: [], edges: [] }) }
})

const emit = defineEmits(['save', 'trigger'])

const { zoomIn, zoomOut, fitView, addNodes, addEdges, removeNodes, updateNode } = useVueFlow()

const vueFlowWrapper = ref(null)
const saving = ref(false)
const selectedNode = ref(null)

const nodes = ref([])
const edges = ref([])

const nodeTypes = [
  { type: 'task', label: '任务', icon: '⚙️', desc: '执行定时任务' },
  { type: 'condition', label: '条件', icon: '🔷', desc: '条件判断' },
  { type: 'wait', label: '等待', icon: '⏱️', desc: '等待时间' },
  { type: 'notification', label: '通知', icon: '📢', desc: '发送通知' }
]

const selectedNodeData = computed(() => {
  if (!selectedNode.value) return { label: '' }
  const node = nodes.value.find(n => n.id === selectedNode.value)
  return node?.data || { label: '' }
})

let nodeIdCounter = 1
let draggedType = null

onMounted(() => {
  if (props.initialData?.nodes?.length > 0) {
    nodes.value = props.initialData.nodes.map(n => ({
      id: n.id,
      type: n.type,
      position: n.position || { x: 100, y: 100 },
      data: { label: n.name || n.id, config: n.config || {} }
    }))
    nodeIdCounter = props.initialData.nodes.length + 1
  }
  if (props.initialData?.edges?.length > 0) {
    edges.value = props.initialData.edges.map((e, i) => ({
      id: `edge-${i}`,
      source: e.source,
      target: e.target,
      animated: true
    }))
  }
})

const onDragStart = (event, nodeType) => {
  draggedType = nodeType
  event.dataTransfer.effectAllowed = 'move'
}

const onDrop = (event) => {
  if (!draggedType) return
  
  const bounds = vueFlowWrapper.value.getBoundingClientRect()
  const position = {
    x: event.clientX - bounds.left - 80,
    y: event.clientY - bounds.top - 30
  }
  
  const newNode = {
    id: `node-${nodeIdCounter++}`,
    type: draggedType.type,
    position,
    data: { label: `${draggedType.label}节点`, config: {} }
  }
  
  addNodes([newNode])
  draggedType = null
}

const onNodeClick = (event) => {
  selectedNode.value = event.node.id
}

const onConnect = (connection) => {
  addEdges([{
    id: `edge-${Date.now()}`,
    source: connection.source,
    target: connection.target,
    animated: true
  }])
}

watch(selectedNodeData, (val) => {
  if (selectedNode.value && val) {
    updateNode(selectedNode.value, (node) => ({ ...node, data: { ...val } }))
  }
}, { deep: true })

const deleteSelectedNode = () => {
  if (selectedNode.value) {
    removeNodes([selectedNode.value])
    selectedNode.value = null
  }
}

const handleSave = async () => {
  saving.value = true
  try {
    emit('save', {
      nodes: nodes.value.map(n => ({
        id: n.id,
        type: n.type,
        name: n.data.label,
        config: n.data.config,
        position: n.position
      })),
      edges: edges.value.map(e => ({
        source: e.source,
        target: e.target
      }))
    })
  } finally {
    saving.value = false
  }
}

const handleTrigger = () => {
  emit('trigger')
}

defineExpose({ 
  getData: () => ({
    nodes: nodes.value,
    edges: edges.value
  })
})
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
  width: 200px;
  background: #fff;
  border-right: 1px solid #e0e0e0;
  padding: 12px;
}

.node-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  margin-bottom: 8px;
  background: #fafafa;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  cursor: grab;
}

.node-item:hover {
  border-color: #18a058;
  background: #f0fff4;
}

.node-icon {
  font-size: 20px;
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
  width: 250px;
  background: #fff;
  border-left: 1px solid #e0e0e0;
  padding: 12px;
}

/* 节点样式 */
.wf-node {
  padding: 12px 20px;
  border-radius: 8px;
  border: 2px solid #e0e0e0;
  background: #fff;
  min-width: 120px;
}

.wf-node.selected {
  border-color: #18a058;
  box-shadow: 0 0 0 2px rgba(24, 160, 88, 0.2);
}

.wf-node.node-task { border-color: #2080f0; }
.wf-node.node-condition { border-color: #f0a020; }
.wf-node.node-wait { border-color: #8a8a8a; }
.wf-node.node-notification { border-color: #722ed1; }

.node-content {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.node-content .icon {
  font-size: 16px;
}
</style>

<style>
/* Vue Flow 全局样式（非 scoped） */
.vue-flow {
  background: #fafafa;
}

.vue-flow__edge-path {
  stroke: #999;
  stroke-width: 2;
}

.vue-flow__edge.animated .vue-flow__edge-path {
  stroke: #18a058;
}

.vue-flow__handle {
  width: 10px !important;
  height: 10px !important;
  background: #18a058 !important;
  border: 2px solid #fff !important;
}
</style>
