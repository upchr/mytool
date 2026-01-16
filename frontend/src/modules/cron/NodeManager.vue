<template>
  <n-card title="🖥️ 节点管理" class="mb-6">
    <!-- 添加节点表单 -->
    <n-form ref="formRef" :model="newNode" :rules="rules" label-placement="left" :label-width="100">
      <n-grid cols="1 s:2" responsive="screen">
        <n-grid-item>
          <n-form-item path="name" label="节点名称">
            <n-input v-model:value="newNode.name" placeholder="例如：生产服务器" />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item path="host" label="主机地址">
            <n-input v-model:value="newNode.host" placeholder="IP 或域名" />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item path="port" label="SSH端口">
            <n-input-number v-model:value="newNode.port" :min="1" :max="65535" />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item path="username" label="用户名">
            <n-input v-model:value="newNode.username" placeholder="root / admin" />
          </n-form-item>
        </n-grid-item>
        <n-grid-item cols="1 600:2">
          <n-form-item path="auth_type" label="认证方式">
            <n-radio-group v-model:value="newNode.auth_type">
              <n-space>
                <n-radio value="password">密码认证</n-radio>
                <n-radio value="ssh_key">SSH密钥</n-radio>
              </n-space>
            </n-radio-group>
          </n-form-item>
        </n-grid-item>
        <n-grid-item v-if="newNode.auth_type === 'password'">
          <n-form-item path="password" label="密码">
            <n-input
                type="password"
                show-password-on="mousedown"
                placeholder="密码"
                v-model:value="newNode.password"
                :maxlength="8"
            />
          </n-form-item>
        </n-grid-item>
        <n-grid-item v-else>
          <n-form-item path="private_key" label="私钥">
            <n-input
                v-model:value="newNode.private_key"
                type="textarea"
                placeholder="粘贴私钥内容（PEM格式）"
                rows="4"
            />
          </n-form-item>
        </n-grid-item>
      </n-grid>
      <n-space justify="end" class="mt-4">
        <n-button type="primary" @click="addNode">添加节点</n-button>
      </n-space>
    </n-form>
    <n-space justify="end" class="mt-4" style="margin-top: 10px">
      <n-button v-if="!isBatchMode" @click="enterBatchMode">批量操作</n-button>
      <div v-if="isBatchMode" class="mb-4 flex justify-between items-center bg-gray-50 p-3 rounded">
        <n-space justify="end" >已选择 {{ selectedNodeIds.length }} 个节点</n-space>
        <n-space>
          <n-button  size="small" type="info" @click="toggleAllNodesAdd"
          >
            {{ allNodesSelectedAdd ? '取消全选' : '全选' }}
          </n-button>
          <n-popconfirm
              @positive-click="batchDeleteNodes"
              negative-text="取消"
              positive-text="确定删除"
          >
            <template #trigger>
              <n-button size="small" type="error">批量删除</n-button>
            </template>
            确定要删除选中的 {{ selectedNodeIds.length }} 个节点吗？
          </n-popconfirm>
          <n-button size="small" @click="cancelBatch">取消</n-button>
        </n-space>
      </div>
    </n-space>


    <!-- 节点列表 -->
    <n-divider />
    <div v-if="nodes.length === 0" class="text-center text-gray-500 py-8">
      暂无节点，点击上方按钮添加
    </div>
    <n-list v-else  style="height: 51vh;overflow-y: auto;">
      <n-list-item v-for="node in nodes" :key="node.id">
        <n-card :title="node.name" :bordered="false" class="shadow-sm"
                :style="isBatchMode && selectedNodeIds.includes(node.id) ? { backgroundColor: 'lightgray'}: {backgroundColor: 'whitesmoke'}"
                @click="handleCardClick(node)">
          <template #header-extra>
            <n-space>
              <n-checkbox
                  v-if="isBatchMode"
                  :checked="selectedNodeIds.includes(node.id)"
                  @click.stop.prevent="(e) => toggleNodeSelection(node.id, !selectedNodeIds.includes(node.id))"
              />
              <n-space v-else>
                <n-button size="small" @click="testConnection(node)">⚡️</n-button>
                <n-button
                    size="small"
                    :type="node.is_active ? 'success' : 'warning'"
                    @click="toggleNode(node)"
                >
                  {{ node.is_active ? '停用' : '启用' }}
                </n-button>
                <n-popconfirm @positive-click="deleteNode(node)">
                  <template #trigger>
                    <n-button size="small" type="error">删除</n-button>
                  </template>
                  确定要删除节点 "{{ node.name }}" 吗？
                </n-popconfirm>
              </n-space>

            </n-space>
          </template>

          <n-descriptions :column="1" label-placement="left" size="small">
            <n-descriptions-item label="主机">
              {{ node.host }}:{{ node.port }}
            </n-descriptions-item>
            <n-descriptions-item label="用户">
              {{ node.username }}
            </n-descriptions-item>
            <n-descriptions-item label="认证">
              {{ node.auth_type === 'password' ? '密码' : 'SSH密钥' }}
            </n-descriptions-item>
            <n-descriptions-item label="状态">
              <n-tag :type="node.is_active ? 'success' : 'default'">
                {{ node.is_active ? '启用' : '停用' }}
              </n-tag>
            </n-descriptions-item>
          </n-descriptions>
        </n-card>
      </n-list-item>
    </n-list>
  </n-card>
