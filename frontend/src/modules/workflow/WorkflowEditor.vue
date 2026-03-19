<template>
  <div class="workflow-editor">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <n-space align="center">
        <n-button @click="goBack">← 返回列表</n-button>
        <n-divider vertical />
        <n-input
          v-model:value="currentWorkflowName"
          placeholder="工作流名称"
          style="width: 200px"
          @update:value="onWorkflowNameChange"
        />
        <n-divider vertical />
        <n-button @click="handleUndo" :disabled="!canUndo">↩ 撤销</n-button>
        <n-button @click="handleRedo" :disabled="!canRedo">↪ 重做</n-button>
        <n-divider vertical />
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
          @edge-click="onEdgeClick"
          @connect="onConnect"
          @dragover.prevent
          @drop="onDrop"
        >
          <Background />
          <Controls />

          <template #node-start="props">
            <div class="wf-node start" :class="{ active: selectedId === props.id }">
              <div class="content">🚀 {{ props.data.label }}</div>
              <Handle type="source" :position="Position.Right" />
            </div>
          </template>

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

          <template #node-and="props">
            <div class="wf-node and" :class="{ active: selectedId === props.id }">
              <Handle type="target" :position="Position.Left" />
              <div class="content">🔗 {{ props.data.label }}</div>
              <Handle type="source" :position="Position.Right" />
            </div>
          </template>

          <template #node-or="props">
            <div class="wf-node or" :class="{ active: selectedId === props.id }">
              <Handle type="target" :position="Position.Left" />
              <div class="content">🔀 {{ props.data.label }}</div>
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

          <template #node-end="props">
            <div class="wf-node end" :class="{ active: selectedId === props.id }">
              <Handle type="target" :position="Position.Left" />
              <div class="content">🏁 {{ props.data.label }}</div>
            </div>
          </template>
        </VueFlow>
      </div>

      <!-- 右侧属性面板 -->
      <div class="right-panel">
        <n-card title="节点属性" size="small" v-if="selectedNode">
          <n-form label-placement="top" size="small">
            <n-form-item>
              <template #label>
                名称<n-tag type="info" size="small" style="margin-left: 8px;">ID：{{ selectedNode.id }}</n-tag>
              </template>
              <n-space align="center" style="width: 100%">
                <n-input v-model:value="editLabel" @blur="applyEdit" style="flex: 1;" />
              </n-space>
            </n-form-item>
            <n-form-item label="类型">
              <n-tag>{{ selectedNode.type }}</n-tag>
            </n-form-item>

            <!-- AND 节点配置 -->
            <template v-if="selectedNode.type === 'and'">
              <n-alert type="info" size="small" style="margin-bottom: 12px">
                <template #header>💡 AND 节点说明</template>
                <div style="font-size: 11px; line-height: 1.6">
                  <div><strong>AND 节点</strong>：等待所有前置节点完成后才执行</div>
                  <div style="margin-top: 4px; color: #666;">
                    • 适用于需要访问所有前置节点输出的场景
                  </div>
                  <div style="margin-top: 4px; color: #666;">
                    • 例如：通知节点需要访问多个前置节点的输出
                  </div>
                </div>
              </n-alert>
            </template>

            <!-- OR 节点配置 -->
            <template v-if="selectedNode.type === 'or'">
              <n-alert type="info" size="small" style="margin-bottom: 12px">
                <template #header>💡 OR 节点说明</template>
                <div style="font-size: 11px; line-height: 1.6">
                  <div><strong>OR 节点</strong>：任一前置节点完成即执行</div>
                  <div style="margin-top: 4px; color: #666;">
                    • 适用于并行执行的场景
                  </div>
                  <div style="margin-top: 4px; color: #666;">
                    • 例如：多个任务完成后发送通知，不需要等待所有任务
                  </div>
                </div>
              </n-alert>
            </template>

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
              <n-alert type="info" size="small" style="margin-bottom: 12px">
                <template #header>💡 条件节点说明</template>
                <div style="font-size: 11px; line-height: 1.6">
                  <div><strong>条件节点</strong>：评估表达式，返回 True 或 False</div>
                  <div style="margin-top: 4px; color: #666;">
                    • 结果存储在 <code style="background: #f0f0f0; padding: 2px 4px; border-radius: 3px;">condition_result</code> 中
                  </div>
                  <div style="margin-top: 4px; color: #666;">
                    • 条件节点本身总是执行成功（status = 'success'）
                  </div>
                </div>
              </n-alert>
              
              <n-form-item label="条件表达式">
                <n-input 
                  v-model:value="editConfig.expression" 
                  placeholder="True" 
                  @blur="applyEdit"
                  type="textarea"
                  :autosize="{ minRows: 3, maxRows: 6 }"
                  style="font-family: 'Courier New', monospace; font-size: 13px;"
                />
              </n-form-item>
              
              <n-form-item label="选择前置节点">
                <n-select 
                  :options="previousNodes"
                  placeholder="选择要引用的节点"
                  @update:value="(val) => { insertNodeVariable(val); applyEdit() }"
                />
              </n-form-item>
              
              <n-form-item label="可用变量">
                <n-collapse size="small">
                  <n-collapse-item v-if="previousNodes.length > 0" title="前置节点变量">
                    <div v-for="node in previousNodes" :key="node.value" style="margin-bottom: 12px">
                      <n-space align="center" style="margin-bottom: 4px">
                        <n-tag type="info" size="small">{{ node.label }}</n-tag>
                        <n-tag :type="getNodeById(node.value)?.type === 'condition' ? 'warning' : 'default'" size="small">
                          {{ getNodeById(node.value)?.type === 'condition' ? '条件节点' : '普通节点' }}
                        </n-tag>
                      </n-space>
                      <div style="font-size: 11px; margin-top: 6px; color: #666; line-height: 1.8;">
                        <div v-if="getNodeById(node.value)?.type === 'condition'" @click="copyVariable(`outputs.${node.value}.condition_result`)" style="cursor: pointer; color: #18a058;">
                          📋 outputs.{{ node.value }}.condition_result <span style="color: #999; font-size: 10px;"> (条件结果：True/False)</span>
                        </div>
                        <div v-else>
                          <div @click="copyVariable(`outputs.${node.value}.status`)" style="cursor: pointer; color: #18a058;">
                            📋 outputs.{{ node.value }}.status <span style="color: #999; font-size: 10px;"> (节点执行状态：success/failed)</span>
                          </div>
                          <div @click="copyVariable(`outputs.${node.value}.output`)" style="cursor: pointer; color: #18a058;">
                            📋 outputs.{{ node.value }}.output <span style="color: #999; font-size: 10px;"> (节点输出内容)</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </n-collapse-item>
                  <n-collapse-item title="工作流输入参数">
                    <div style="font-size: 11px; color: #666; line-height: 1.8;">
                      <div style="margin-bottom: 8px;">
                        <strong>什么是工作流输入参数？</strong>
                      </div>
                      <div style="margin-bottom: 8px;">
                        在触发工作流时传递的数据，例如：{"count": 10, "status": "active"}
                      </div>
                      <div @click="copyVariable('inputs.xxx')" style="cursor: pointer; color: #18a058;">
                        📋 inputs.xxx (输入参数)
                      </div>
                      <div style="margin-top: 8px; padding: 8px; background: #f6ffed; border-radius: 4px; font-size: 10px;">
                        <strong>示例：</strong><br>
                        • inputs.count > 5 (判断输入参数是否大于5)<br>
                        • inputs.status == 'active' (判断输入参数是否等于'active')
                      </div>
                    </div>
                  </n-collapse-item>
                </n-collapse>
              </n-form-item>
              
              <n-form-item label="常用表达式">
                <n-space vertical style="width: 100%">
                  <n-select 
                    :options="dynamicConditionExamples"
                    placeholder="选择示例"
                    @update:value="(val) => { editConfig.expression = val; applyEdit() }"
                  />
                </n-space>
              </n-form-item>
            </template>

            <!-- 等待节点配置 -->
            <template v-if="selectedNode.type === 'wait'">
              <n-form-item label="等待秒数">
                <n-input-number v-model:value="editConfig.seconds" style="width: 100%" @blur="applyEdit" />
              </n-form-item>
            </template>

            <!-- 通知节点配置 -->
            <template v-if="selectedNode.type === 'notification'">
              <n-alert type="info" size="small" style="margin-bottom: 12px">
                <template #header>💡 通知节点说明</template>
                <div style="font-size: 11px; line-height: 1.6">
                  <div><strong>支持占位符：</strong></div>
                  <div style="margin-top: 4px; color: #666;">
                    • <code style="background: #f0f0f0; padding: 2px 4px; border-radius: 3px;">&lbrace;&lbrace;inputs.xxx&rbrace;&rbrace;</code> - 工作流输入参数
                  </div>
                  <div style="margin-top: 4px; color: #666;">
                    • <code style="background: #f0f0f0; padding: 2px 4px; border-radius: 3px;">&lbrace;&lbrace;outputs.node_id.xxx&rbrace;&rbrace;</code> - 前置节点输出
                  </div>
                </div>
              </n-alert>
              
              <n-form-item label="标题">
                <n-input v-model:value="editConfig.title" @blur="applyEdit" placeholder="例如：任务执行成功" />
              </n-form-item>
              <n-form-item label="内容">
                <n-input v-model:value="editConfig.content" type="textarea" @blur="applyEdit" placeholder="例如：用户&lbrace;&lbrace;inputs.name&rbrace;&rbrace;的任务执行完成，状态：&lbrace;&lbrace;outputs.task1.status&rbrace;&rbrace;" />
              </n-form-item>
              
              <n-form-item label="可用变量">
                <n-collapse size="small">
                  <n-collapse-item v-if="previousNodes.length > 0" title="前置节点变量">
                    <div v-for="node in previousNodes" :key="node.value" style="margin-bottom: 12px">
                      <n-space align="center" style="margin-bottom: 4px">
                        <n-tag type="info" size="small">{{ node.label }}</n-tag>
                        <n-tag :type="getNodeById(node.value)?.type === 'condition' ? 'warning' : 'default'" size="small">
                          {{ getNodeById(node.value)?.type === 'condition' ? '条件节点' : '普通节点' }}
                        </n-tag>
                      </n-space>
                      <div style="font-size: 11px; margin-top: 6px; color: #666; line-height: 1.8;">
                        <div v-if="getNodeById(node.value)?.type === 'condition'" @click="copyVariable(`outputs.${node.value}.condition_result`)" style="cursor: pointer; color: #18a058;">
                          📋 outputs.{{ node.value }}.condition_result <span style="color: #999; font-size: 10px;"> (条件结果：True/False)</span>
                        </div>
                        <div v-else>
                          <div @click="copyVariable(`outputs.${node.value}.status`)" style="cursor: pointer; color: #18a058;">
                            📋 outputs.{{ node.value }}.status <span style="color: #999; font-size: 10px;"> (状态：success/failed)</span>
                          </div>
                          <div @click="copyVariable(`outputs.${node.value}.output`)" style="cursor: pointer; color: #18a058;">
                            📋 outputs.{{ node.value }}.output <span style="color: #999; font-size: 10px;"> (输出内容)</span>
                          </div>
                          <div @click="copyVariable(`outputs.${node.value}.error`)" style="cursor: pointer; color: #18a058;">
                            📋 outputs.{{ node.value }}.error <span style="color: #999; font-size: 10px;"> (错误信息)</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </n-collapse-item>
                  <n-collapse-item title="输入参数变量">
                    <div v-for="input in usedInputs" :key="input" style="margin-bottom: 8px">
                      <div @click="copyVariable(`inputs.${input}`)" style="cursor: pointer; color: #18a058; font-size: 11px;">
                        📋 inputs.{{ input }}
                      </div>
                    </div>
                  </n-collapse-item>
                </n-collapse>
              </n-form-item>
            </template>
          </n-form>
          <n-button type="error" size="small" block @click="deleteNode">删除此节点</n-button>
        </n-card>
        
        <!-- 连线属性面板 -->
        <n-card title="连线属性" size="small" v-if="selectedEdge">
          <n-form label-placement="top" size="small">
            <n-form-item label="执行条件">
              <n-select 
                v-model:value="editEdgeCondition"
                :options="currentEdgeConditionOptions"
                @update:value="applyEdgeEdit"
              />
            </n-form-item>
            <n-alert type="info" size="small" style="margin-top: 8px">
              <template #header>💡 连线条件说明</template>
              <div style="font-size: 11px; line-height: 1.6;">
                <div v-if="selectedEdgeSourceNode?.type === 'condition'">
                  <strong>前置是条件节点：</strong><br>
                  • <code style="background: #f0f0f0; padding: 2px 4px; border-radius: 3px;">true</code> - 条件为真时执行<br>
                  • <code style="background: #f0f0f0; padding: 2px 4px; border-radius: 3px;">false</code> - 条件为假时执行
                </div>
                <div v-else>
                  <strong>前置是普通节点：</strong><br>
                  • <code style="background: #f0f0f0; padding: 2px 4px; border-radius: 3px;">always</code> - 总是执行后续节点
                </div>
                <div style="margin-top: 8px; color: #666; font-size: 10px;">
                  💡 提示：条件节点用于分支判断，普通节点通常用"总是执行"
                </div>
              </div>
            </n-alert>
          </n-form>
          <n-button type="error" size="small" block @click="deleteEdge" style="margin-top: 8px">删除此连线</n-button>
        </n-card>
        
        <n-card v-else-if="!selectedNode && !selectedEdge" title="属性面板" size="small">
          <n-empty description="点击节点或连线编辑属性" />
        </n-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { VueFlow, useVueFlow, Position, Handle } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'

