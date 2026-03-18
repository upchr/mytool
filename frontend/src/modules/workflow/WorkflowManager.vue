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
              </n-space>
            </template>
            <template #header-extra>
              <n-space>
                <n-button size="small" type="primary" @click="handleEdit(wf)">编辑</n-button>
                <n-button size="small" @click="handleTrigger(wf)">执行</n-button>
                <n-button size="small" type="error" @click="handleDelete(wf)">删除</n-button>
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
      :initial-data="{ nodes: current?.nodes || [], edges: current?.edges || [] }"
      @save="onSave"
      @trigger="onTrigger"
      @back="showEditor = false"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import WorkflowEditor from './WorkflowEditor.vue'

const loading = ref(false)
const list = ref([])
const showEditor = ref(false)
const editorRef = ref(null)
const current = ref(null)

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
  showEditor.value = true
}

const handleEdit = (wf) => {
  current.value = wf
  showEditor.value = true
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
  await window.$request.post('/workflows/trigger', { workflow_id: wf.workflow_id })
  window.$message.success('已触发')
}

const onSave = async (data) => {
  try {
    const payload = {
      workflow_id: current.value.workflow_id || `wf-${Date.now()}`,
      name: current.value.name || '新工作流',
      description: current.value.description || '',
      node_id: 1,
      is_active: true,
      ...data
    }
    if (current.value.workflow_id) {
      await window.$request.put(`/workflows/${current.value.workflow_id}`, payload)
    } else {
      await window.$request.post('/workflows', payload)
    }
    window.$message.success('保存成功')
    showEditor.value = false
    loadList()
  } catch (e) {
    window.$message.error('保存失败')
  }
}

const onTrigger = () => {
  if (current.value.workflow_id) {
    window.$request.post('/workflows/trigger', { workflow_id: current.value.workflow_id })
    window.$message.success('已触发')
  }
}

onMounted(() => loadList())
</script>

<style scoped>
.workflow-page { height: 100%; }
</style>
