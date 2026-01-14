<template>
  <n-card title="⏰ 定时任务管理" class="mb-6">
    <!-- 任务筛选 -->
    <n-space justify="space-between" class="mb-4" style="margin-bottom: 20px">
      <n-space>
        <n-select
            v-model:value="selectedNode"
            :options="nodeOptions"
            placeholder="选择节点"
            @update:value="loadJobs"
            style="width: 200px"
        />
        <n-button type="primary" @click="addJobModal = true;">添加任务</n-button>
      </n-space>
    </n-space>

    <!-- 任务列表 -->
    <n-empty v-if="jobs.length === 0" description="暂无任务" />
    <n-collapse v-else>
      <n-collapse-item v-for="job in jobs" :key="job.id" :title="getNodeName(job.node_id)+'：'+job.name"  class="mb-2">
        <n-card :bordered="false" class="shadow-sm">
          <template #header>
            <div class="flex justify-between items-start">
              <div style="margin-bottom: 10px">
                <span class="ml-2 text-xs text-gray-500">{{ getNodeName(job.node_id) }}：</span>
                <span class="font-bold">{{ job.name }}</span>
                <n-tag size="small" class="ml-2" type="info" style="margin-left: 10px">{{ job.schedule }}</n-tag>
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
            </n-collapse-item>
          </n-collapse>
        </n-card>
      </n-collapse-item>
    </n-collapse>

    <!-- 添加任务模态框 -->
    <n-modal v-model:show="addJobModal" preset="card" title="添加新任务" style="width: 600px">
      <n-form ref="jobFormRef" :model="newJob" :rules="jobRules" label-placement="left" label-width="auto">
          <n-form-item path="node_id" label="所属节点">
            <n-select v-model:value="newJob.node_id" :options="nodeOptions" />
          </n-form-item>
          <n-form-item path="name" label="任务名称">
            <n-input v-model:value="newJob.name" placeholder="例如：每日备份" />
          </n-form-item>
          <n-form-item path="schedule" label="Cron表达式">
            <n-input v-model:value="newJob.schedule" placeholder="* * * * *" />
            <template #footer>
              <n-text depth="3" class="text-xs">分 时 日 月 周 (例如: 0 2 * * * 表示每天凌晨2点)</n-text>
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
const selectedNode = ref('')
const addJobModal = ref(false)
const logModal = ref(false)
const selectedExecution = ref(null)

const newJob = ref({
  node_id: '',
  name: '',
  schedule: '',
  command: '',
  description: '',
  is_active: false
})

const jobFormRef = ref(null)

const jobRules = {
  // node_id: {required: true, message: '请选择节点', trigger: ['blur']},
  name: {required: true, message: '请输入任务名称', trigger: ['blur']},
  schedule: {required: true, message: '请输入Cron表达式', trigger: ['blur']},
  command: {required: true, message: '请输入执行命令', trigger: ['blur']}
}

const nodeOptions = computed(() => [
  {label: '所有节点', value: ''},
  ...nodes.value.map(node => ({
    label: `${node.name} (${node.host})`,
    value: node.id
  }))
])

const loadNodes = async () => {
  try {
    const res = await axios.get('/api/cron/nodes')
    nodes.value = res.data
  } catch (error) {
    message.error('加载节点失败')
  }
}

const loadJobs = async () => {
  try {
    console.log('selectedNode.value',selectedNode.value)
    const params = selectedNode.value ? {node_id: selectedNode.value} : {}
    const res = await axios.get('/api/cron/jobs', {params})
    jobs.value = res.data
    jobs.value.forEach(job => loadRecentExecutions(job.id))
    newJob.value.node_id = selectedNode.value
  } catch (error) {
    message.error('加载任务失败')
  }
}

const loadRecentExecutions = async (jobId) => {
  try {
    const res = await axios.get(`/api/cron/jobs/${jobId}/executions`, {
      params: {limit: 5}
    })
    executions.value[jobId] = res.data
  } catch (error) {
    console.error(`加载任务 ${jobId} 的执行记录失败:`, error)
  }
}

const executeJob = async (job) => {
  try {
    await axios.post('/api/cron/jobs/execute', {
      job_ids: [job.id]
    })
    message.success(`任务 "${job.name}" 已触发执行`)
    loadRecentExecutions(job.id)
  } catch (error) {
    message.error(`执行任务失败: ${error.response?.data?.detail || error.message}`)
  }
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

const getRecentExecutions = (jobId) => {
  return executions.value[jobId] || []
}

const addJob = async () => {
  try {
    await jobFormRef.value.validate()
    const res = await axios.post('/api/cron/jobs', newJob.value)
    message.success('任务添加成功')
    addJobModal.value = false
    newJob.value = {
      node_id: '',
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
    await loadJobs()
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
