<template>
  <n-card title="🖥️ 节点管理" class="mb-6">
    <!--    按钮操作-->
    <n-space justify="end" style="margin-bottom: 10px">
      <n-button v-if="!isBatchMode" @click="enterBatchMode">批量操作</n-button>
      <n-button type="warning" @click="manageTicket();isBatchMode = false;resetForm();">凭据管理</n-button>
      <n-button type="primary" @click="showForm=true;isBatchMode = false;resetForm();">添加节点</n-button>
    </n-space>

    <!-- 添加节点表单 -->
    <n-modal v-model:show="showForm" preset="card"
             :title="'🖥️ '+title"
             class=" mediaModal"
             draggable
             :on-after-leave="()=>resetForm(true)">
      <n-form v-if="showForm" ref="formRef" :model="currentNode" :rules="rules" label-placement="left" :label-width="100">
        <n-grid cols="1 s:2" responsive="screen">
          <n-grid-item>
            <n-form-item path="name" label="节点名称">
              <n-input v-model:value="currentNode.name" placeholder="例如：生产服务器" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item path="host" label="主机地址">
              <n-input v-model:value="currentNode.host" placeholder="IP 或域名" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item path="port" label="SSH端口">
              <n-input-number v-model:value="currentNode.port" placeholder="端口：22" :min="1" :max="65535" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item cols="1 600:2">
            <n-form-item label="凭据模板">
              <n-select
                  v-model:value="selectedCredentialId"
                  :options="credentialTemplates.map(t => ({ label: t.name, value: t.id }))"
                  placeholder="选择凭据模板（可选）"
                  clearable
                  @update:value="applyCredentialTemplate">
                <template #header>
                  <n-button
                      text
                      size="small"
                      block
                      @click="manageTicket"
                  >
                    管理凭据
                  </n-button>
                </template>
              </n-select>
            </n-form-item>
          </n-grid-item>
          <n-grid-item cols="1 600:2">
            <n-form-item path="auth_type" label="认证方式">
              <n-radio-group v-model:value="currentNode.auth_type">
                <n-space>
                  <n-radio value="password">密码认证</n-radio>
                  <n-radio value="ssh_key">SSH密钥</n-radio>
                </n-space>
              </n-radio-group>
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item path="username" label="用户名">
              <n-input v-model:value="currentNode.username" placeholder="root / admin" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item v-if="currentNode.auth_type === 'password'">
            <n-form-item path="password" label="密码">
              <n-input
                  type="password"
                  show-password-on="click"
                  placeholder="密码"
                  v-model:value="currentNode.password"
                  :maxlength="8"
              >
                <template #password-visible-icon>
                  <n-icon :size="16" :component="GlassesOutline" />
                </template>
                <template #password-invisible-icon>
                  <n-icon :size="16" :component="Glasses" />
                </template>
              </n-input>

            </n-form-item>
          </n-grid-item>
          <n-grid-item v-else>
            <n-form-item path="private_key" label="私钥">
              <n-input
                  v-model:value="currentNode.private_key"
                  type="textarea"
                  placeholder="粘贴私钥内容（PEM格式）"
                  :autosize="{
                    minRows: 6,
                    maxRows: 10,
                  }"
              />
            </n-form-item>
          </n-grid-item>
        </n-grid>
        <n-space justify="end" class="mt-4">
          <n-button type="primary" @click="addNode">
            {{ isEditing ? '更新节点' : '添加节点' }}
          </n-button>
          <n-button
              type="warning"
              @click="saveAsTemplate"
              :disabled="!currentNode.name || !currentNode.username"
          >
            保存凭据模板
          </n-button>
        </n-space>
      </n-form>
    </n-modal>

    <n-modal v-model:show="pjForm" preset="card" class="mediaModal"
             title="凭据管理"
             draggable
             :on-after-leave="()=>resetForm(true)">
      <n-space justify="end" style="margin-bottom: 15px">
        <n-button type="success" @click="pjEditForm=true;pjNewFlag=true">新增</n-button>
      </n-space>

      <n-form  :model="credentialTemplates" label-placement="left" :label-width="100">
        <n-space vertical style="height: 80vh;overflow-y: auto">
          <n-table striped size="small">
            <thead>
            <tr>
              <th style="text-align: center" width="25%" >名称</th>
              <th style="text-align: center" width="25%">用户名</th>
              <th style="text-align: center" width="12%">类型</th>
              <th style="text-align: center" width="38%">操作</th>
            </tr>
            </thead>
            <tbody>
            <tr v-for="node in credentialTemplates" :key="node.id">
              <td style="text-align: center">{{node.name}}</td>
              <td style="text-align: center">{{node.username}}</td>
              <td style="text-align: center">
                <n-tag :type="node.auth_type === 'password' ? 'success' : 'warning'">
                  {{ node.auth_type === 'password' ? '密码' : '密钥' }}
                </n-tag>
              </td>
              <td >
                <n-space justify="center">
                  <n-button size="small" type="info" @click="editPj(node)">编辑</n-button>
                  <n-button size="small" type="error" @click="deletePj(node)">删除</n-button>
                </n-space>
              </td>
            </tr>
            </tbody>
          </n-table>
        </n-space>
      </n-form>
    </n-modal>
    <n-modal v-model:show="pjEditForm" preset="card" class="mediaModal"
             :title="pjTitle"
             draggable
             :on-after-leave="()=>resetFormPj(true)">
      <n-form :model="credentialForm"  ref="credentialFormRef" :rules="pjrules" label-placement="left" :label-width="100">
        <n-grid cols="1 s:2" responsive="screen">
          <n-grid-item>
            <n-form-item path="name" label="凭证名称">
              <n-input v-model:value="credentialForm.name" placeholder="凭证名称" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item cols="1 600:2">
            <n-form-item path="auth_type" label="认证方式">
              <n-radio-group v-model:value="credentialForm.auth_type">
                <n-space>
                  <n-radio value="password">密码认证</n-radio>
                  <n-radio value="ssh_key">SSH密钥</n-radio>
                </n-space>
              </n-radio-group>
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item path="username" label="用户名">
              <n-input v-model:value="credentialForm.username" placeholder="root / admin" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item v-if="credentialForm.auth_type === 'password'">
            <n-form-item path="password" label="密码">
              <n-input
                  type="password"
                  show-password-on="click"
                  placeholder="密码"
                  v-model:value="credentialForm.password"
                  :maxlength="8"
              >
                <template #password-visible-icon>
                  <n-icon :size="16" :component="GlassesOutline" />
                </template>
                <template #password-invisible-icon>
                  <n-icon :size="16" :component="Glasses" />
                </template>
              </n-input>

            </n-form-item>
          </n-grid-item>
          <n-grid-item v-else>
            <n-form-item path="private_key" label="私钥">
              <n-input
                  v-model:value="credentialForm.private_key"
                  type="textarea"
                  placeholder="粘贴私钥内容（PEM格式）"
                  :autosize="{
                    minRows: 6,
                    maxRows: 10,
                  }"
              />
            </n-form-item>
          </n-grid-item>
        </n-grid>
        <n-space justify="end" class="mt-4">
          <n-button type="primary" @click="savePj">
            {{ pjNewFlag ?  '添加模板':'更新模板' }}
          </n-button>
        </n-space>
      </n-form>
    </n-modal>


    <!--    批量操作-->
    <n-space justify="end" class="mt-4" style="margin-top: 10px">
      <div v-if="isBatchMode" class="mb-4 flex justify-between items-center bg-gray-50 p-3 rounded">
        <n-space justify="end" >已选择 {{ selectedNodeIds.length }} 个节点</n-space>
        <n-space style="margin-top: 5px">
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
    <n-list v-else  style="height: 70vh;overflow-y: auto;">
      <n-list-item v-for="node in nodes" :key="node.id">
        <n-card hoverable size="small" :title="'节点名称：'+node.name" :bordered="false" class="shadow-sm"
                @click="handleCardClick(node)">

          <template #header-extra>
            <n-checkbox
                v-if="isBatchMode"
                :checked="selectedNodeIds.includes(node.id)"
                @click.stop.prevent="(e) => toggleNodeSelection(node.id, !selectedNodeIds.includes(node.id))"
            />
          </template>
          <template #action>
            <n-space v-if="!isBatchMode" justify="end">
              <n-button size="small" @click="testConnection(node)">⚡️</n-button>
                <n-button
                    size="small"
                    :type="node.is_active ? 'success' : 'warning'"
                    @click="toggleNode(node)"
                >
                  {{ node.is_active ? '停用' : '启用' }}
                </n-button>
                <n-button size="small" type="info"  @click="editNode(node)">
                  编辑
                </n-button>
                <n-popconfirm @positive-click="deleteNode(node)">
                  <template #trigger>
                    <n-button size="small" type="error">删除</n-button>
                  </template>
                  确定要删除节点 "{{ node.name }}" 吗？
                </n-popconfirm>
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
import {NInput} from 'naive-ui'
import { Glasses, GlassesOutline } from '@vicons/ionicons5'

