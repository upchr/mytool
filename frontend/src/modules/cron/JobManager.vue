<template>
  <n-card title="⏰ 定时任务管理" class="mb-6">
    <!-- 任务筛选 -->
    <n-space justify="space-between" class="mb-4" style="margin-bottom: 20px">
      <n-space>
        <n-select
            v-model:value="selectedNodes"
            :options="nodeOptions"
            placeholder="选择节点"
            @update:value="loadJobs"
            multiple
            style="width: 200px">
          <!-- 全选插槽 -->
<!--          <template #action>-->
<!--            <n-button-->
<!--                text-->
<!--                size="small"-->
<!--                @click="toggleAllNodes"-->
<!--            >-->
<!--              {{ allNodesSelected ? '取消全选' : '全选' }}-->
<!--            </n-button>-->
<!--          </template>-->
        </n-select>
        <n-button type="primary" @click="addJobModal = true;">添加任务</n-button>
      </n-space>
    </n-space>

    <!-- 任务列表 -->
    <n-empty v-if="jobs.length === 0" description="暂无任务" />
    <n-collapse v-else @item-header-click="handleItemHeaderClick">
      <n-collapse-item v-for="job in jobs" :key="job.id" :title="getJobTitle(job)"  class="mb-2" :name="job.id">
        <n-card :bordered="false" class="shadow-sm">
          <template #header>
            <div class="flex justify-between items-start">
              <div style="margin-bottom: 10px">
                <span class="ml-2 text-xs text-gray-500">{{ getNodeName(job.node_id) }}：</span>
                <span class="font-bold">{{ job.name }}</span>
                <n-tag size="small" class="ml-2" type="info" style="margin-left: 10px;margin-right: 10px">{{ job.schedule }}</n-tag>

                <!-- 下次执行时间标签 -->
                <n-tag
                    v-if="job.next_run"
                    size="small"
                    type="success"
                    class="ml-2"
                >
                  下次：{{formatDate(job.next_run) }}
                </n-tag>
                <n-tag
                    v-else-if="!job.is_active"
                    size="small"
                    type="warning"
                    class="ml-2"
                >
                  已停用
                </n-tag>
              </div>
              <n-space>
                <n-button size="small" type="info" @click="executeJob(job)">立即执行</n-button>
                <n-button
                    size="small"
                    :type="job.is_active ? 'success' : 'warning'"
                    @click="toggleJob(job)"
                >
                  {{ job.is_active ? '停用' : '启用' }}
                </n-button>
                <n-popconfirm @positive-click="deleteJob(job)">
                  <template #trigger>
                    <n-button size="small" type="error">删除</n-button>
                  </template>
                  确定要删除任务 "{{ job.name }}" 吗？
                </n-popconfirm>
              </n-space>
            </div>
          </template>

          <n-collapse :default-expanded-names="['3']">
            <n-collapse-item title="命令详情" name="1">
              <pre class="bg-gray-50 p-2 rounded text-sm overflow-x-auto">
              <n-code :code="job.command" language="sh" show-line-numbers />
              </pre>
            </n-collapse-item>
            <n-collapse-item v-if="job.description" title="描述" name="2">
              <p>{{ job.description }}</p>
            </n-collapse-item>
            <n-collapse-item title="执行历史" name="3">
              <div
                  style="
                  max-height: 40vh;
                  overflow-y: auto;
                  border: 1px solid #f0f0f0;
                  border-radius: 6px;
                "
                >
                <n-table :bordered="false" size="small" class="mt-2">
                  <thead>
                  <tr>
                    <th>状态</th>
                    <th>时间</th>
                    <th>触发方式</th>
                  </tr>
                  </thead>
                  <tbody>
                  <tr v-for="exec in getRecentExecutions(job.id)" :key="exec.id" @click="showLog(exec)">
                    <td>
                      <n-tag
                          :type="
                            exec.status === 'success'
                              ? 'success'
                              : exec.status === 'failed'
                              ? 'error'
                              : exec.status === 'cancelled'
                              ? 'warning'
                              : 'info'
                          "
                          size="small"
                      >
                        {{ exec.status }}
                      </n-tag>
                    </td>
                    <td>{{ new Date(exec.start_time).toLocaleString() }}</td>
                    <td><n-tag size="small" type="info">{{ exec.triggered_by }}</n-tag></td>
                  </tr>
                  </tbody>
                </n-table>
              </div>
            </n-collapse-item>
          </n-collapse>
        </n-card>
      </n-collapse-item>
    </n-collapse>

    <!-- 添加任务模态框 -->
    <n-modal v-model:show="addJobModal" preset="card" title="添加新任务" style="width: 600px">
      <n-form ref="jobFormRef" :model="newJob" :rules="jobRules" label-placement="left" label-width="auto">
          <n-form-item path="node_id" label="所属节点">
