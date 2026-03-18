<template>
  <div class="workflow-editor">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <n-space>
        <n-button @click="goBack">← 返回列表</n-button>
        <n-button type="primary" @click="handleSave" :loading="saving">保存</n-button>
        <n-button @click="handleTrigger" v-if="workflowId">执行</n-button>
        <n-divider vertical />
        <n-button @click="zoomIn">放大</n-button>
        <n-button @click="zoomOut">缩小</n-button>
        <n-button @click="fitView">适应</n-button>
      </n-space>
    </div>

    <div class="editor-body">
      <!-- 左侧节点面板 -->
      <div class="left-panel">
        <n-card title="节点类型" size="small">
          <div class="node-list">
            <div
              v-for="item in nodeTypes"
              :key="item.type"
              class="draggable-node"
              draggable="true"
              @dragstart="onDragStart($event, item)"
            >
              <span class="icon">{{ item.icon }}</span>
              <div class="info">
                <div class="name">{{ item.label }}</div>
                <div class="desc">{{ item.desc }}</div>
              </div>
            </div>
          </div>
        </n-card>
        <n-card size="small" style="margin-top: 8px">
          <n-text depth="3" style="font-size: 12px">
            操作：拖拽节点到画布 → 点击选中 → 右侧编辑属性 → 拖拽端口连线
          </n-text>
        </n-card>
      </div>

      <!-- 画布 -->
      <div class="canvas" ref="canvasRef">
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

          <template #node-task="props">
            <div class="wf-node task" :class="{ active: selectedId === props.id }">
              <Handle type="target" :position="Position.Left" />
              <div class="content">⚙️ {{ props.data.label }}</div>
              <Handle type="source" :position="Position.Right" />
            </div>
          </template>

          <template #node-condition="props">
            <div class="wf-node condition" :class="{ active: selectedId === props.id }">
              <Handle type="target" :position="Position.Left" />
              <div class="content">🔷 {{ props.data.label }}</div>
              <Handle type="source" :position="Position.Right" />
            </div>
          </template>

          <template #node-wait="props">
            <div class="wf-node wait" :class="{ active: selectedId === props.id }">
              <Handle type="target" :position="Position.Left" />
              <div class="content">⏱️ {{ props.data.label }}</div>
              <Handle type="source" :position="Position.Right" />
            </div>
          </template>

          <template #node-notification="props">
            <div class="wf-node notification" :class="{ active: selectedId === props.id }">
              <Handle type="target" :position="Position.Left" />
              <div class="content">📢 {{ props.data.label }}</div>
              <Handle type="source" :position="Position.Right" />
            </div>
          </template>
        </VueFlow>
      </div>

      <!-- 右侧属性面板 -->
      <div class="right-panel">
        <n-card title="节点属性" size="small" v-if="selectedNode">
          <n-form label-placement="top" size="small">
            <n-form-item label="名称">
              <n-input v-model:value="editLabel" @blur="applyEdit" />
            </n-form-item>
            <n-form-item label="类型">
              <n-tag>{{ selectedNode.type }}</n-tag>
            </n-form-item>
            
            <!-- 任务节点配置 -->
            <template v-if="selectedNode.type === 'task'">
              <n-form-item label="选择任务">
                <n-select
                  v-model:value="editConfig.job_id"
                  :options="jobOptions"
                  placeholder="请选择要执行的任务"
                  @update:value="applyEdit"
                />
              </n-form-item>
              <n-text depth="3" style="font-size: 11px">
                从「任务管理」中已创建的任务里选择
              </n-text>
            </template>
            
            <!-- 条件节点配置 -->
            <template v-if="selectedNode.type === 'condition'">
              <n-form-item label="条件表达式">
                <n-input v-model:value="editConfig.expression" placeholder="True" @blur="applyEdit" />
              </n-form-item>
              <n-text depth="3" style="font-size: 11px">
                示例：outputs.node1.status == 'success'
              </n-text>
            </template>
            
            <!-- 等待节点配置 -->
            <template v-if="selectedNode.type === 'wait'">
              <n-form-item label="等待秒数">
                <n-input-number v-model:value="editConfig.seconds" style="width: 100%" @blur="applyEdit" />
              </n-form-item>
            </template>
            
            <!-- 通知节点配置 -->
            <template v-if="selectedNode.type === 'notification'">
              <n-form-item label="标题">
                <n-input v-model:value="editConfig.title" @blur="applyEdit" />
              </n-form-item>
              <n-form-item label="内容">
                <n-input v-model:value="editConfig.content" type="textarea" @blur="applyEdit" />
              </n-form-item>
            </template>
          </n-form>
          <n-button type="error" size="small" block @click="deleteNode">删除此节点</n-button>
        </n-card>
        <n-card v-else title="节点属性" size="small">
          <n-empty description="点击节点编辑属性" />
        </n-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { VueFlow, useVueFlow, Position, Handle } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'

