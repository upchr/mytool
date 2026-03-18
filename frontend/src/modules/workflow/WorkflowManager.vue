<template>
  <div class="workflow-page">
    <!-- 列表视图 -->
    <div v-if="!showEditor" class="list-view">
      <n-card>
        <template #header>
          <n-space justify="space-between" align="center">
            <n-space align="center">
              <n-text strong style="font-size: 18px">🔄 工作流管理</n-text>
              <n-tag type="info" size="small">可视化任务编排</n-tag>
            </n-space>
            <n-space>
              <n-button type="primary" @click="handleCreate">
                <template #icon><n-icon><AddOutline /></n-icon></template>
                新建工作流
              </n-button>
            </n-space>
          </n-space>
        </template>

        <n-alert type="info" style="margin-bottom: 16px">
          <template #header>💡 什么是工作流？</template>
          工作流可以将多个任务按顺序、条件、并行等方式串联执行。支持可视化拖拽编辑！
          <br>
          <n-text strong>节点类型：</n-text>
          ⚙️ 任务（执行定时任务） → 🔷 条件（条件分支） → ⏱️ 等待 → 📢 通知
        </n-alert>

        <n-space style="margin-bottom: 16px">
          <n-input v-model:value="searchKeyword" placeholder="搜索" clearable style="width: 200px" @keyup.enter="loadWorkflows" />
          <n-button @click="loadWorkflows">搜索</n-button>
        </n-space>

        <n-empty v-if="!loading && data.length === 0" description="暂无工作流">
          <template #extra>
            <n-button type="primary" @click="handleCreate">新建工作流</n-button>
          </template>
        </n-empty>

        <n-list v-else bordered>
          <n-list-item v-for="wf in data" :key="wf.id">
            <n-thing>
              <template #header>
                <n-space align="center">
                  <n-text strong>{{ wf.name }}</n-text>
                  <n-tag :type="wf.is_active ? 'success' : 'default'" size="small">{{ wf.is_active ? '启用' : '禁用' }}</n-tag>
                  <n-tag v-if="wf.schedule" type="info" size="small">⏰ {{ wf.schedule }}</n-tag>
                </n-space>
              </template>
              <template #header-extra>
                <n-space>
                  <n-button size="small" type="primary" @click="handleEdit(wf)">
                    <template #icon><n-icon><CreateOutline /></n-icon></template>
                    编辑
                  </n-button>
                  <n-button size="small" @click="handleTrigger(wf)">执行</n-button>
                  <n-button size="small" @click="showExecutions(wf)">记录</n-button>
                  <n-button size="small" @click="showVersions(wf)">版本</n-button>
                  <n-button size="small" type="error" @click="handleDelete(wf)">删除</n-button>
                </n-space>
              </template>
              <template #description>
                <n-text depth="3">{{ wf.description || '暂无描述' }}</n-text>
                <br>
                <n-text depth="3" style="font-size: 12px">
                  ID: {{ wf.workflow_id }} · 节点: {{ wf.nodes?.length || 0 }} 个
                </n-text>
              </template>
            </n-thing>
          </n-list-item>
        </n-list>

        <n-space v-if="data.length > 0" justify="center" style="margin-top: 16px">
          <n-pagination v-model:page="pagination.page" :page-count="Math.ceil(pagination.itemCount / pagination.pageSize)" @update:page="loadWorkflows" />
        </n-space>
      </n-card>
    </div>

    <!-- 编辑器视图 -->
    <div v-else class="editor-view">
      <WorkflowEditor
        ref="editorRef"
        :workflow-id="currentWorkflow?.workflow_id"
        :initial-data="{ nodes: currentWorkflow?.nodes || [], edges: currentWorkflow?.edges || [] }"
        @save="handleSave"
        @trigger="handleTriggerSave"
      />
      <div class="editor-back">
        <n-button @click="showEditor = false">
          <template #icon><n-icon><ArrowBackOutline /></n-icon></template>
          返回列表
        </n-button>
      </div>
    </div>

    <!-- 执行记录抽屉 -->
    <n-drawer v-model:show="showExecDrawer" width="600px">
      <n-drawer-content title="执行记录">
        <n-button size="small" @click="loadExecutions" style="margin-bottom: 12px">刷新</n-button>
        <n-empty v-if="executions.length === 0" description="暂无执行记录" />
        <n-list v-else bordered>
          <n-list-item v-for="exec in executions" :key="exec.id">
            <n-thing>
              <template #header>
                <n-tag :type="statusType(exec.status)" size="small">{{ exec.status }}</n-tag>
              </template>
              <template #description>
                <n-text depth="3">{{ exec.start_time }}</n-text>
              </template>
            </n-thing>
          </n-list-item>
        </n-list>
      </n-drawer-content>
    </n-drawer>

    <!-- 版本管理抽屉 -->
    <n-drawer v-model:show="showVerDrawer" width="500px">
      <n-drawer-content title="版本管理">
        <n-button type="primary" size="small" @click="createVersion" style="margin-bottom: 12px">保存当前版本</n-button>
        <n-empty v-if="versions.length === 0" description="暂无版本" />
        <n-list v-else bordered>
          <n-list-item v-for="ver in versions" :key="ver.id">
            <n-thing>
              <template #header>
                <n-tag type="info" size="small">v{{ ver.version }}</n-tag>
                {{ ver.change_note || '无说明' }}
              </template>
              <template #header-extra>
                <n-button size="small" type="warning" @click="restoreVersion(ver.id)">恢复</n-button>
              </template>
            </n-thing>
          </n-list-item>
        </n-list>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup>