const props = defineProps({
  workflowId: String,
  workflowName: String,
  initialData: { type: Object, default: () => ({ nodes: [], edges: [] }) }
})

const emit = defineEmits(['save', 'trigger', 'back', 'update:workflowName'])

const { zoomIn, zoomOut, fitView, addNodes, addEdges, removeNodes } = useVueFlow()

const canvasRef = ref(null)
const saving = ref(false)
const nodes = ref([])
const edges = ref([])
const selectedId = ref(null)
const editLabel = ref('')
const editConfig = ref({})
let nodeCounter = ref(1)

// 工作流名称（内部状态）
const currentWorkflowName = ref(props.workflowName || '新工作流')

// 工作流名称变化
const onWorkflowNameChange = (value) => {
  currentWorkflowName.value = value
  emit('update:workflowName', value)
}

// 撤销/重做历史记录
const history = ref([])
const historyIndex = ref(-1)

// 计算是否可以撤销/重做
const canUndo = computed(() => historyIndex.value > 0)
const canRedo = computed(() => historyIndex.value < history.value.length - 1)

const nodeTypes = [
  { type: 'start', label: '开始', icon: '🚀', desc: '工作流起点' },
  { type: 'task', label: '任务', icon: '⚙️', desc: '执行定时任务' },
  { type: 'condition', label: '条件', icon: '🔷', desc: '条件判断' },
  { type: 'wait', label: '等待', icon: '⏱️', desc: '等待时间' },
  { type: 'notification', label: '通知', icon: '📢', desc: '发送消息' },
  { type: 'and', label: 'AND', icon: '🔗', desc: '等待所有前置节点完成' },
  { type: 'or', label: 'OR', icon: '🔀', desc: '任一前置节点完成即执行' },
  { type: 'end', label: '结束', icon: '🏁', desc: '工作流终点' }
]