<!--            <n-select v-model:value="newJob.node_id" :options="nodeOptions" />-->
            <n-select
                v-model:value="newJob.node_ids"
                :options="nodeOptions.filter(opt => opt.value !== '')"
                multiple
                placeholder="请选择节点"
            />
          </n-form-item>
          <n-form-item path="name" label="任务名称">
            <n-input v-model:value="newJob.name" placeholder="例如：每日备份" />
          </n-form-item>
          <n-form-item path="schedule" label="Cron表达式">
            <n-input v-model:value="newJob.schedule" placeholder="* * * * *【分 时 日 月 周 (例如: 0 2 * * * 表示每天凌晨2点)】" />
            <template #footer>
              <n-text depth="3" class="text-xs">
                格式：分(0-59) 时(0-23) 日(1-31) 月(1-12) 周(0-6)<br/>
                示例：0 2 * * * → 每天凌晨2点
              </n-text>
            </template>
          </n-form-item>
          <n-form-item path="command" label="执行命令">
            <n-input
                v-model:value="newJob.command"
                type="textarea"
                placeholder="例如: echo 'Hello World'"
                rows="4"
            />
          </n-form-item>
          <n-form-item path="description" label="描述">
            <n-input
                v-model:value="newJob.description"
                type="textarea"
                placeholder="任务说明"
                rows="2"
            />
          </n-form-item>
        <n-space justify="end" class="mt-4">
          <n-button @click="addJobModal = false">取消</n-button>
          <n-button type="primary" @click="addJob">保存任务</n-button>
        </n-space>
      </n-form>
    </n-modal>

    <!-- 日志模态框 -->
    <n-modal
        v-model:show="logModal"
        @after-leave="closeLogModal"
        preset="card"
        title="执行日志"
        style="width: 1200px; max-height: 80vh;min-height: 60vh"
    >
      <div class="space-y-4">
        <div class="flex justify-between items-center" style="margin-bottom: 20px">
          <n-tag :type="getLogStatusType(selectedExecution?.status)">
            {{ selectedExecution?.status }}
          </n-tag>
          <n-button
              v-if="['running', 'pending'].includes(selectedExecution?.status)"
              size="small"
              type="error"
              style="margin-left: 10px"
              @click="stopExecution"
          >
            中断执行
          </n-button>
          <n-text depth="3">执行ID: {{ selectedExecution?.id }}</n-text>
        </div>

        <!-- STDOUT -->
        <div>
          <n-text depth="3">STDOUT:</n-text>
          <div
              ref="stdoutRef"
              class="bg-gray-50 p-2 rounded text-sm font-mono"
              style="
              height: 25vh;
              overflow-y: auto;
              overflow-x: auto;
              white-space: pre-wrap;
              word-break: break-word;
      "
          >
            {{ selectedExecution?.output || '无输出' }}
          </div>
        </div>

        <!-- STDERR -->
        <div>
          <n-text depth="3">STDERR:</n-text>
          <div
              ref="stderrRef"
              class="bg-red-50 p-2 rounded text-sm font-mono text-red-700"
              style="
                height: 25vh;
                overflow-y: auto;
                overflow-x: auto;
                white-space: pre-wrap;
                word-break: break-word;
              "
          >
            {{ selectedExecution?.error || '无错误' }}
          </div>
        </div>
      </div>
    </n-modal>
  </n-card>
</template>

<script setup>
import {ref, onMounted, onUnmounted, computed, nextTick} from 'vue'
import axios from 'axios'
import {useMessage} from 'naive-ui'

const message = useMessage()
const nodes = ref([])
const jobs = ref([])
const executions = ref({})
const selectedNodes = ref([])
const addJobModal = ref(false)
const logModal = ref(false)
const selectedExecution = ref(null)

const newJob = ref({
  node_ids: [],
  name: '',
  schedule: '',
  command: '',
  description: '',
  is_active: false
})

const jobFormRef = ref(null)

