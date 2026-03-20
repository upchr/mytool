<template>
  <div class="workflow-page">
    <!-- 列表 -->
    <n-card v-if="!showEditor">
      <template #header>
        <n-space justify="space-between">
          <n-text strong style="font-size: 18px">🔄 工作流管理</n-text>
          <n-button type="primary" @click="handleCreate">新建工作流</n-button>
        </n-space>
      </template>

      <n-alert type="info" style="margin-bottom: 16px">
        <template #header>什么是工作流？</template>
        工作流可以串联多个任务按顺序执行，支持条件判断、等待、通知等节点。点击「新建」进入可视化编辑器。
      </n-alert>

      <n-empty v-if="!loading && list.length === 0">
        <template #extra>
          <n-button type="primary" @click="handleCreate">新建工作流</n-button>
        </template>
      </n-empty>

      <n-list v-else bordered>
        <n-list-item v-for="wf in list" :key="wf.id">
          <n-thing>
            <template #header>
              <n-space>
                <n-text strong>{{ wf.name }}</n-text>
                <n-tag :type="wf.is_active ? 'success' : 'default'" size="small">{{ wf.is_active ? '启用' : '禁用' }}</n-tag>
                <n-tag v-if="wf.default_version" type="info" size="small">v{{ wf.default_version }}</n-tag>
                <n-tag v-if="wf.schedule" type="warning" size="small">⏰ {{ wf.schedule }}</n-tag>
              </n-space>
            </template>
            <template #header-extra>
              <n-space>
                <n-button size="small" quaternary @click="handleSchedule(wf)">
                  <template #icon>
                    <n-icon><ClockIcon /></n-icon>
                  </template>
                  定时
                </n-button>
                <n-button size="small" quaternary @click="handleVersions(wf)">
                  <template #icon>
                    <n-icon><GitBranchIcon /></n-icon>
                  </template>
                  版本
                </n-button>
                <n-button size="small" quaternary @click="handleExecutions(wf)">
                  <template #icon>
                    <n-icon><ListIcon /></n-icon>
                  </template>
                  执行记录
                </n-button>
                <n-button size="small" type="primary" @click="handleEdit(wf)">
                  <template #icon>
                    <n-icon><CreateIcon /></n-icon>
                  </template>
                  编辑
                </n-button>
                <n-button size="small" type="success" @click="handleTrigger(wf)">
                  <template #icon>
                    <n-icon><PlayIcon /></n-icon>
                  </template>
                  执行
                </n-button>
                <n-button size="small" type="error" @click="handleDelete(wf)">
                  <template #icon>
                    <n-icon><TrashIcon /></n-icon>
                  </template>
                  删除
                </n-button>
              </n-space>
            </template>
            <template #description>
              <n-text depth="3">{{ wf.description || '暂无描述' }}</n-text>
            </template>
          </n-thing>
        </n-list-item>
      </n-list>
    </n-card>

    <!-- 编辑器 -->
    <WorkflowEditor
      v-else
      ref="editorRef"
      :workflow-id="current?.workflow_id"
      :workflow-name="currentWorkflowName"
      :initial-data="{ nodes: current?.nodes || [], edges: current?.edges || [] }"
      @save="onSave"
      @trigger="onTrigger"
      @back="showEditor = false"
      @update:workflow-name="onWorkflowNameUpdate"
    />

    <!-- 输入参数对话框 -->
    <n-modal v-model:show="showInputDialog" preset="dialog" title="输入参数" style="width: 600px">
      <n-alert v-if="getUsedInputs().length > 0" type="success" style="margin-bottom: 12px">
        <template #header>💡 检测到工作流需要以下输入参数</template>
        <div style="font-size: 11px; line-height: 1.6;">
          <n-space>
            <n-tag v-for="input in getUsedInputs()" :key="input" type="info" size="small">
              inputs.{{ input }}
            </n-tag>
          </n-space>
        </div>
        <div style="margin-top: 8px; font-size: 10px; color: #666;">
          这些参数已在下方列出，请填写对应的值
        </div>
      </n-alert>

      <n-form label-placement="left" label-width="120px">
        <div v-for="(param, index) in inputParamsList" :key="index" style="margin-bottom: 12px">
          <n-space align="center">
            <n-input
              v-model:value="param.name"
              placeholder="参数名"
              style="width: 150px"
              :disabled="param.required"
            />
            <n-input
              v-model:value="param.value"
              placeholder="参数值"
              style="flex: 1"
            />
            <n-button
              v-if="!param.required"
              type="error"
              size="small"
              @click="removeParam(index)"
              :disabled="param.required"
            >
              删除
            </n-button>
            <n-tag v-else type="warning" size="small">必需</n-tag>
          </n-space>
        </div>

        <n-button @click="addParam" type="primary" dashed style="width: 100%; margin-top: 8px">
          + 添加参数
        </n-button>
      </n-form>

      <n-alert v-if="inputParamsError" type="error" style="margin-top: 12px">
        {{ inputParamsError }}
      </n-alert>
      <n-alert type="info" style="margin-top: 12px">
        <template #header>💡 提示</template>
        <div style="font-size: 11px; line-height: 1.6;">
          • 参数值可以是字符串、数字、布尔值或JSON对象<br>
          • 字符串值建议用引号包裹，如："active"<br>
          • 数字直接输入，如：10<br>
          • 布尔值输入：true 或 false
        </div>
      </n-alert>

      <template #action>
        <n-space>
          <n-button @click="showInputDialog = false">取消</n-button>
          <n-button type="primary" @click="confirmTrigger">确定</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 版本管理对话框 -->
    <n-modal v-model:show="showVersionsDialog" preset="card" title="版本管理" style="width: 800px" @after-leave="loadList">
      <template #header-extra>
        <n-space>
          <n-button type="primary" size="small" @click="handleCreateVersion">创建新版本</n-button>
        </n-space>
      </template>

      <n-empty v-if="versions.length === 0" description="暂无版本记录" />

      <n-timeline v-else>
        <n-timeline-item
          v-for="version in versions"
          :key="version.id"
          :type="version.is_default ? 'success' : 'default'"
        >
          <template #header>
            <n-space align="center">
              <n-text strong>v{{ version.version }} - {{ version.name }}</n-text>
              <n-tag v-if="version.is_default" type="success" size="small" style="font-weight: bold; padding: 4px 12px;">⭐ 默认版本</n-tag>
            </n-space>
          </template>
          <div style="margin-bottom: 8px;">
            <n-text depth="3">{{ version.description || '暂无描述' }}</n-text>
          </div>
          <div style="margin-bottom: 8px;">
            <n-text depth="2" style="font-size: 12px;">
              变更说明: {{ version.change_note || '无' }}
            </n-text>
          </div>
          <div style="margin-bottom: 8px;">
            <n-text depth="2" style="font-size: 12px;">
              创建者: {{ version.created_by || '未知' }} | 创建时间: {{ formatTime(version.created_at) }}
            </n-text>
          </div>
          <n-space>
            <n-button
              size="small"
              :type="version.is_default ? 'success' : 'primary'"
              @click="handleEditVersion(version)"
            >
              编辑
            </n-button>
            <n-button
              v-if="version.is_default"
              size="small"
              type="default"
              disabled
            >
              已是默认
            </n-button>
            <n-button
              v-else
              size="small"
              type="info"
              @click="handleSetDefaultVersion(version)"
            >
              设为默认
            </n-button>
          </n-space>
        </n-timeline-item>
      </n-timeline>

      <template #footer>
        <n-button @click="showVersionsDialog = false">关闭</n-button>
      </template>
    </n-modal>

    <!-- 执行记录对话框 -->
    <n-modal v-model:show="showExecutionsDialog" preset="card" title="📋 执行记录" style="width: 900px; max-height: 80vh;">
      <n-empty v-if="executions.length === 0" description="暂无执行记录" />

      <n-scrollbar v-else style="max-height: 60vh;">
        <n-timeline>
          <n-timeline-item
            v-for="execution in executions"
            :key="execution.id"
            :type="execution.status === 'success' ? 'success' : (execution.status === 'failed' ? 'error' : 'info')"
          >
            <template #header>
              <n-space align="center">
                <n-text strong>执行 #{{ execution.id }}</n-text>
                <n-tag :type="execution.status === 'success' ? 'success' : (execution.status === 'failed' ? 'error' : 'info')" size="small">
                  {{ execution.status === 'success' ? '成功' : (execution.status === 'failed' ? '失败' : '进行中') }}
                </n-tag>
              </n-space>
            </template>
            <div style="margin-bottom: 8px;">
              <n-text depth="3" style="font-size: 12px;">
                触发方式: {{ execution.triggered_by === 'manual' ? '手动' : (execution.triggered_by === 'schedule' ? '定时' : '系统') }} |
                开始时间: {{ formatTime(execution.start_time) }}
                <span v-if="execution.end_time"> | 结束时间: {{ formatTime(execution.end_time) }}</span>
              </n-text>
            </div>
            <div v-if="execution.inputs && Object.keys(execution.inputs).length > 0" style="margin-bottom: 8px;">
              <n-text depth="2" style="font-size: 11px;">输入参数: {{ JSON.stringify(execution.inputs) }}</n-text>
            </div>
            <div v-if="execution.error" style="margin-bottom: 8px;">
              <n-alert type="error" size="small">{{ execution.error }}</n-alert>
            </div>
            <n-space>
              <n-button size="small" type="primary" @click="handleViewNodeLogs(execution.id)">
                查看节点执行日志
              </n-button>
              <n-button size="small" type="info" @click="handleViewGraphLog(execution)">
                查看图形化日志
              </n-button>
            </n-space>
          </n-timeline-item>
        </n-timeline>
      </n-scrollbar>

      <template #footer>
        <n-button @click="showExecutionsDialog = false">关闭</n-button>
      </template>
    </n-modal>

    <!-- 节点执行日志对话框 -->
    <n-modal v-model:show="showNodeLogsDialog" preset="card" title="📝 节点执行日志" style="width: 1000px; max-height: 85vh;">
      <n-empty v-if="nodeExecutions.length === 0" description="暂无节点执行记录" />

      <n-scrollbar v-else style="max-height: 70vh;">
        <n-collapse accordion>
          <n-collapse-item v-for="nodeExec in nodeExecutions" :key="nodeExec.id" :title="`${nodeExec.node_name} (${nodeExec.node_type})`">
            <template #header-extra>
              <n-tag :type="nodeExec.status === 'success' ? 'success' : (nodeExec.status === 'failed' ? 'error' : 'info')" size="small">
                {{ nodeExec.status === 'success' ? '成功' : (nodeExec.status === 'failed' ? '失败' : '进行中') }}
              </n-tag>
            </template>

            <div style="padding: 12px; background: #f5f5f5; border-radius: 4px; margin-bottom: 12px;">
              <n-descriptions :column="2" size="small" bordered>
                <n-descriptions-item label="节点ID">{{ nodeExec.node_id }}</n-descriptions-item>
                <n-descriptions-item label="节点类型">{{ nodeExec.node_type }}</n-descriptions-item>
                <n-descriptions-item label="开始时间">{{ formatTime(nodeExec.start_time) }}</n-descriptions-item>
                <n-descriptions-item label="结束时间">{{ nodeExec.end_time ? formatTime(nodeExec.end_time) : '进行中' }}</n-descriptions-item>
                <n-descriptions-item label="执行时长" :span="2">
                  {{ nodeExec.end_time ? calculateDuration(nodeExec.start_time, nodeExec.end_time) : '进行中' }}
                </n-descriptions-item>
              </n-descriptions>
            </div>

            <div v-if="nodeExec.output" style="margin-bottom: 12px;">
              <n-text depth="2" style="font-size: 12px; font-weight: bold;">输出:</n-text>
              <n-code :code="nodeExec.output" language="text" :word-wrap="true" style="margin-top: 4px;" />
            </div>

            <div v-if="nodeExec.error" style="margin-bottom: 12px;">
              <n-alert type="error" size="small" title="错误信息">{{ nodeExec.error }}</n-alert>
            </div>

            <div v-if="nodeExec.logs && nodeExec.logs.length > 0">
              <n-text depth="2" style="font-size: 12px; font-weight: bold; margin-bottom: 8px;">执行日志:</n-text>
              <n-timeline size="small">
                <n-timeline-item
                  v-for="(log, index) in nodeExec.logs"
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
          </n-collapse-item>
        </n-collapse>
      </n-scrollbar>

      <template #footer>
        <n-button @click="showNodeLogsDialog = false">关闭</n-button>
      </template>
    </n-modal>

    <!-- 定时设置对话框 -->
    <n-modal v-model:show="showScheduleDialog" preset="card" title="⏰ 定时设置" style="width: 600px">
      <n-form label-placement="top" size="small">
        <n-alert type="info" size="small" style="margin-bottom: 12px">
          <template #header>💡 定时设置说明</template>
          <div style="font-size: 11px; line-height: 1.6">
            <div><strong>Cron 表达式</strong>：用于定义工作流的定时执行规则</div>
            <div style="margin-top: 4px; color: #666;">
              • 格式：分 时 日 月 周
            </div>
            <div style="margin-top: 4px; color: #666;">
              • 示例：<code style="background: #f0f0f0; padding: 2px 4px; border-radius: 3px;">0 0 * * *</code>（每天0点执行）
            </div>
            <div style="margin-top: 4px; color: #666;">
              • 示例：<code style="background: #f0f0f0; padding: 2px 4px; border-radius: 3px;">*/5 * * * *</code>（每5分钟执行）
            </div>
            <div style="margin-top: 4px; color: #666;">
              • 示例：<code style="background: #f0f0f0; padding: 2px 4px; border-radius: 3px;">0 0 * * 1</code>（每周一0点执行）
            </div>
          </div>
        </n-alert>

        <n-form-item label="Cron 表达式">
          <n-input
            v-model:value="editingSchedule"
            placeholder="* * * * *【分 时 日 月 周】"
          >
            <template #suffix>
              <n-button text @click="showCronGenerator = true" style="color: grey">
                <n-icon><CalendarOutline /></n-icon>
                生成器
              </n-button>
            </template>
          </n-input>

          <CronGenerator
            v-model:show="showCronGenerator"
            :cron="editingSchedule"
            @update:cron="editingSchedule = $event"
            @close="showCronGenerator = false"
          />
        </n-form-item>

        <n-form-item label="常用表达式">
          <n-space vertical style="width: 100%">
            <n-select
              :options="scheduleExamples"
              placeholder="选择示例"
              @update:value="(val) => { editingSchedule = val }"
            />
          </n-space>
        </n-form-item>

        <n-form-item label="启用定时任务">
          <n-switch v-model:value="editingWorkflowActive">
            <template #checked>停用</template>
            <template #unchecked>启用</template>
          </n-switch>
          <div style="margin-top: 8px; font-size: 11px; color: #666;">
            启用后，工作流将按照设置的 Cron 表达式自动执行
          </div>
        </n-form-item>
      </n-form>

      <template #footer>
        <n-space justify="end">
          <n-button @click="showScheduleDialog = false">取消</n-button>
          <n-button type="primary" @click="handleSaveSchedule">保存</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import WorkflowEditor from './WorkflowEditor.vue'