const selectedNode = ref(null)
const selectedEdge = ref(null)
const editEdgeCondition = ref('always')
const jobOptions = ref([])  // 任务列表选项

const edgeConditionOptions = [
  { label: '总是执行', value: 'always' },
  { label: '条件为真时执行', value: 'true' },
  { label: '条件为假时执行', value: 'false' },
  { label: '节点成功时执行', value: 'success' },
  { label: '节点失败时执行', value: 'failed' }
]

// 计算前置节点选项
const previousNodes = computed(() => {
  if (!selectedNode.value) return []
  
  const nodeId = selectedNode.value.id
  const prevNodeIds = new Set()
  
  // 找到所有直接连接到当前节点的源节点
  edges.value.forEach(edge => {
    if (edge.target === nodeId) {
      const sourceNode = nodes.value.find(n => n.id === edge.source)
      if (sourceNode && sourceNode.type !== 'start') {
        prevNodeIds.add(edge.source)
      }
    }
  })
  
  // 转换为选项格式
  return Array.from(prevNodeIds).map(id => {
    const node = nodes.value.find(n => n.id === id)
    return {
      label: node.data.label || node.id,
      value: id
    }
  })
})

// 计算当前连线可用的条件选项
const currentEdgeConditionOptions = computed(() => {
  if (!selectedEdge.value) return edgeConditionOptions
  
  const sourceNode = nodes.value.find(n => n.id === selectedEdge.value.source)
  if (!sourceNode) return edgeConditionOptions
  
  // 根据源节点类型过滤选项
  switch (sourceNode.type) {
    case 'condition':
      // 条件节点只能用 true/false
      return edgeConditionOptions.filter(opt => ['true', 'false'].includes(opt.value))
    default:
      // 其他节点只用 always
      return edgeConditionOptions.filter(opt => opt.value === 'always')
  }
})