// Cron 表达式正则（支持标准 5 位格式）
const CRON_REGEX = /^(\*|(\*\/\d{1,2})|(\d{1,2})(-\d{1,2})?(\/\d{1,2})?)(,(\*|(\*\/\d{1,2})|(\d{1,2})(-\d{1,2})?(\/\d{1,2})?))*\s+(\*|(\*\/\d{1,2})|([01]?\d|2[0-3])(-([01]?\d|2[0-3]))?(\/\d{1,2})?)(,(\*|(\*\/\d{1,2})|([01]?\d|2[0-3])(-([01]?\d|2[0-3]))?(\/\d{1,2})?))*\s+(\*|(\*\/\d{1,2})|([1-9]|[12]\d|3[01])(-([1-9]|[12]\d|3[01]))?(\/\d{1,2})?)(,(\*|(\*\/\d{1,2})|([1-9]|[12]\d|3[01])(-([1-9]|[12]\d|3[01]))?(\/\d{1,2})?))*\s+(\*|(\*\/\d{1,2})|(1[0-2]|[1-9])(-(1[0-2]|[1-9]))?(\/\d{1,2})?)(,(\*|(\*\/\d{1,2})|(1[0-2]|[1-9])(-(1[0-2]|[1-9]))?(\/\d{1,2})?))*\s+(\*|(\*\/\d{1,2})|[0-6](-[0-6])?(\/\d{1,2})?)(,(\*|(\*\/\d{1,2})|[0-6](-[0-6])?(\/\d{1,2})?))*$/;

const jobRules = {
  node_ids: [
    {
      required: true,
      validator: (rule, value) => {
        return value && value.length > 0
      },
      message: '请选择至少一个节点',
      trigger: ['blur', 'change']
    }
  ],
  name: { required: true, message: '请输入任务名称', trigger: ['blur'] },
  schedule: [
    { required: true, message: '请输入Cron表达式', trigger: ['blur'] },
    {
      validator: (rule, value) => CRON_REGEX.test(value.trim()),
      message: 'Cron表达式格式错误（分 时 日 月 周）',
      trigger: ['blur']
    }
  ],
  command: { required: true, message: '请输入执行命令', trigger: ['blur'] }
}
const nodeOptions = computed(() => [
  // {label: '所有节点', value: ''},
  ...nodes.value.map(node => ({
    label: `${node.name} (${node.host})`,
    value: node.id
  }))
])

const loadNodes = async () => {
  try {
    const res = await axios.get('/api/cron/nodes/true')
    nodes.value = res.data
  } catch (error) {
    message.error('加载节点失败')
  }
}
// 添加响应式变量
const expandedJobs = ref(new Set()) // 存储已展开的任务ID

// 监听展开/折叠事件
const handleItemHeaderClick = (node) => {
  if (node.expanded && !executions.value[node.name]) {
    // 只在首次展开时加载
    loadRecentExecutions(node.name)
  }
  if (node.expanded) {
    expandedJobs.value.add(node.name)
  } else {
    expandedJobs.value.delete(node.name)
  }
}
const getRecentExecutions = (jobId) => {
  return executions.value[jobId] || []
}

// 防止重复请求
const loadRecentExecutions = async (jobId,loadForce=false) => {
  // 如果已有数据或正在加载，直接返回
  if (!loadForce && executions.value[jobId]) return

  try {
    // 标记为正在加载（可选）
    executions.value[jobId] = []

    const res = await axios.get(`/api/cron/jobs/${jobId}/executions`, {
      params: { limit: 50 } // 增加限制数量
    })
    executions.value[jobId] = res.data
  } catch (error) {
    console.error(`加载任务 ${jobId} 的执行记录失败:`, error)
    executions.value[jobId] = [] // 确保有默认值
  }
}


const loadJobs = async () => {
  try {
    console.log('selectedNodes.value',selectedNodes.value)
    // const params = selectedNodes.value ? {node_ids: selectedNodes.value} : {}
    // const params = selectedNodes.value.length > 0 ? { node_ids: selectedNodes.value } : {}
    const res = await axios.post('/api/cron/jobsList', { node_ids: selectedNodes.value })
    jobs.value = res.data
    // jobs.value.forEach(job => loadRecentExecutions(job.id))
    newJob.value.node_ids = selectedNodes.value
    console.log('newJob.value.node_ids',newJob.value.node_ids)

  } catch (error) {
    message.error('加载任务失败')
  }
}

const executeJob = async (job) => {
  try {
    // 1. 触发执行
    const res = await axios.post('/api/cron/jobs/execute', {
      job_ids: [job.id]
    })
    message.success(`任务 "${job.name}" 已触发执行`)
    await loadRecentExecutions(job.id,true)

    // 2. 获取执行ID（假设返回格式为 [{id: 123, ...}]）
    const executionId = res.data?.[0]?.id
    if (!executionId) return

    // 3. 开始轮询状态
    await pollExecutionStatus(executionId, job.id)

  } catch (error) {
    message.error(`执行任务失败: ${error.response?.data?.detail || error.message}`)
  }
}

