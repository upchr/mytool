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
            style="width: 200px">
          <!-- 全选插槽 -->
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
        <n-button type="primary" @click="addJobModal = true;">添加任务</n-button>
      </n-space>
    </n-space>

    <!-- 任务列表 -->
    <n-empty v-if="jobs.length === 0" description="暂无任务" />
    <n-collapse v-else @item-header-click="handleItemHeaderClick" class="jobList">
      <n-collapse-item v-for="job in jobs" :key="job.id" :title="getJobTitle(job)"  class="mb-2" :name="job.id">
        <template #header-extra>
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
                <n-button size="small" type="info" @click="openEditModal(job)">编辑</n-button> <!-- 新增 -->
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

    <!-- 添加任务模态框 -->
    <n-modal v-model:show="addJobModal" preset="card" title="添加新任务" class="mediaModal " >
      <n-form ref="jobFormRef" :model="newJob" :rules="jobRules" label-placement="left" label-width="auto">
          <n-form-item path="node_id" label="所属节点">
<!--            <n-select v-model:value="newJob.node_id" :options="nodeOptions" />-->
            <n-select
                v-model:value="newJob.node_ids"
                :options="nodeOptions.filter(opt => opt.value !== '')"
                multiple
                placeholder="请选择节点"
                max-tag-count="responsive"
            >
              <template #action>
                <n-button
                    text
                    size="small"
                    block
                    @click="toggleAllNodesAdd"
                >
                  {{ allNodesSelectedAdd ? '取消全选' : '全选' }}
                </n-button>
              </template>
            </n-select>
          </n-form-item>
          <n-form-item path="name" label="任务名称">
            <n-input v-model:value="newJob.name" placeholder="例如：每日备份" />
          </n-form-item>
          <n-form-item path="schedule" label="Cron表达式">
            <n-input v-model:value="newJob.schedule" placeholder="* * * * *【分 时 日 月 周】"
            >
              <template #suffix>
                <n-button text @click="showCronGenerator = true" style="color: grey">
                  <n-icon><CalendarOutline /></n-icon>
                  生成器
                </n-button>
              </template>
            </n-input>

            <!-- Cron 生成器 -->
            <CronGenerator
                v-model:show="showCronGenerator"
                @update:cron="newJob.schedule = $event"
                @close="showCronGenerator = false"
            />
<!--            <CronGenerator
                v-model:show="showCronGenerator"
                @update:cron="handleCronUpdate"
            />-->
          </n-form-item>
          <n-form-item path="command" label="执行命令">
            <n-input
                v-model:value="newJob.command"
                type="textarea"
                placeholder="例如: echo 'Hello World'"
                :autosize="{
                  minRows: 3,
                  maxRows: 10,
                }"
            />
          </n-form-item>
          <n-form-item path="description" label="描述">
            <n-input
                v-model:value="newJob.description"
                type="textarea"
                placeholder="任务说明"
                :autosize="{
                  minRows: 2,
                  maxRows: 5,
                }"
            />
          </n-form-item>
          <n-form-item label="启用">
            <n-switch v-model:value="newJob.is_active">
              <template #checked>
                停用
              </template>
              <template #unchecked>
                启用
              </template>
            </n-switch>
          </n-form-item>
          <n-space justify="end" class="mt-4">
            <n-button @click="addJobModal = false">取消</n-button>
            <n-button type="primary" @click="addJob">保存任务</n-button>
          </n-space>
      </n-form>
    </n-modal>
    <!-- 编辑任务模态框 -->
    <n-modal v-model:show="editJobModal" preset="card" title="编辑任务" class="mediaModal " >
      <n-form ref="editJobFormRef" :model="editingJob" :rules="jobRules" label-placement="left" label-width="auto">
        <n-form-item path="node_ids" label="所属节点">
          <n-select
              v-model:value="editingJob.node_ids"
              :options="nodeOptions.filter(opt => opt.value !== '')"
              multiple
              disabled
              placeholder="请选择节点"
              max-tag-count="responsive"
          >
            <template #action>
              <n-button
                  text
                  size="small"
                  block
                  @click="toggleAllNodesEdit"
              >
                {{ allNodesSelectedEdit ? '取消全选' : '全选' }}
              </n-button>
            </template>
          </n-select>
        </n-form-item>
        <n-form-item path="name" label="任务名称">
          <n-input v-model:value="editingJob.name" placeholder="例如：每日备份" />
        </n-form-item>
        <n-form-item path="schedule" label="Cron表达式">
          <n-input v-model:value="editingJob.schedule" placeholder="* * * * *【分 时 日 月 周】"
          >
            <template #suffix>
              <n-button text @click="showCronGenerator = true" style="color: grey">
                <n-icon><CalendarOutline /></n-icon>
                生成器
              </n-button>
            </template>
          </n-input>

          <!-- Cron 生成器 -->
          <CronGenerator
              v-model:show="showCronGenerator"
              :cron="editingJob.schedule"
              @update:cron="editingJob.schedule = $event"
              @close="showCronGenerator = false"
          />
          <!--            <CronGenerator
                          v-model:show="showCronGenerator"
                          @update:cron="handleCronUpdate"
                      />-->
        </n-form-item>
        <n-form-item path="command" label="执行命令">
          <n-input
              v-model:value="editingJob.command"
              type="textarea"
              placeholder="例如: echo 'Hello World'"
              :autosize="{
                  minRows: 3,
                  maxRows: 10,
                }"
          />
        </n-form-item>
        <n-form-item path="description" label="描述">
          <n-input
              v-model:value="editingJob.description"
              type="textarea"
              placeholder="任务说明"
              :autosize="{
                  minRows: 2,
                  maxRows: 5,
                }"
          />
        </n-form-item>
        <n-form-item label="启用">
          <n-switch v-model:value="editingJob.is_active">
            <template #checked>
              停用
            </template>
            <template #unchecked>
              启用
            </template>
          </n-switch>
        </n-form-item>
        <n-space justify="end" class="mt-4">
          <n-button @click="editJobModal = false">取消</n-button>
          <n-button type="primary" @click="updateJob">保存修改</n-button>
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
          <n-text depth="3" style="margin-left: 10px">执行ID: {{ selectedExecution?.id }}</n-text>
        </div>

        <!-- STDOUT -->
        <div>
          <n-text depth="3">STDOUT:</n-text>
          <div
              ref="stdoutRef"
              :class="stdOutClass"
          >
            {{ selectedExecution?.output || '无输出' }}
          </div>
        </div>

        <!-- STDERR -->
        <div>
          <n-text depth="3">STDERR:</n-text>
          <div
              ref="stderrRef"
              :class="stdErrClass"
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
import CronGenerator from "@/components/CronGenerator.vue";
import { CalendarOutline } from '@vicons/ionicons5'
import { useThemeStore } from '@/stores/theme'
const themeStore = useThemeStore()