// 连线条件描述
const edgeConditionDescription = computed(() => {
  const descriptions = {
    'always': '无论节点执行结果如何，都会执行后续节点',
    'true': '当前置条件节点结果为真时执行',
    'false': '当前置条件节点结果为假时执行',
    'success': '当节点执行成功时执行后续节点',
    'failed': '当节点执行失败时执行后续节点'
  }
  return descriptions[editEdgeCondition.value] || ''
})

// 获取选中的连线源节点
const selectedEdgeSourceNode = computed(() => {
  if (!selectedEdge.value) return null
  return nodes.value.find(n => n.id === selectedEdge.value.source)
})

// 插入节点变量
const insertNodeVariable = (nodeId) => {
  if (!nodeId) return
  
  const node = nodes.value.find(n => n.id === nodeId)
  if (!node) return
  
  let variable = ''
  switch (node.type) {
    case 'task':
      variable = `outputs.${nodeId}.status == 'success'`
      break
    case 'condition':
      variable = `outputs.${nodeId}.condition_result == True`
      break
    case 'wait':
      variable = `outputs.${nodeId}.status == 'success'`
      break
    case 'notification':
      variable = `outputs.${nodeId}.status == 'success'`
      break
    default:
      variable = `outputs.${nodeId}.status == 'success'`
  }
  
  // 追加到表达式
  if (editConfig.value.expression) {
    editConfig.value.expression += ` and ${variable}`
  } else {
    editConfig.value.expression = variable
  }
  
  // 自动应用更改
  applyEdit()
}