const props = defineProps({
  workflowId: String,
  initialData: { type: Object, default: () => ({ nodes: [], edges: [] }) }
})

const emit = defineEmits(['save', 'trigger', 'back'])

const { zoomIn, zoomOut, fitView, addNodes, addEdges, removeNodes } = useVueFlow()

const canvasRef = ref(null)
const saving = ref(false)
const nodes = ref([])
const edges = ref([])
const selectedId = ref(null)
const editLabel = ref('')
const editConfig = ref({})
const nodeCounter = ref(1)

const nodeTypes = [
  { type: 'task', label: '任务', icon: '⚙️', desc: '执行定时任务' },
  { type: 'condition', label: '条件', icon: '🔷', desc: '条件判断' },
  { type: 'wait', label: '等待', icon: '⏱️', desc: '等待时间' },
  { type: 'notification', label: '通知', icon: '📢', desc: '发送消息' }
]

const selectedNode = ref(null)
const jobOptions = ref([])  // 任务列表选项

// 加载任务列表
const loadJobs = async () => {
  try {
    const res = await window.$request.post('/cron/jobsList', {})
    jobOptions.value = (res?.list || res || []).map(j => ({
      label: `${j.name} (ID: ${j.id})`,
      value: j.id
    }))
  } catch (e) {
    console.error('加载任务列表失败', e)
  }
}

onMounted(() => {
  loadJobs()  // 加载任务列表
  
  if (props.initialData?.nodes?.length > 0) {
    nodes.value = props.initialData.nodes.map(n => ({
      id: n.id,
      type: n.type,
      position: n.position || { x: 100, y: 100 },
      data: { label: n.name || '节点', config: n.config || {} }
    }))
    nodeCounter.value = props.initialData.nodes.length + 1
  }
  if (props.initialData?.edges?.length > 0) {
    edges.value = props.initialData.edges.map((e, i) => ({
      id: `e${i}`,
      source: e.source,
      target: e.target,
      animated: true
    }))
  }
})

// 加载任务列表
const loadJobs = async () => {
  try {
    const res = await window.$request.post('/cron/jobsList', {})
    jobOptions.value = (res?.list || res || []).map(j => ({
      label: `${j.name} (ID: ${j.id})`,
      value: j.id
    }))
  } catch (e) {
    console.error('加载任务列表失败', e)
  }
}

onMounted(() => {
  loadJobs()
  
  if (props.initialData?.nodes?.length > 0) {
    nodes.value = props.initialData.nodes.map(n => ({
      id: n.id,
      type: n.type,
      position: n.position || { x: 100, y: 100 },
      data: { label: n.name || '节点', config: n.config || {} }
    }))
    nodeCounter.value = props.initialData.nodes.length + 1
  }
  if (props.initialData?.edges?.length > 0) {
    edges.value = props.initialData.edges.map((e, i) => ({
      id: `e${i}`,
      source: e.source,
      target: e.target,
      animated: true
    }))
  }
})