const nodes = ref([])
const defaultNode = ref({
  name: '',
  host: '',
  port: 22,
  username: '',
  auth_type: 'password',
  password: '',
  private_key: '',
  is_active: true
})
const showForm = ref(false)

// 表单验证规则
const rules = {
  name: { required: true, message: '请输入节点名称', trigger: ['blur'] },
  host: { required: true, message: '请输入主机地址', trigger: ['blur'] ,pattern: /^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+(?:[a-zA-Z]{2,})$|^(?:\d{1,3}\.){3}\d{1,3}$/},
  username: { required: true, message: '请输入用户名', trigger: ['blur'],min: 3,max: 20,},
  /*password: [
    {
      validator: (rule, value, callback) => {
        if (currentNode.value.auth_type === 'password' && (!value || !value.trim())) {
          callback(new Error('请输入密码'))
        } else {
          callback() // 验证通过
        }
      },
      trigger: ['blur', 'input']
    }
  ],*/
  private_key: [
    {
      validator: (rule, value, callback) => {
        if (currentNode.value.auth_type === 'ssh_key' && (!value || !value.trim())) {
          callback(new Error('请粘贴私钥'))
        } else {
          callback()
        }
      },
      trigger: ['blur', 'input'],
      required: true,
    }
  ],
}

const formRef = ref(null)