// 根据ID获取节点
const getNodeById = (nodeId) => {
  return nodes.value.find(n => n.id === nodeId)
}

// 复制变量到剪贴板
const copyVariable = (variable) => {
  navigator.clipboard.writeText(variable).then(() => {
    window.$message.success(`已复制: ${variable}`)
  }).catch(() => {
    window.$message.error('复制失败')
  })
}

// 动态生成常用表达式
const dynamicConditionExamples = computed(() => {
  if (!selectedNode.value || selectedNode.value.type !== 'condition') {
    return []
  }
  
  const prevNodes = previousNodes.value
  if (prevNodes.length === 0) {
    return [
      { label: '总是为真', value: 'True' },
      { label: '总是为假', value: 'False' }
    ]
  }
  
  const examples = [
    { label: '总是为真', value: 'True' },
    { label: '总是为假', value: 'False' }
  ]
  
  // 根据前置节点类型生成表达式
  const taskNodes = prevNodes.filter(n => getNodeById(n.value)?.type !== 'condition')
  const conditionNodes = prevNodes.filter(n => getNodeById(n.value)?.type === 'condition')
  
  // 任务节点表达式
  if (taskNodes.length > 0) {
    if (taskNodes.length === 1) {
      const node = taskNodes[0]
      examples.push({
        label: `${node.label}(${node.value})执行成功`,
        value: `outputs.${node.value}.status == 'success'`
      })
      examples.push({
        label: `${node.label}(${node.value})执行失败`,
        value: `outputs.${node.value}.status == 'failed'`
      })
    } else if (taskNodes.length === 2) {
      const node1 = taskNodes[0]
      const node2 = taskNodes[1]
      examples.push({
        label: '所有任务都成功',
        value: `outputs.${node1.value}.status == 'success' and outputs.${node2.value}.status == 'success'`
      })
      examples.push({
        label: '任意一个任务失败',
        value: `outputs.${node1.value}.status == 'failed' or outputs.${node2.value}.status == 'failed'`
      })
    } else if (taskNodes.length >= 3) {
      const nodeIds = taskNodes.map(n => n.value).join(', ')
      examples.push({
        label: `所有任务都成功 (${taskNodes.length}个)`,
        value: taskNodes.map(n => `outputs.${n.value}.status == 'success'`).join(' and ')
      })
      examples.push({
        label: `任意一个任务失败 (${taskNodes.length}个)`,
        value: taskNodes.map(n => `outputs.${n.value}.status == 'failed'`).join(' or ')
      })
    }
  }
  
  // 条件节点表达式
  if (conditionNodes.length > 0) {
    conditionNodes.forEach(node => {
      examples.push({
        label: `${node.label}(${node.value})结果为真`,
        value: `outputs.${node.value}.condition_result == True`
      })
      examples.push({
        label: `${node.label}(${node.value})结果为假`,
        value: `outputs.${node.value}.condition_result == False`
      })
    })
  }
  
  // 输入参数表达式
  examples.push({ label: '输入参数大于5', value: 'inputs.count > 5' })
  examples.push({ label: '输入参数等于指定值', value: "inputs.status == 'active'" })
  
  return examples
})