import CronGenerator from '@/components/CronGenerator.vue'
import {
  CalendarOutline,
  AlarmOutline as ClockIcon,
  GitBranchOutline as GitBranchIcon,
  ListOutline as ListIcon,
  CreateOutline as CreateIcon,
  PlayOutline as PlayIcon,
  TrashOutline as TrashIcon
} from '@vicons/ionicons5'

const router = useRouter()
const loading = ref(false)
const list = ref([])
const showEditor = ref(false)
const editorRef = ref(null)
const current = ref(null)
const currentWorkflowName = ref('')
const currentEditingVersion = ref(null)

// 版本管理
const showVersionsDialog = ref(false)
const versions = ref([])

// 定时设置
const showScheduleDialog = ref(false)
const showCronGenerator = ref(false)
const editingWorkflow = ref(null)
const editingSchedule = ref('')
const editingWorkflowActive = ref(true)

// 输入参数对话框
const showInputDialog = ref(false)
const inputParamsList = ref([])
const inputParamsError = ref('')
const usedInputs = ref([])

// 执行记录对话框
const showExecutionsDialog = ref(false)
const executions = ref([])
const currentExecutionWorkflow = ref(null)

// 节点执行日志对话框
const showNodeLogsDialog = ref(false)
const nodeExecutions = ref([])

