<!-- src/modules/cron/JobManager.vue -->
<template>
  <n-card title="⏰ 定时任务" class="mb-6">
    <!-- 任务筛选 -->
    <n-space justify="space-between" class="mb-4" style="margin-bottom: 20px">
      <n-space>
        <n-select
            v-model:value="selectedNodes"
            :options="nodeOptions"
            placeholder="选择节点"
            @update:value="loadJobs"
            multiple
            max-tag-count="responsive"
            style="width: 200px"
        >
          <template #action>
            <n-button
                text
                size="small"
                block
                @click="toggleAllNodes"
            >
              {{ allNodesSelected ? '取消全选' : '全选' }}
            </n-button>
          </template>
        </n-select>
        <n-button type="primary" @click="showAddModal = true">添加任务</n-button>
      </n-space>
    </n-space>

    <!-- 任务列表 -->
    <n-empty v-if="jobs.length === 0" description="暂无任务" />
    <n-collapse v-else @item-header-click="handleItemHeaderClick" class="jobList">
      <n-collapse-item
          v-for="job in jobs"
          :key="job.id"
          :title="getJobTitle(job)"
          class="mb-2"
          :name="job.id"
      >
        <template #header-extra>
          <n-tag
              v-if="job.next_run"
              size="small"
              type="success"
              class="ml-2"
          >
            下次：{{ formatDate(job.next_run) }}
          </n-tag>
          <n-tag
              v-else-if="!job.is_active"
              size="small"
              type="warning"
              class="ml-2"
          >
            已停用
          </n-tag>
        </template>
        <n-card hoverable :bordered="false" class="shadow-sm" size="small">
          <template #header>
            <div class="flex justify-between items-start">
              <div style="margin-bottom: 10px;">
                <span class="font-bold">{{ job.name }}</span>
                <n-tag size="small" class="ml-2" type="info" style="margin-left: 10px;margin-right: 10px">{{ job.schedule }}</n-tag>
              </div>
              <n-space>
                <n-button
                    size="small"
                    :type="job.is_active ? 'success' : 'warning'"
                    @click="toggleJob(job)"
                >
                  {{ job.is_active ? '停用' : '启用' }}
                </n-button>
                <n-button size="small" type="primary" @click="executeJob(job)">执行</n-button>
                <n-button size="small" type="info" @click="openEditModal(job)">编辑</n-button>
                <n-popconfirm @positive-click="deleteJob(job)">
                  <template #trigger>
                    <n-button size="small" type="error">删除</n-button>
                  </template>
                  确定要删除任务 "{{ job.name }}" 吗？
                </n-popconfirm>
              </n-space>
            </div>
          </template>

          <n-collapse :default-expanded-names="['3']" style="margin-bottom: 10px">
            <n-collapse-item title="命令详情" name="1">
              <div style="overflow: auto">
                <n-code :code="job.command" language="shell" show-line-numbers/>
              </div>
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

    <!-- 新增/编辑模态框 -->
    <JobFormModal
        v-model:visible="showAddModal"
        :nodes="nodes"
        :job-data="{}"
        :is-edit="false"
        @submit="addJob"
        @cancel="showAddModal = false"
    />

    <JobFormModal
        v-model:visible="showEditModal"
        :nodes="nodes"
        :job-data="editingJob"
        :is-edit="true"
        @submit="updateJob"
        @cancel="showEditModal = false"
    />

    <!-- 日志模态框 -->
    <JobLogModal
        v-model:visible="showLogModal"
        :execution="selectedExecution"
        @update-execution="updateExecution"
        @update-log="updateLog"
        @close="closeLogModal"
        :on-stop-execution="stopExecution"
    />
  </n-card>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick, watch } from 'vue'
import { useThemeStore } from '@/stores/theme'
import { getAuthToken } from '@/utils/auth'
import JobFormModal from '@/modules/cron/JobFormModal.vue'
import JobLogModal from '@/modules/cron/JobLogModal.vue'

const themeStore = useThemeStore()