const conditionExamples = [
  { label: '总是为真', value: 'True' },
  { label: '总是为假', value: 'False' },
  { label: '任务节点(n1)执行成功', value: "outputs.n1.status == 'success'" },
  { label: '任务节点(n1)执行失败', value: "outputs.n1.status == 'failed'" },
  { label: '条件节点(condition1)结果为真', value: "outputs.condition1.condition_result == True" },
  { label: '条件节点(condition1)结果为假', value: "outputs.condition1.condition_result == False" },
  { label: '输入参数大于5', value: 'inputs.count > 5' },
  { label: '输入参数等于指定值', value: "inputs.status == 'active'" },
  { label: '多个任务都成功', value: "outputs.n1.status == 'success' and outputs.n2.status == 'success'" },
  { label: '任意一个任务失败', value: "outputs.n1.status == 'failed' or outputs.n2.status == 'failed'" },
  { label: '引用前置条件节点结果', value: "outputs.condition1.condition_result == True" }
]

// 加载任务列表
const loadJobs = async () => {
  try {
    const res = await window.$request.post('/cron/jobsList', {node_ids:[] } )
    jobOptions.value = (res?.items || res || []).map(j => ({
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
      animated: true,
      condition: e.condition || 'always'
    }))
  }
  
  // 初始化历史记录
  saveToHistory()
})