import { onMounted, ref, reactive } from 'vue'
import { AddOutline, CreateOutline, ArrowBackOutline } from '@vicons/ionicons5'
import WorkflowEditor from './WorkflowEditor.vue'

const loading = ref(false)
const data = ref([])
const searchKeyword = ref('')
const showEditor = ref(false)
const editorRef = ref(null)
const currentWorkflow = ref(null)

const showExecDrawer = ref(false)
const executions = ref([])
const currentWfId = ref('')

const showVerDrawer = ref(false)
const versions = ref([])

const pagination = reactive({ page: 1, pageSize: 10, itemCount: 0 })

const statusType = (status) => {
  const map = { success: 'success', failed: 'error', running: 'warning' }
  return map[status] || 'default'
}

onMounted(() => { loadWorkflows() })

const loadWorkflows = async () => {
  loading.value = true
  try {
    const result = await window.$request.get('/workflows', {
      params: { page: pagination.page, page_size: pagination.pageSize, keyword: searchKeyword.value }
    })
    data.value = result.items || []
    pagination.itemCount = result.total || 0
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  currentWorkflow.value = { workflow_id: '', name: '', nodes: [], edges: [] }
  showEditor.value = true
}

const handleEdit = (wf) => {
  currentWorkflow.value = wf
  showEditor.value = true
}

const handleDelete = (wf) => {
  window.$dialog.warning({
    title: '确认删除',
    content: `删除 "${wf.name}"？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      await window.$request.delete(`/workflows/${wf.workflow_id}`)
      window.$message.success('已删除')
      loadWorkflows()
    }
  })
}

const handleTrigger = async (wf) => {
  try {
    await window.$request.post('/workflows/trigger', { workflow_id: wf.workflow_id })
    window.$message.success('已触发执行')
  } catch (e) {}
}

const handleSave = async (workflowData) => {
  try {
    const payload = {
      workflow_id: currentWorkflow.value.workflow_id || `wf-${Date.now()}`,
      name: currentWorkflow.value.name || '新工作流',
      description: currentWorkflow.value.description || '',
      node_id: currentWorkflow.value.node_id || 1,
      schedule: currentWorkflow.value.schedule || '',
      is_active: currentWorkflow.value.is_active ?? true,
      ...workflowData
    }
    
    if (currentWorkflow.value.workflow_id) {
      await window.$request.put(`/workflows/${currentWorkflow.value.workflow_id}`, payload)
    } else {
      await window.$request.post('/workflows', payload)
    }
    
    window.$message.success('保存成功')
    showEditor.value = false
    loadWorkflows()
  } catch (e) {}
}

const handleTriggerSave = async () => {
  if (currentWorkflow.value.workflow_id) {
    await window.$request.post('/workflows/trigger', { workflow_id: currentWorkflow.value.workflow_id })
    window.$message.success('已触发执行')
  }
}

const showExecutions = async (wf) => {
  currentWfId.value = wf.workflow_id
  showExecDrawer.value = true
  loadExecutions()
}

const loadExecutions = async () => {
  try {
    const result = await window.$request.get(`/workflows/${currentWfId.value}/executions`)
    executions.value = result || []
  } catch (e) {}
}

const showVersions = async (wf) => {
  currentWfId.value = wf.workflow_id
  showVerDrawer.value = true
  loadVersions()
}

const loadVersions = async () => {
  try {
    const result = await window.$request.get(`/workflows/${currentWfId.value}/versions`)
    versions.value = result || []
  } catch (e) {}
}

const createVersion = async () => {
  try {
    await window.$request.post(`/workflows/${currentWfId.value}/versions`)
    window.$message.success('版本已保存')
    loadVersions()
  } catch (e) {}
}

const restoreVersion = async (versionId) => {
  window.$dialog.warning({
    title: '确认恢复',
    content: '恢复到此版本？当前状态会先保存。',
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      await window.$request.post(`/workflows/${currentWfId.value}/versions/restore`, { version_id: versionId })
      window.$message.success('已恢复')
      loadVersions()
      loadWorkflows()
    }
  })
}
</script>

<style scoped>
.workflow-page {
  height: 100%;
}

.list-view, .editor-view {
  height: 100%;
}

.editor-view {
  position: relative;
}

.editor-back {
  position: absolute;
  top: 16px;
  left: 250px;
  z-index: 10;
}
</style>