// 状态管理
const nodes = ref([])
const jobs = ref([])
const executions = ref({})
const selectedNodes = ref([])
const showAddModal = ref(false)
const showLogModal = ref(false)
const showEditModal = ref(false)
const selectedExecution = ref(null)
const editingJob = ref({
  id: null,
  node_ids: [],
  name: '',
  schedule: '',
  command: '',
  description: '',
  is_active: false
})

// Cron 表达式正则
const CRON_REGEX = /^(\*|(\*\/\d{1,2})|(\d{1,2})(-\d{1,2})?(\/\d{1,2})?)(,(\*|(\*\/\d{1,2})|(\d{1,2})(-\d{1,2})?(\/\d{1,2})?))*\s+(\*|(\*\/\d{1,2})|([01]?\d|2[0-3])(-([01]?\d|2[0-3]))?(\/\d{1,2})?)(,(\*|(\*\/\d{1,2})|([01]?\d|2[0-3])(-([01]?\d|2[0-3]))?(\/\d{1,2})?))*\s+(\*|(\*\/\d{1,2})|([1-9]|[12]\d|3[01])(-([1-9]|[12]\d|3[01]))?(\/\d{1,2})?)(,(\*|(\*\/\d{1,2})|([1-9]|[12]\d|3[01])(-([1-9]|[12]\d|3[01]))?(\/\d{1,2})?))*\s+(\*|(\*\/\d{1,2})|(1[0-2]|[1-9])(-(1[0-2]|[1-9]))?(\/\d{1,2})?)(,(\*|(\*\/\d{1,2})|(1[0-2]|[1-9])(-(1[0-2]|[1-9]))?(\/\d{1,2})?))*\s+(\*|(\*\/\d{1,2})|[0-6](-[0-6])?(\/\d{1,2})?)(,(\*|(\*\/\d{1,2})|[0-6](-[0-6])?(\/\d{1,2})?))*$/;

// 节点选项
const nodeOptions = computed(() => [
  ...nodes.value.map(node => ({
    label: `${node.name} (${node.host})`,
    value: node.id
  }))
])

// 全选逻辑
const allNodesSelected = computed(() => {
  const activeNodes = nodes.value
  return (
      activeNodes.length > 0 &&
      selectedNodes.value.length === activeNodes.length &&
      activeNodes.every(node => selectedNodes.value.includes(node.id))
  )
})

const toggleAllNodes = () => {
  if (allNodesSelected.value) {
    selectedNodes.value = []
  } else {
    selectedNodes.value = nodes.value.map(n => n.id)
  }
  loadJobs()
}