const loadNodes = async () => {
  try {
    const res = await window.$request.get('/nodes/only_active/false')
    nodes.value = res
  } catch (error) {
    window.$message.error('加载节点失败')
  }
}

const addNode = async () => {
  await formRef.value.validate()
  try {
    if (isEditing.value) {
      // 更新节点
      const res = await window.$request.put(`/nodes/${currentNode.value.id}`, currentNode.value)
      window.$message.success('节点更新成功')
    } else {
      // 新增节点
      const res = await window.$request.post('/nodes', currentNode.value)
      window.$message.success('节点添加成功')
    }
    resetForm(true)
    loadNodes()
  } catch (error) {
    console.log(error)
    window.$message.error(isEditing.value ? '更新节点失败' : '添加节点失败')
  }
}

const testConnection = async (node) => {
  try {
    window.$message.info(`正在测试 ${node.name} 的连接...`)
    // 👇 调用后端真实 SSH 测试接口（需后端实现）
    await window.$request.post(`/nodes/${node.id}/test`)
    window.$message.success(`${node.name} 连接成功！`)
  } catch (error) {
    window.$message.error(`${node.name} 连接失败`)
  }
}

const toggleNode = async (node) => {
  try {
    node.is_active = !node.is_active
    // 👇 调用后端更新接口（需后端实现）
    await window.$request.patch(`/nodes/${node.id}/toggle`, { is_active: node.is_active })
    window.$message.success(`节点 ${node.name} 已${node.is_active ? '启用' : '停用'}`)
  } catch (error) {
    window.$message.error('操作失败')
  }
}
const isEditing = ref(false)
const title = ref('我的节点')
const currentNode = ref({
  name: '',
  host: '',
  port: 22,
  username: '',
  auth_type: 'password',
  password: '',
  private_key: '',
  is_active: true
})


const editNode = async (node) => {
  currentNode.value = {...node}
  isEditing.value = true
  showForm.value = true
  title.value = `修改：${currentNode.value.name}`
}
const resetForm = (afterFlag=false) => {
  if(afterFlag){
    showForm.value=false
    isEditing.value = false
    title.value = '节点管理'
    selectedCredentialId.value=null
  }

  currentNode.value = {...defaultNode.value}

  if (!isEditing){
    currentNode.value.id = null
  }
}