</template>

<script setup>
import {ref, onMounted, computed} from 'vue'
import axios from 'axios'
import { useMessage } from 'naive-ui'

const message = useMessage()
const nodes = ref([])
const newNode = ref({
  name: '',
  host: '',
  port: 22,
  username: '',
  auth_type: 'password',
  password: '',
  private_key: '',
  is_active: true
})

// 表单验证规则
const rules = {
  name: { required: true, message: '请输入节点名称', trigger: ['blur'] },
  host: { required: true, message: '请输入主机地址', trigger: ['blur'] ,pattern: /^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+(?:[a-zA-Z]{2,})$|^(?:\d{1,3}\.){3}\d{1,3}$/},
  username: { required: true, message: '请输入用户名', trigger: ['blur'],min: 3,max: 20,},
  password: ({ value }) => {
    if (newNode.value.auth_type === 'password' && !value) {
      return '请输入密码'
    }
    return true
  },
  private_key: ({ value }) => {
    if (newNode.value.auth_type === 'ssh_key' && !value) {
      return '请粘贴私钥'
    }
    return true
  }
}

const formRef = ref(null)

const loadNodes = async () => {
  try {
    const res = await axios.get('/api/cron/nodes/false')
    nodes.value = res.data
  } catch (error) {
    message.error('加载节点失败')
  }
}

const addNode = async () => {
  try {
    await formRef.value.validate()
    const res = await axios.post('/api/cron/nodes', newNode.value)
    message.success('节点添加成功')
    newNode.value = {
      name: '',
      host: '',
      port: 22,
      username: '',
      auth_type: 'password',
      password: '',
      private_key: '',
      is_active: true
    }
    loadNodes()
  } catch (error) {
    message.error('添加节点失败: ' + (error.response?.data?.detail || error.message))
  }
}

const testConnection = async (node) => {
  try {
    message.info(`正在测试 ${node.name} 的连接...`)
    // 👇 调用后端真实 SSH 测试接口（需后端实现）
    const res = await axios.post(`/api/cron/nodes/${node.id}/test`)
    if (res.data.success) {
      message.success(`✅ ${node.name} 连接成功！`)
    } else {
      message.error(`❌ ${node.name} 连接失败: ${res.data.message}`)
    }
  } catch (error) {
    message.error(`连接失败: ${error.response?.data?.detail || error.message}`)
  }
}

const toggleNode = async (node) => {
  try {
    node.is_active = !node.is_active
    // 👇 调用后端更新接口（需后端实现）
    await axios.patch(`/api/cron/nodes/${node.id}/toggle`, { is_active: node.is_active })
    message.success(`节点 ${node.name} 已${node.is_active ? '启用' : '停用'}`)
  } catch (error) {
    message.error('操作失败')
  }
}

const deleteNode = async (node) => {
  try {
    await axios.delete(`/api/cron/nodes/${node.id}`)
    message.success('节点删除成功')
    loadNodes()
  } catch (error) {
    message.error('删除节点失败')
  }
}

//批量删除
const selectedNodeIds = ref([]) // 批量选择的节点ID
const isBatchMode = ref(false)  // 批量模式开关
// 批量操作方法
const enterBatchMode = () => {
  isBatchMode.value = true
  selectedNodeIds.value = []
}

const cancelBatch = () => {
  isBatchMode.value = false
  selectedNodeIds.value = []
}

const toggleNodeSelection = (nodeId, checked) => {
  if (checked) {
    selectedNodeIds.value.push(nodeId)
  } else {
    selectedNodeIds.value = selectedNodeIds.value.filter(id => id !== nodeId)
  }
}

const batchDeleteNodes = async () => {
  if (selectedNodeIds.value.length === 0) return

  try {
    await axios.post('/api/cron/nodes/deleteBatch', { node_ids: selectedNodeIds.value })
    message.success(`成功删除 ${selectedNodeIds.value.length} 个节点`)
    cancelBatch()
    loadNodes()
  } catch (error) {
    message.error('批量删除失败')
  }
}
// 处理卡片点击（仅在批量模式下生效）
const handleCardClick = (node) => {
  if (!isBatchMode.value) return

  const isChecked = selectedNodeIds.value.includes(node.id)
  toggleNodeSelection(node.id, !isChecked)
}

const allNodesSelectedAdd = computed(() => {
  const activeNodes = nodes.value
  return (
      activeNodes.length > 0 &&
      selectedNodeIds.value.length === activeNodes.length &&
      activeNodes.every(node => selectedNodeIds.value.includes(node.id))
  )
})

// 全选/取消全选
const toggleAllNodesAdd = () => {
  if (allNodesSelectedAdd.value) {
    selectedNodeIds.value = []
  } else {
    // 只选择活跃节点
    selectedNodeIds.value = nodes.value
        .map(n => n.id)
  }
}


onMounted(loadNodes)
</script>