const message = useMessage()
const nodes = ref([])
const jobs = ref([])
const executions = ref({})
const selectedNodes = ref([])
const selectedNodesAdd = ref([])
const addJobModal = ref(false)
const logModal = ref(false)
const selectedExecution = ref(null)
const editJobModal = ref(false)
const editingJob = ref({
  id: null,
  node_ids: [],
  name: '',
  schedule: '',
  command: '',
  description: '',
  is_active: false
})
const editJobFormRef = ref(null)
const newJob = ref({
  node_ids: [],
  name: '',
  schedule: '',
  command: '',
  description: '',
  is_active: false
})


const showCronGenerator = ref(false)
const job = ref({
  cron: '* * * * *'
})
// 处理子组件传来的 Cron 表达式。。老式处理
const handleCronUpdate = (newCron) => {
  newJob.value.schedule = newCron
}
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
      params: { limit: 25 } // 增加限制数量
    })
    executions.value[jobId] = res.data
  } catch (error) {
    console.error(`加载任务 ${jobId} 的执行记录失败:`, error)
    executions.value[jobId] = [] // 确保有默认值
  }
}


const loadJobs = async () => {
  try {
    const res = await axios.post('/api/cron/jobsList', { node_ids: selectedNodes.value })
    jobs.value = res.data
    newJob.value.node_ids = selectedNodes.value

  } catch (error) {
    message.error('加载任务失败')
  }
}

// 计算属性：是否全选
const allNodesSelected = computed(() => {
  const activeNodes = nodes.value
  return (
      activeNodes.length > 0 &&
      selectedNodes.value.length === activeNodes.length &&
      activeNodes.every(node => selectedNodes.value.includes(node.id))
  )
})

// 全选/取消全选
const toggleAllNodes = () => {
  if (allNodesSelected.value) {
    selectedNodes.value = []
  } else {
    // 只选择活跃节点
    selectedNodes.value = nodes.value
        .map(n => n.id)
  }
  loadJobs() // 立即加载
}


//add
// 计算属性：是否全选
const allNodesSelectedAdd = computed(() => {
  const activeNodes = nodes.value
  return (
      activeNodes.length > 0 &&
      selectedNodesAdd.value.length === activeNodes.length &&
      activeNodes.every(node => selectedNodesAdd.value.includes(node.id))
  )
})

// 全选/取消全选
const toggleAllNodesAdd = () => {
  if (allNodesSelectedAdd.value) {
    selectedNodesAdd.value = []
  } else {
    // 只选择活跃节点
    selectedNodesAdd.value = nodes.value
        .map(n => n.id)
  }
  newJob.value.node_ids = selectedNodesAdd.value
}