// 轮询任务状态
const pollExecutionStatus = async (executionId, jobId) => {
  let attempts = 0
  const maxAttempts = 60 // 最多轮询 60 秒

  const checkStatus = async () => {
    if (attempts >= maxAttempts) {
      console.warn('轮询超时，停止检测')
      return
    }

    try {
      // 获取最新执行记录
      const res = await axios.get(`/api/cron/executions/${executionId}`)
      const status = res.data.status

      // 如果任务已完成
      if (['success', 'failed', 'cancelled'].includes(status)) {
        console.log('任务已完成，刷新历史')
        message.success(`任务 "${jobId}" 已完成。`)
        await loadRecentExecutions(jobId, true) // 强制刷新
        return
      }

      // 继续轮询
      attempts++
      setTimeout(checkStatus, 1000) // 每秒检查一次

    } catch (error) {
      console.error('轮询状态失败:', error)
      // 即使出错也继续轮询（可能是临时网络问题）
      attempts++
      setTimeout(checkStatus, 1000)
    }
  }

  // 立即开始第一次检查
  checkStatus()
}


const toggleJob = async (job) => {
  try {
    job.is_active = !job.is_active
    await axios.patch(`/api/cron/jobs/${job.id}/toggle`, {is_active: job.is_active})
    message.success(`任务 "${job.name}" 已${job.is_active ? '启用' : '停用'}`)
  } catch (error) {
    message.error('更新任务状态失败')
  }
}

// const showLog = (execution) => {
//   selectedExecution.value = execution
//   logModal.value = true
// }

const getNodeName = (nodeId) => {
  const node = nodes.value.find(n => n.id === nodeId)
  return node ? node.name : `未知节点 (#${nodeId})`
}

const formatDate = (isoString) => {
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}
const getJobTitle = (job) => {
  const nodeName = getNodeName(job.node_id)
  let title = `${nodeName}：${job.name}`

  // 显示下次执行时间
  if (job.next_run) {
    const nextRun = new Date(job.next_run)
    const formatted = nextRun.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
    title += `（下次：${formatted}）`
  } else if (!job.is_active) {
    title += '（已停用）'
  }

  return title
}

const addJob = async () => {
  try {
    await jobFormRef.value.validate()
    const res = await axios.post('/api/cron/jobs', newJob.value)
    message.success('任务添加成功')
    addJobModal.value = false
    newJob.value = {
      node_ids: [],
      name: '',
      schedule: '',
      command: '',
      description: '',
      is_active: false
    }
    loadJobs()
  } catch (error) {
    message.error(`添加任务失败: ${error.response?.data?.detail || error.message}`)
  }
}

const deleteJob = async (job) => {
  try {
    await axios.delete(`/api/cron/jobs/${job.id}`)
    message.success('任务删除成功')
    loadJobs()
  } catch (error) {
    message.error('任务节点失败')
  }
}

const stopExecution = async () => {
  if (!selectedExecution.value) return

  try {
    await axios.post(`/api/cron/executions/${selectedExecution.value.id}/stop`)
    message.info('中断请求已发送')

    // 更新本地状态（可选）
    if (selectedExecution.value) {
      selectedExecution.value.status = 'cancelled'
    }

    logModal.value = false
    await loadRecentExecutions(selectedExecution.value.job_id,true)
  } catch (error) {
    message.error('中断失败')
  }
}



const stdoutRef = ref(null)
const stderrRef = ref(null)
let ws = null

const showLog = (execution) => {
  selectedExecution.value = { ...execution }
  logModal.value = true

  // 建立 WebSocket 连接
  connectWebSocket(execution.id)
}

const connectWebSocket = (executionId) => {
  const wsUrl = `/api/cron/executions/${executionId}/logs`
  ws = new WebSocket(wsUrl)

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    // 更新日志
    if (selectedExecution.value && selectedExecution.value.id === executionId) {
      selectedExecution.value.status = data.status
      selectedExecution.value.output = data.output
      selectedExecution.value.error = data.error
      if (data.end_time) {
        selectedExecution.value.end_time = data.end_time
      }

      // 触发自动滚动
      nextTick(() => {
        scrollToBottom(stdoutRef.value)
        scrollToBottom(stderrRef.value)
      })
    }
  }

  ws.onclose = () => {
    console.log('WebSocket closed')
  }

  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
  }
}

const scrollToBottom = (element) => {
  if (element) {
    element.scrollTop = element.scrollHeight
  }
}

const closeLogModal = () => {
  logModal.value = false
  // 关闭 WebSocket
  if (ws) {
    ws.close()
    ws = null
  }
}

const getLogStatusType = (status) => {
  switch (status) {
    case 'success': return 'success'
    case 'failed': return 'error'
    case 'running': return 'info'
    case 'cancelled': return 'warning'
    default: return 'default'
  }
}
onMounted(async () => {
  await loadNodes()
  await loadJobs()
})
onUnmounted(() => {
  if (ws) {
    ws.close()
  }
})
</script>