// 拖拽
let dragType = null
const onDragStart = (e, item) => {
  dragType = item
  e.dataTransfer.effectAllowed = 'move'
}

const onDrop = (e) => {
  if (!dragType) return
  const rect = canvasRef.value.getBoundingClientRect()
  const pos = { x: e.clientX - rect.left - 60, y: e.clientY - rect.top - 20 }
  const id = `n${nodeCounter++}`
  nodes.value.push({
    id,
    type: dragType.type,
    position: pos,
    data: { label: `${dragType.label}节点`, config: {} }
  })
  dragType = null
}

// 点击节点
const onNodeClick = (e) => {
  selectedId.value = e.node.id
  selectedNode.value = e.node
  editLabel.value = e.node.data.label
  editConfig.value = { ...e.node.data.config }
}

// 连线
const onConnect = (conn) => {
  edges.value.push({
    id: `e${Date.now()}`,
    source: conn.source,
    target: conn.target,
    animated: true
  })
}

// 应用编辑（失焦时）
const applyEdit = () => {
  if (!selectedId.value) return
  const idx = nodes.value.findIndex(n => n.id === selectedId.value)
  if (idx >= 0) {
    nodes.value[idx].data.label = editLabel.value
    nodes.value[idx].data.config = { ...editConfig.value }
  }
}

// 删除节点
const deleteNode = () => {
  if (!selectedId.value) return
  const idx = nodes.value.findIndex(n => n.id === selectedId.value)
  if (idx >= 0) {
    nodes.value.splice(idx, 1)
    edges.value = edges.value.filter(e => e.source !== selectedId.value && e.target !== selectedId.value)
  }
  selectedId.value = null
  selectedNode.value = null
}

// 保存
const handleSave = () => {
  saving.value = true
  emit('save', {
    nodes: nodes.value.map(n => ({
      id: n.id,
      type: n.type,
      name: n.data.label,
      config: n.data.config,
      position: n.position
    })),
    edges: edges.value.map(e => ({ source: e.source, target: e.target }))
  })
  saving.value = false
}

const handleTrigger = () => emit('trigger')
const goBack = () => emit('back')

defineExpose({ getData: () => ({ nodes: nodes.value, edges: edges.value }) })
</script>

<style scoped>
.workflow-editor {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f0f2f5;
}

.toolbar {
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #d9d9d9;
}

.editor-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.left-panel {
  width: 200px;
  padding: 12px;
  background: #fff;
  border-right: 1px solid #d9d9d9;
  overflow-y: auto;
}

.node-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.draggable-node {
  display: flex;
  gap: 10px;
  padding: 10px;
  background: #fafafa;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  cursor: grab;
}

.draggable-node:hover {
  border-color: #18a058;
  background: #f6ffed;
}

.draggable-node .icon {
  font-size: 20px;
}

.draggable-node .name {
  font-weight: 500;
  font-size: 13px;
}

.draggable-node .desc {
  font-size: 11px;
  color: #999;
}

.canvas {
  flex: 1;
  background: #fff;
}

.right-panel {
  width: 260px;
  padding: 12px;
  background: #fff;
  border-left: 1px solid #d9d9d9;
  overflow-y: auto;
}

/* 节点样式 */
.wf-node {
  padding: 10px 16px;
  border-radius: 6px;
  border: 2px solid #d9d9d9;
  background: #fff;
  font-size: 13px;
}

.wf-node.active {
  border-color: #18a058;
  box-shadow: 0 0 0 2px rgba(24, 160, 88, 0.2);
}

.wf-node.task { border-color: #1890ff; }
.wf-node.condition { border-color: #fa8c16; }
.wf-node.wait { border-color: #8c8c8c; }
.wf-node.notification { border-color: #722ed1; }
</style>

<style>
/* 全局样式 */
.vue-flow { background: #fafafa; }
.vue-flow__handle { width: 10px !important; height: 10px !important; background: #18a058 !important; border: 2px solid #fff !important; }
.vue-flow__edge-path { stroke: #999; stroke-width: 2; }
</style>