// 编辑模态框 - 全选
const allNodesSelectedEdit = computed(() => {
  const activeNodes = nodes.value
  return (
      activeNodes.length > 0 &&
      editingJob.value.node_ids.length === activeNodes.length &&
      activeNodes.every(node => editingJob.value.node_ids.includes(node.id))
  )
})

const toggleAllNodesEdit = () => {
  if (allNodesSelectedEdit.value) {
    editingJob.value.node_ids = []
  } else {
    editingJob.value.node_ids = nodes.value.map(n => n.id)
  }
}
const openEditModal = (job) => {
  // 注意：原 job.node_id 是单个 ID（旧设计），但新结构支持多节点（node_ids 数组）
  // 如果后端已改为多节点，则 job.node_ids 存在；否则需兼容
  editingJob.value = {
    id: job.id,
    node_ids: Array.isArray(job.node_ids) ? job.node_ids : [job.node_id],
    name: job.name,
    schedule: job.schedule,
    command: job.command,
    description: job.description || '',
    is_active: job.is_active || false
  }
  editJobModal.value = true
}

const updateJob = async () => {
  try {
    await editJobFormRef.value.validate()
    await axios.put(`/api/cron/jobs/${editingJob.value.id}`, editingJob.value)
    message.success('任务更新成功')
    editJobModal.value = false
    loadJobs() // 刷新列表
  } catch (error) {
    message.error(`更新任务失败: ${error.response?.data?.detail || error.message}`)
  }
}

// 立即执行
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
        if(logModal.value){
          logModal.value = false
          setTimeout(async () => {
            await showLog(res.data)
          },500)
        }

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
  if (ws) {
    ws.close()  // 立即关闭连接
    ws = null
  }
  try {
    await axios.post(`/api/cron/executions/${selectedExecution.value.id}/stop`)
    message.info('中断请求已发送，等待日志加载完成')

    await loadRecentExecutions(selectedExecution.value.job_id,true)
    showLog(selectedExecution.value)
  } catch (error) {
    message.error('中断失败')
  }
}



const stdoutRef = ref(null)
const stderrRef = ref(null)
let ws = null

const showLog = async (execution) => {
  selectedExecution.value = {...execution}
  logModal.value = true

  try {
    // 获取最新执行记录
    const res = await axios.get(`/api/cron/executions/${execution.id}`)
    const status = res.data.status
    selectedExecution.value = {...res.data}

    if('running' === status){
      // 建立 WebSocket 连接
      connectWebSocket(execution.id)
    }
  } catch (error) {
    console.error('查看日志失败:', error)
  }
}

const connectWebSocket = (executionId) => {
  const wsUrl = `/api/cron/executions/${executionId}/logs`
  selectedExecution.value.output = ''
  selectedExecution.value.error = ''

  ws = new WebSocket(wsUrl)
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    // console.log(data)
    // 更新日志
    if (selectedExecution.value && selectedExecution.value.id === executionId) {
      if (data.end_time) {
        selectedExecution.value.end_time = data.end_time
        selectedExecution.value.status = data.status
        selectedExecution.value.output = data.output
        selectedExecution.value.error = data.error
      }else{
        selectedExecution.value.output += data.output
        selectedExecution.value.error  += data.error
      }

      // 检查当前滚动位置，决定是否自动滚动到底部
      nextTick(() => {
        const isAtBottom = isScrollAtBottom(stdoutRef.value);
        // 如果用户当前已经在底部，自动滚动到底部
        if (isAtBottom) {
          scrollToBottom(stdoutRef.value);
          scrollToBottom(stderrRef.value);
        }
      });
      // 检查是否滚动到接近底部
      function isScrollAtBottom(element) {
        const margin = 100;  // 容错范围：接近底部时也算作底部
        return element.scrollHeight - element.scrollTop - element.clientHeight < margin;
      }

    // 自动滚动到底部
      function scrollToBottom(element) {
        element.scrollTop = element.scrollHeight;
      }
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

const stdOutClass = computed(() => {
  if (themeStore.theme?.name === 'dark') {
    return ['stdClass','stdOutClassM']
  } else {
    return ['stdClass','stdOutClass']
  }
})
const stdErrClass = computed(() => {
  if (themeStore.theme?.name === 'dark') {
    return ['stdClass','stdErrClassM']
  } else {
    return ['stdClass','stdErrClass']
  }
})


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
<style>
.jobList{
  height: 66vh;
  overflow-y: auto;

  .n-card__content{
    padding: 0px !important;
  }
}

.stdClass{
  height: 25vh;
  overflow-y: auto;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
  padding: 10px;
}
.stdOutClass{
  background-color: whitesmoke;
}
.stdErrClass{
  background-color: wheat;
}
.stdOutClassM{
  background-color: rgb(24, 24, 28);
}
.stdErrClassM{
  background-color: gray;
}
</style>