// 获取当前工作流使用的输入参数
const getUsedInputs = () => {
  return usedInputs.value
}

// 添加参数
const addParam = () => {
  inputParamsList.value.push({ name: '', value: '', required: false })
}

// 删除参数
const removeParam = (index) => {
  if (inputParamsList.value[index].required) return
  inputParamsList.value.splice(index, 1)
}

// 工作流名称更新
const onWorkflowNameUpdate = (name) => {
  currentWorkflowName.value = name
}

const loadList = async () => {
  loading.value = true
  try {
    const r = await window.$request.get('/workflows', { params: { page: 1, page_size: 100 } })
    list.value = r.items || []
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  current.value = { workflow_id: '', name: '', nodes: [], edges: [] }
  currentWorkflowName.value = '新工作流'
  showEditor.value = true
}

const handleEdit = async (wf) => {
  try {
    // 获取工作流的默认版本
    const r = await window.$request.get(`/workflows/${wf.workflow_id}/versions`)
    const versions = r.items || r || []

    // 找到默认版本
    const defaultVersion = versions.find(v => v.is_default)

    if (defaultVersion) {
      // 加载默认版本的数据
      current.value = {
        workflow_id: wf.workflow_id,
        name: wf.name,
        description: wf.description,
        nodes: defaultVersion.nodes || [],
        edges: defaultVersion.edges || []
      }
      currentWorkflowName.value = wf.name
      currentEditingVersion.value = null
    } else {
      // 如果没有版本，直接使用工作流数据
      current.value = wf
      currentWorkflowName.value = wf.name || ''
      currentEditingVersion.value = null
    }

    showEditor.value = true
  } catch (e) {
    window.$message.error('加载工作流失败')
  }
}

const handleDelete = async (wf) => {
  window.$dialog.warning({
    title: '确认删除',
    content: `删除 "${wf.name}"？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      await window.$request.delete(`/workflows/${wf.workflow_id}`)
      window.$message.success('已删除')
      loadList()
    }
  })
}

const handleTrigger = async (wf) => {
  inputParamsError.value = ''

  try {
    // 获取工作流的默认版本数据
    const r = await window.$request.get(`/workflows/${wf.workflow_id}/versions`)
    const versions = r.items || r || []
    const defaultVersion = versions.find(v => v.is_default)

    // 使用默认版本的数据，如果没有默认版本则使用工作流数据
    const workflowData = defaultVersion ? {
      ...wf,
      nodes: defaultVersion.nodes || [],
      edges: defaultVersion.edges || []
    } : wf

    // 获取任务列表，用于分析任务命令中的占位符
    let jobs = []
    try {
      const jobsRes = await window.$request.post('/cron/jobsList', {node_ids:[] } )
      jobs = jobsRes.data || []
    } catch (e) {
      console.warn('获取任务列表失败', e)
    }

    // 设置当前工作流
    current.value = workflowData

    // 分析工作流中使用的输入参数
    const inputs = analyzeWorkflowInputs(workflowData, jobs)
    usedInputs.value = inputs

    // 生成输入参数列表
    inputParamsList.value = inputs.map(input => ({
      name: input,
      value: '',
      required: true
    }))

    showInputDialog.value = true
  } catch (e) {
    window.$message.error('加载工作流失败')
  }
}

// 分析工作流中使用的输入参数
const analyzeWorkflowInputs = (workflow, jobs = []) => {
  const inputs = new Set()

  // 遍历所有节点
  const nodes = workflow.nodes || []
  nodes.forEach(node => {
    const config = node.config || {}

    // 根据节点类型分析不同的配置字段
    if (node.type === 'condition') {
      // 条件节点：分析表达式
      const expression = config.expression || ''
      const matches = expression.match(/inputs\.(\w+)/g)
      if (matches) {
        matches.forEach(match => {
          const inputName = match.replace('inputs.', '')
          if (inputName && inputName !== 'xxx') {
            inputs.add(inputName)
          }
        })
      }
    } else if (node.type === 'task') {
      // 任务节点：分析命令
      const jobId = config.job_id
      if (jobId && jobs.length > 0) {
        const job = jobs.find(j => j.id === jobId)
        if (job && job.command) {
          const matches = job.command.match(/\{\{inputs\.(\w+)\}\}/g)
          if (matches) {
            matches.forEach(match => {
              const inputName = match.replace(/\{\{inputs\.|\}\}/g, '')
              if (inputName && inputName !== 'xxx') {
                inputs.add(inputName)
              }
            })
          }
        }
      }
    } else if (node.type === 'notification') {
      // 通知节点：分析标题和内容
      const title = config.title || ''
      const content = config.content || ''

      // 分析标题
      const titleMatches = title.match(/\{\{inputs\.(\w+)\}\}/g)
      if (titleMatches) {
        titleMatches.forEach(match => {
          const inputName = match.replace(/\{\{inputs\.|\}\}/g, '')
          if (inputName && inputName !== 'xxx') {
            inputs.add(inputName)
          }
        })
      }

      // 分析内容
      const contentMatches = content.match(/\{\{inputs\.(\w+)\}\}/g)
      if (contentMatches) {
        contentMatches.forEach(match => {
          const inputName = match.replace(/\{\{inputs\.|\}\}/g, '')
          if (inputName && inputName !== 'xxx') {
            inputs.add(inputName)
          }
        })
      }
    }
  })

  return Array.from(inputs)
}

const confirmTrigger = async () => {
  try {
    // 将输入参数列表转换为对象
    const inputs = {}
    inputParamsList.value.forEach(param => {
      if (param.name && param.value !== undefined && param.value !== '') {
        // 尝试解析参数值
        try {
          inputs[param.name] = JSON.parse(param.value)
        } catch (e) {
          // 如果不是JSON，直接使用字符串值
          inputs[param.name] = param.value
        }
      }
    })

    // 检查必需参数是否已填写
    const missingRequired = inputParamsList.value
      .filter(p => p.required && (!p.name || p.value === ''))
      .map(p => p.name)

    if (missingRequired.length > 0) {
      inputParamsError.value = `以下必需参数未填写：${missingRequired.join(', ')}`
      return
    }

    await window.$request.post('/workflows/trigger', {
      workflow_id: current.value.workflow_id,
      inputs: inputs
    })
    window.$message.success('已触发')
    showInputDialog.value = false
  } catch (e) {
    window.$message.error('触发失败')
  }
}

const onSave = async (data) => {
  try {
    // 先验证工作流格式
    const validation = await validateWorkflow(data)
    if (!validation.valid) {
      window.$message.error('工作流格式验证失败')
      window.$dialog.error({
        title: '工作流格式验证失败',
        content: `以下问题需要修复：\n${validation.errors.join('\n')}\n\n警告：\n${validation.warnings.join('\n')}`,
        positiveText: '确定'
      })
      return
    }

    // 如果有警告，提示用户
    if (validation.warnings.length > 0) {
      const proceed = await new Promise((resolve) => {
        window.$dialog.warning({
          title: '工作流格式警告',
          content: `以下警告可能影响工作流执行：\n${validation.warnings.join('\n')}\n\n是否继续保存？`,
          positiveText: '继续保存',
          negativeText: '取消',
          onPositiveClick: () => resolve(true),
          onNegativeClick: () => resolve(false)
        })
      })

      if (!proceed) return
    }
    const payload = {
      workflow_id: current.value.workflow_id || `wf-${Date.now()}`,
      name: currentWorkflowName.value || '新工作流',
      description: current.value.description || '',
      schedule: null,
      is_active: false,
      ...data
    }
    if (current.value.workflow_id) {
      // 如果正在编辑特定版本，传递版本号
      const params = currentEditingVersion.value ? { version: currentEditingVersion.value } : {}
      await window.$request.put(`/workflows/${current.value.workflow_id}`, payload, { params })
    } else {
      await window.$request.post('/workflows', payload)
    }
    window.$message.success('保存成功')

    // 弹框询问是否继续编辑
    window.$dialog.success({
      title: '保存成功',
      content: '工作流已保存，是否继续编辑？',
      positiveText: '继续编辑',
      negativeText: '返回列表',
      onPositiveClick: () => {
        // 继续编辑，不做任何操作
      },
      onNegativeClick: () => {
        // 返回列表
        showEditor.value = false
        loadList()
      }
    })
  } catch (e) {
    window.$message.error('保存失败')
  }
}

const scheduleExamples = [
  { label: '每天0点执行', value: '0 0 * * *' },
  { label: '每5分钟执行', value: '*/5 * * * *' },
  { label: '每小时执行', value: '0 * * * *' },
  { label: '每周一0点执行', value: '0 0 * * 1' },
  { label: '每月1号0点执行', value: '0 0 1 * *' },
  { label: '工作日每天9点执行', value: '0 9 * * 1-5' }
]

const handleSchedule = (wf) => {
  editingWorkflow.value = wf
  editingSchedule.value = wf.schedule || ''
  editingWorkflowActive.value = wf.is_active !== undefined ? wf.is_active : true
  showScheduleDialog.value = true
}

const handleSaveSchedule = async () => {
  if (!editingWorkflow.value) return

  try {
    await window.$request.put(`/workflows/${editingWorkflow.value.workflow_id}`, {
      schedule: editingSchedule.value || null,
      is_active: editingWorkflowActive.value
    })

    window.$message.success('定时设置已保存')
    showScheduleDialog.value = false
    loadList()
  } catch (e) {
    window.$message.error('保存失败')
  }
}

// 验证工作流格式
const validateWorkflow = async (data) => {
  try {
    const r = await window.$request.post('/workflows/validate', data)
    return r.data || r
  } catch (e) {
    return { valid: false, errors: ['验证请求失败'], warnings: [] }
  }
}

// 版本管理
const handleVersions = async (wf) => {
  current.value = wf
  try {
    const r = await window.$request.get(`/workflows/${wf.workflow_id}/versions`)
    versions.value = r.items || r || []
    showVersionsDialog.value = true
  } catch (e) {
    window.$message.error('加载版本失败')
  }
}

const handleCreateVersion = async () => {
  try {
    // 直接创建新版本（从默认版本复制）
    await window.$request.post(`/workflows/${current.value.workflow_id}/versions`)

    window.$message.success('版本创建成功')

    // 重新加载版本列表
    const r2 = await window.$request.get(`/workflows/${current.value.workflow_id}/versions`)
    versions.value = r2.items || r2 || []
  } catch (e) {
    window.$message.error('创建版本失败')
  }
}

const handleSetDefaultVersion = async (version) => {
  try {
    await window.$request.put(`/workflows/${current.value.workflow_id}/versions/${version.id}/default`)
    window.$message.success('默认版本设置成功')

    // 重新加载版本列表
    const r = await window.$request.get(`/workflows/${current.value.workflow_id}/versions`)
    versions.value = r.items || r || []
  } catch (e) {
    window.$message.error('设置默认版本失败')
  }
}

const handleEditVersion = async (version) => {
  showVersionsDialog.value = false

  try {
    // 获取工作流信息
    const workflow = await window.$request.get(`/workflows/${current.value.workflow_id}`)

    current.value = {
      workflow_id: current.value.workflow_id,
      name: workflow.name,
      description: workflow.description,
      nodes: version.nodes || [],
      edges: version.edges || []
    }
    currentWorkflowName.value = workflow.name
    currentEditingVersion.value = version.version
    showEditor.value = true
  } catch (e) {
    window.$message.error('加载版本失败')
  }
}

const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  return date.toLocaleString('zh-CN')
}

const calculateDuration = (startTime, endTime) => {
  if (!startTime || !endTime) return '进行中'
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

const handleExecutions = async (wf) => {
  currentExecutionWorkflow.value = wf
  try {
    const r = await window.$request.get(`/workflows/${wf.workflow_id}/executions`)
    executions.value = r.items || r || []
    showExecutionsDialog.value = true
  } catch (e) {
    window.$message.error('加载执行记录失败')
  }
}

const handleViewNodeLogs = async (executionId) => {
  try {
    const r = await window.$request.get(`/workflows/executions/${executionId}/nodes`)
    nodeExecutions.value = r || []
    showNodeLogsDialog.value = true
  } catch (e) {
    window.$message.error('加载节点执行日志失败')
  }
}

const handleViewGraphLog = (execution) => {
  router.push({
    path: '/workflow-execution-log',
    query: {
      workflowId: execution.workflow_id,
      executionId: execution.id
    }
  })
}

const onTrigger = () => {
  if (current.value.workflow_id) {
    handleTrigger(current.value)
  }
}

onMounted(() => loadList())
</script>

<style scoped>
.workflow-page { height: 100%; }
</style>