// 保存当前状态到历史记录
const saveToHistory = () => {
  const state = {
    nodes: JSON.parse(JSON.stringify(nodes.value)),
    edges: JSON.parse(JSON.stringify(edges.value))
  }
  
  // 如果当前不在历史记录末尾，删除后面的记录
  if (historyIndex.value < history.value.length - 1) {
    history.value = history.value.slice(0, historyIndex.value + 1)
  }
  
  history.value.push(state)
  historyIndex.value = history.value.length - 1
  
  // 限制历史记录数量
  if (history.value.length > 50) {
    history.value.shift()
    historyIndex.value--
  }
}

// 撤销
const handleUndo = () => {
  if (!canUndo.value) return
  historyIndex.value--
  const state = history.value[historyIndex.value]
  nodes.value = JSON.parse(JSON.stringify(state.nodes))
  edges.value = JSON.parse(JSON.stringify(state.edges))
}

// 重做
const handleRedo = () => {
  if (!canRedo.value) return
  historyIndex.value++
  const state = history.value[historyIndex.value]
  nodes.value = JSON.parse(JSON.stringify(state.nodes))
  edges.value = JSON.parse(JSON.stringify(state.edges))
}

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
  const id = `n${nodeCounter.value++}`
  nodes.value.push({
    id,
    type: dragType.type,
    position: pos,
    data: { label: `${dragType.label}节点`, config: {} }
  })
  dragType = null
  saveToHistory()
}

// 点击节点
const onNodeClick = (e) => {
  selectedId.value = e.node.id
  selectedNode.value = e.node
  selectedEdge.value = null
  editLabel.value = e.node.data.label
  editConfig.value = { ...e.node.data.config }
}

// 点击连线
const onEdgeClick = (e) => {
  selectedEdge.value = e.edge
  selectedNode.value = null
  selectedId.value = null
  editEdgeCondition.value = e.edge.condition || 'always'
}

// 连线
const onConnect = (conn) => {
  edges.value.push({
    id: `e${Date.now()}`,
    source: conn.source,
    target: conn.target,
    animated: true,
    condition: 'always'
  })
  saveToHistory()
}

// 应用连线编辑
const applyEdgeEdit = () => {
  if (!selectedEdge.value) return
  const idx = edges.value.findIndex(e => e.id === selectedEdge.value.id)
  if (idx >= 0) {
    edges.value[idx].condition = editEdgeCondition.value
  }
  saveToHistory()
}

// 删除连线
const deleteEdge = () => {
  if (!selectedEdge.value) return
  const idx = edges.value.findIndex(e => e.id === selectedEdge.value.id)
  if (idx >= 0) {
    edges.value.splice(idx, 1)
  }
  selectedEdge.value = null
  saveToHistory()
}

// 应用编辑（失焦时）
const applyEdit = () => {
  if (!selectedId.value) return
  const idx = nodes.value.findIndex(n => n.id === selectedId.value)
  if (idx >= 0) {
    nodes.value[idx].data.label = editLabel.value
    nodes.value[idx].data.config = { ...editConfig.value }
  }
  saveToHistory()
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
  saveToHistory()
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
    edges: edges.value.map(e => ({ 
      source: e.source, 
      target: e.target,
      condition: e.condition || 'always'
    }))
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
.wf-node.and { border-color: #13c2c2; }
.wf-node.or { border-color: #eb2f96; }
.wf-node.start { border-color: #52c41a; background: #f6ffed; }
.wf-node.end { border-color: #ff4d4f; background: #fff1f0; }
</style>

<style>
/* 全局样式 */
.vue-flow { background: #fafafa; }
.vue-flow__handle { width: 10px !important; height: 10px !important; background: #18a058 !important; border: 2px solid #fff !important; }
.vue-flow__edge-path { stroke: #999; stroke-width: 2; }
</style>