// 展开任务管理
const expandedJobs = ref(new Set())
const handleItemHeaderClick = (node) => {
  if (node.expanded && !executions.value[node.name]) {
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

const loadRecentExecutions = async (jobId, loadForce = false) => {
  if (!loadForce && executions.value[jobId]) return

  try {
    executions.value[jobId] = []
    const res = await window.$request.get(`/cron/jobs/${jobId}/executions`, {
      params: { limit: 25 }
    })
    executions.value[jobId] = res
  } catch (error) {
    console.error(`加载任务 ${jobId} 的执行记录失败:`, error)
    executions.value[jobId] = []
  }
}

// 数据加载
const loadNodes = async () => {
  try {
    const res = await window.$request.get('/nodes/only_active/true')
    nodes.value = res
  } catch (error) {
    window.$message.error('加载节点失败')
  }
}

const loadJobs = async () => {
  try {
    const res = await window.$request.post('/cron/jobsList', { node_ids: selectedNodes.value })
    jobs.value = res
  } catch (error) {
    window.$message.error('加载任务失败')
  }
}

// 任务操作
const openEditModal = (job) => {
  debugger
  editingJob.value = {
    id: job.id,
    node_ids: Array.isArray(job.node_ids) ? job.node_ids : [job.node_id],
    name: job.name,
    schedule: job.schedule,
    command: job.command,
    description: job.description || '',
    is_active: job.is_active || false
  }
  showEditModal.value = true
}

const addJob = async (jobData) => {
  try {
    await window.$request.post('/cron/jobs', jobData)
    window.$message.success('任务添加成功')
    showAddModal.value = false
    loadJobs()
  } catch (error) {
    window.$message.error('添加任务失败')
  }
}

const updateJob = async (jobData) => {
  try {
    await window.$request.put(`/cron/jobs/${jobData.id}`, jobData)
    window.$message.success('任务更新成功')
    showEditModal.value = false
    loadJobs()
  } catch (error) {
    window.$message.error('更新任务失败')
  }
}

const deleteJob = async (job) => {
  try {
    await window.$request.delete(`/cron/jobs/${job.id}`)
    window.$message.success('任务删除成功')
    loadJobs()
  } catch (error) {
    window.$message.error('删除任务失败')
  }
}

const toggleJob = async (job) => {
  try {
    job.is_active = !job.is_active
    await window.$request.patch(`/cron/jobs/${job.id}/toggle`, { is_active: job.is_active })
    window.$message.success(`任务 "${job.name}" 已${job.is_active ? '启用' : '停用'}`)
  } catch (error) {
    window.$message.error('更新任务状态失败')
  }
}

// 执行任务
const executeJob = async (job) => {
  try {
    const res = await window.$request.post('/cron/jobs/execute', {
      job_ids: [job.id]
    })
    window.$message.success(`任务 "${job.name}" 已触发执行`)
    await loadRecentExecutions(job.id, true)

    const executionId = res?.[0]?.id
    if (!executionId) return

    await pollExecutionStatus(executionId, job.id, job.name)
  } catch (error) {
    window.$message.error('执行任务失败')
  }
}

const pollExecutionStatus = async (executionId, jobId, jobName) => {
  let attempts = 0
  const maxAttempts = 60

  const checkStatus = async () => {
    if (attempts >= maxAttempts) {
      console.warn('轮询超时，停止检测')
      return
    }

    try {
      const res = await window.$request.get(`/cron/executions/${executionId}`)
      const status = res.status

      if (['success', 'failed', 'cancelled'].includes(status)) {
        if (showLogModal.value) {
          showLogModal.value = false
          setTimeout(async () => {
            await showLog(res)
          }, 500)
        }
        window.$message.success(`任务 "${jobId}-${jobName}" 已完成。`)
        await loadRecentExecutions(jobId, true)
        return
      }

      attempts++
      setTimeout(checkStatus, 1000)
    } catch (error) {
      console.error('轮询状态失败:', error)
      attempts++
      setTimeout(checkStatus, 1000)
    }
  }

  checkStatus()
}

// 日志相关
const showLog = async (execution) => {
  try {
    const res = await window.$request.get(`/cron/executions/${execution.id}`)
    selectedExecution.value = { ...res }
    showLogModal.value = true
  } catch (error) {
    console.error('查看日志失败:', error)
  }
}

const updateExecution = (data) => {
  selectedExecution.value = { ...selectedExecution.value, ...data }
}

const updateLog = ({ output, error }) => {
  if (selectedExecution.value) {
    selectedExecution.value.output += output
    selectedExecution.value.error += error
  }
}

const stopExecution = async (execution) => {
  try {
    await window.$request.post(`/cron/executions/${execution.id}/stop`)
    window.$message.info('中断请求已发送，等待日志加载完成')
    await loadRecentExecutions(execution.job_id, true)
    // 刷新当前日志
    const res = await window.$request.get(`/cron/executions/${execution.id}`)
    selectedExecution.value = { ...res }
  } catch (error) {
    window.$message.error('中断失败')
  }
}

const closeLogModal = () => {
  showLogModal.value = false
}

// 辅助方法
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
  return title
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

// 生命周期
onMounted(async () => {
  await loadNodes()
  await loadJobs()
})

onUnmounted(() => {
  // WebSocket 清理在 JobLogModal 中处理
})
</script>

<style>
.jobList {
  height: 66vh;
  overflow-y: auto;
}

.jobList .n-card__content {
  padding: 0px !important;
}
</style>
