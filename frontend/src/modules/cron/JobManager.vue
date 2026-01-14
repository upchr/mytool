<template>
  <n-card title="⏰ 定时任务管理" class="mb-6">
    <!-- 任务筛选 -->
    <n-space justify="space-between" class="mb-4">
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
    <n-list v-else>
      <n-list-item v-for="job in jobs" :key="job.id" class="mb-2">
        <n-card :bordered="false" class="shadow-sm">
          <template #header>
            <div class="flex justify-between items-start">
              <div>
                <span class="font-bold">{{ job.name }}</span>
                <span class="ml-2 text-xs text-gray-500">({{ getNodeName(job.node_id) }})</span>
                <n-tag size="small" class="ml-2" type="info">{{ job.schedule }}</n-tag>
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
              </n-space>
            </div>
          </template>

          <n-collapse :default-expanded-names="['1', '2', '3']">
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
                            : 'warning'
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
      </n-list-item>
    </n-list>

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
    <n-modal v-model:show="logModal" preset="card" title="执行日志" style="width: 800px; max-height: 600px; overflow-y: auto">
      <n-space vertical>
        <n-text depth="3">执行 ID: {{ selectedExecution?.id }}</n-text>
        <n-text depth="3">开始时间: {{ new Date(selectedExecution?.start_time).toLocaleString() }}</n-text>
        <n-text depth="3" v-if="selectedExecution?.end_time">
          结束时间: {{ new Date(selectedExecution?.end_time).toLocaleString() }}
        </n-text>
        <n-text :type="selectedExecution?.status === 'success' ? 'success' : 'error'">
          状态: {{ selectedExecution?.status }}
        </n-text>
        <n-text type="info">触发方式: {{ selectedExecution?.triggered_by }}</n-text>

        <n-divider />

        <n-text depth="3">STDOUT:</n-text>
        <pre class="bg-gray-50 p-2 rounded text-sm overflow-x-auto">
{{ selectedExecution?.output || '无输出' }}
        </pre>

        <n-divider />

        <n-text depth="3">STDERR:</n-text>
        <pre class="bg-red-50 p-2 rounded text-sm overflow-x-auto text-red-700">
{{ selectedExecution?.error || '无错误' }}
        </pre>
      </n-space>
    </n-modal>
  </n-card>
</template>

<script setup>
import {ref, onMounted, computed} from 'vue'
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
  is_active: true
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

const showLog = (execution) => {
  selectedExecution.value = execution
  logModal.value = true
}

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
      is_active: true
    }
    loadJobs()
  } catch (error) {
    message.error(`添加任务失败: ${error.response?.data?.detail || error.message}`)
  }
}

onMounted(async () => {
  await loadNodes()
  await loadJobs()
})
</script>