const deleteNode = async (node) => {
  try {
    await window.$request.delete(`/nodes/${node.id}`)
    window.$message.success('节点删除成功')
    loadNodes()
  } catch (error) {
    window.$message.error('删除节点失败')
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
    await window.$request.post('/nodes/deleteBatch', { node_ids: selectedNodeIds.value })
    window.$message.success(`成功删除 ${selectedNodeIds.value.length} 个节点`)
    cancelBatch()
    loadNodes()
  } catch (error) {
    window.$message.error('批量删除失败')
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



const pjForm = ref(false)
const pjEditForm = ref(false)
const pjNewFlag = ref(true)
const pjTitle = computed(() => {
  if(pjNewFlag.value){
    return '新增凭据'
  }else{
    return `修改凭据  ${credentialForm?.value.name}`
  }
})
const credentialForm = ref({
  name: '',
  username: '',
  auth_type: 'password',
  password: '',
  private_key: '',
})
const credentialFormRef = ref(null)
const editPj = async (node) => {
  pjEditForm.value = true;
  pjNewFlag.value = false;
  credentialForm.value = { ...node };
};
const credentialTemplates = ref([])
const selectedCredentialId = ref(null) // 当前选中的模板ID
const loadCredentialTemplates = async () => {
  try {
    const res = await window.$request.get('/nodes/credentials/')
    credentialTemplates.value = res
  } catch (error) {
    console.warn('加载凭据模板失败:', error)
  }
}
const applyCredentialTemplate = (templateId) => {
  if (!templateId) return

  const template = credentialTemplates.value.find(t => t.id === templateId)
  if (template) {
    currentNode.value.username = template.username
    currentNode.value.auth_type = template.auth_type
    currentNode.value.password = template.password || ''
    currentNode.value.private_key = template.private_key || ''
  }
}
const pjrules = {
  name: { required: true, message: '请输入凭据名称', trigger: ['blur'] },
  username: { required: true, message: '请输入用户名', trigger: ['blur'],min: 3,max: 20,},
  /*password: [
    {
      validator: (rule, value, callback) => {
        if (credentialForm.value.auth_type === 'password' && (!value || !value.trim())) {
          callback(new Error('请输入密码'))
        } else {
          callback() // 验证通过
        }
      },
      trigger: ['blur', 'input']
    }
  ],*/
  private_key: [
    {
      validator: (rule, value, callback) => {
        if (credentialForm.value.auth_type === 'ssh_key' && (!value || !value.trim())) {
          callback(new Error('请粘贴私钥'))
        } else {
          callback()
        }
      },
      trigger: ['blur', 'input'],
      required: true,
    }
  ],
}
import { prompt } from '@/utils/dialog.js'
const resetFormPj = (afterFlag=false) => {
  if(afterFlag){
    pjEditForm.value=false
  }

  credentialForm.value = {
    name: '',
    username: '',
    auth_type: 'password',
    password: '',
    private_key: '',
  }
}
const savePj = async () => {
  try {
    await credentialFormRef.value?.validate() // 验证失败会抛出错误
    if(pjNewFlag.value){
      await window.$request.post('/nodes/credentials/', credentialForm.value)
      window.$message.success('凭据模板保存成功')
    }else{
      // 更新节点
      const res = await window.$request.put(`/nodes/credentials/${credentialForm.value.id}`, credentialForm.value)
      window.$message.success('凭据模板更新成功')
    }
    await loadCredentialTemplates() // 刷新列表
    pjEditForm.value=false
    resetFormPj(true)
  } catch (error) {
    window.$message.error('凭据模板保存失败')
  }
}
const deletePj = async (pj) => {
  try {
    await window.$request.delete(`/nodes/credentials/${pj.id}`)
    window.$message.success('凭据删除成功')
    await loadCredentialTemplates() // 刷新列表

  } catch (error) {
      window.$message.error('删除失败，请重试')
  }
}
const saveAsTemplate = async () => {
  try {
    const name = await prompt({
      title: '新建凭据',
      placeholder: '请输入凭据名称',
      validate: (value) => value.trim().length >= 2,
      validateMessage: '名称至少2个字符'
    })

    const payload = {
      name,
      username: currentNode.value.username,
      auth_type: currentNode.value.auth_type,
      password: currentNode.value.auth_type === 'password' ? currentNode.value.password : undefined,
      private_key: currentNode.value.auth_type === 'ssh_key' ? currentNode.value.private_key : undefined
    }
    await window.$request.post('/nodes/credentials/', payload)
    window.$message.success('凭据模板保存成功')
    await loadCredentialTemplates() // 刷新列表
  } catch (error) {
      window.$message.error('凭据模板保存失败')
  }
}
const manageTicket = () => {
  pjForm.value=true
  // window.$message.error('凭据模板管理功能未开发')
}
onMounted(async () => {
  await loadNodes()
  await loadCredentialTemplates() // 新增
})
</script>
<style>

</style>
