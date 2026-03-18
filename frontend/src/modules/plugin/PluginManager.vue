<template>
  <div class="plugin-market">
    <n-card>
      <template #header>
        <n-space justify="space-between" align="center">
          <n-space align="center">
            <n-text strong style="font-size: 18px">🔌 插件市场</n-text>
            <n-tag type="info" size="small">扩展系统能力</n-tag>
          </n-space>
          <n-space>
            <n-button @click="initPlugins" :loading="initing" type="primary" ghost>
              初始化官方插件
            </n-button>
          </n-space>
        </n-space>
      </template>

      <!-- 使用说明 -->
      <n-alert type="info" style="margin-bottom: 16px">
        <template #header>💡 使用说明</template>
        点击「初始化官方插件」→ 安装需要的插件 → 配置参数 → 在任务/工作流中使用
      </n-alert>

      <!-- 筛选栏 -->
      <n-space style="margin-bottom: 16px">
        <n-input v-model:value="searchKeyword" placeholder="搜索插件" clearable style="width: 200px" @keyup.enter="loadPlugins" />
        <n-select v-model:value="filterType" placeholder="类型筛选" clearable style="width: 120px" :options="typeOptions" @update:value="loadPlugins" />
        <n-button @click="loadPlugins">搜索</n-button>
      </n-space>

      <!-- 空状态 -->
      <n-empty v-if="!loading && data.length === 0" description="暂无插件，请点击「初始化官方插件」加载预置插件">
        <template #extra>
          <n-button type="primary" @click="initPlugins" :loading="initing">
            初始化官方插件
          </n-button>
        </template>
      </n-empty>

      <!-- 插件卡片 -->
      <n-grid v-else :cols="2" :x-gap="16" :y-gap="16" responsive="screen">
        <n-grid-item v-for="plugin in data" :key="plugin.id">
          <n-card size="small">
            <template #header>
              <n-space align="center">
                <n-text strong style="font-size: 24px">{{ plugin.icon || '📦' }}</n-text>
                <div>
                  <n-text strong>{{ plugin.name }}</n-text>
                  <br>
                  <n-text depth="3" style="font-size: 12px">v{{ plugin.version }} · {{ plugin.author }}</n-text>
                </div>
              </n-space>
            </template>
            <template #header-extra>
              <n-tag :type="plugin.is_installed ? 'success' : 'default'" size="small">
                {{ plugin.is_installed ? '已安装' : '未安装' }}
              </n-tag>
            </template>
            
            <p style="color: #666; min-height: 40px">{{ plugin.description || '暂无描述' }}</p>
            
            <n-descriptions :column="2" size="small">
              <n-descriptions-item label="类型">
                {{ { notification: '通知', executor: '执行器', datasource: '数据源' }[plugin.plugin_type] || plugin.plugin_type }}
              </n-descriptions-item>
              <n-descriptions-item label="插件ID">
                <n-text code>{{ plugin.plugin_id }}</n-text>
              </n-descriptions-item>
            </n-descriptions>
            
            <template #footer>
              <n-space justify="end">
                <n-button v-if="!plugin.is_installed" type="primary" size="small" @click="handleInstall(plugin)">
                  安装
                </n-button>
                <template v-else>
                  <n-button size="small" @click="handleConfig(plugin)">配置</n-button>
                  <n-button v-if="plugin.plugin_type === 'notification'" type="success" size="small" @click="handleTestSend(plugin)">
                    发送测试
                  </n-button>
                  <n-button v-if="plugin.plugin_type === 'executor'" type="info" size="small" @click="handleTestExecute(plugin)">
                    执行测试
                  </n-button>
                  <n-button type="warning" size="small" @click="handleUninstall(plugin)">
                    卸载
                  </n-button>
                </template>
              </n-space>
            </template>
          </n-card>
        </n-grid-item>
      </n-grid>

      <!-- 分页 -->
      <n-space v-if="data.length > 0" justify="center" style="margin-top: 16px">
        <n-pagination v-model:page="pagination.page" :page-count="Math.ceil(pagination.itemCount / pagination.pageSize)" @update:page="loadPlugins" />
      </n-space>
    </n-card>

    <!-- 配置对话框 -->
    <n-modal v-model:show="showConfigModal" preset="card" title="插件配置" style="width: 500px">
      <n-alert type="info" style="margin-bottom: 16px">
        <template #header>配置说明</template>
        <template v-if="currentPlugin?.plugin_id === 'notification-feishu'">
          在飞书群中添加机器人，获取 Webhook 地址
        </template>
        <template v-else-if="currentPlugin?.plugin_id === 'notification-dingtalk'">
          在钉钉群中添加机器人，获取 Webhook 地址和加签密钥
        </template>
        <template v-else-if="currentPlugin?.plugin_id === 'notification-wecom'">
          在企业微信群中添加机器人，获取 Webhook 地址
        </template>
        <template v-else-if="currentPlugin?.plugin_id === 'notification-bark'">
          下载 Bark App，获取服务器地址和 Key
        </template>
        <template v-else>
          请填写下方配置项
        </template>
      </n-alert>
      
      <n-form label-placement="left" label-width="120px">
        <n-form-item label="Webhook地址">
          <n-input v-model:value="configForm.webhook_url" placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/xxx" />
        </n-form-item>
        <n-form-item v-if="currentPlugin?.plugin_id === 'notification-dingtalk'" label="加签密钥">
          <n-input v-model:value="configForm.secret" placeholder="SECxxx" />
        </n-form-item>
        <n-form-item v-if="currentPlugin?.plugin_id === 'notification-bark'" label="服务器地址">
          <n-input v-model:value="configForm.server" placeholder="https://api.day.app" />
        </n-form-item>
        <n-form-item v-if="currentPlugin?.plugin_id === 'notification-bark'" label="Key">
          <n-input v-model:value="configForm.key" placeholder="Bark Key" />
        </n-form-item>
      </n-form>
      
      <template #footer>
        <n-space justify="end">
          <n-button @click="showConfigModal = false">取消</n-button>
          <n-button type="primary" @click="saveConfig" :loading="saving">保存配置</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 发送测试对话框 -->
    <n-modal v-model:show="showSendModal" preset="card" title="发送通知测试" style="width: 500px">
      <n-form label-placement="left" label-width="80px">
        <n-form-item label="标题">
          <n-input v-model:value="sendForm.title" placeholder="通知标题" />
        </n-form-item>
        <n-form-item label="内容">
          <n-input v-model:value="sendForm.content" type="textarea" :autosize="{ minRows: 3 }" placeholder="通知内容" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showSendModal = false">取消</n-button>
          <n-button type="primary" @click="doSend" :loading="sending">发送</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 执行测试对话框 -->
    <n-modal v-model:show="showExecuteModal" preset="card" title="执行命令测试" style="width: 650px">
      <n-form label-placement="left" label-width="80px">
        <n-form-item label="命令">
          <n-input v-model:value="executeForm.command" type="textarea" :autosize="{ minRows: 3 }" placeholder="ls -la" />
        </n-form-item>
        <n-form-item label="超时(秒)">
          <n-input-number v-model:value="executeForm.timeout" :min="10" :max="3600" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showExecuteModal = false">取消</n-button>
          <n-button type="primary" @click="doExecute" :loading="executing">执行</n-button>
        </n-space>
      </template>
      <n-divider>执行结果</n-divider>
      <n-code v-if="executeResult" :code="executeResult" language="text" />
    </n-modal>
  </div>
</template>

<script setup>
import { onMounted, ref, reactive } from 'vue'

const loading = ref(false)
const initing = ref(false)
const saving = ref(false)
const sending = ref(false)
const executing = ref(false)
const data = ref([])
const searchKeyword = ref('')
const filterType = ref(null)
const currentPlugin = ref(null)
const executeResult = ref('')

const showConfigModal = ref(false)
const configForm = ref({ webhook_url: '', secret: '', server: '', key: '' })

const showSendModal = ref(false)
const sendForm = ref({ title: '测试通知', content: '这是一条来自 ToolsPlus 的测试消息' })

const showExecuteModal = ref(false)
const executeForm = ref({ command: 'echo "Hello ToolsPlus"', timeout: 300 })

const pagination = reactive({ page: 1, pageSize: 10, itemCount: 0 })

const typeOptions = [
  { label: '通知', value: 'notification' },
  { label: '执行器', value: 'executor' },
  { label: '数据源', value: 'datasource' }
]

const loadPlugins = async () => {
  loading.value = true
  try {
    const result = await window.$request.get('/plugins', {
      params: {
        page: pagination.page,
        page_size: pagination.pageSize,
        keyword: searchKeyword.value,
        plugin_type: filterType.value
      }
    })
    data.value = result.items || []
    pagination.itemCount = result.total || 0
  } finally {
    loading.value = false
  }
}

const initPlugins = async () => {
  initing.value = true
  try {
    await window.$request.post('/plugins/init')
    window.$message.success('官方插件初始化成功')
    loadPlugins()
  } finally {
    initing.value = false
  }
}

const handleInstall = async (plugin) => {
  try {
    await window.$request.post(`/plugins/${plugin.plugin_id}/install`)
    window.$message.success('插件安装成功')
    loadPlugins()
  } catch (e) {}
}

const handleUninstall = async (plugin) => {
  window.$dialog.warning({
    title: '确认卸载',
    content: `确定要卸载 ${plugin.name} 吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      await window.$request.post(`/plugins/${plugin.plugin_id}/uninstall`)
      window.$message.success('插件已卸载')
      loadPlugins()
    }
  })
}

const handleConfig = async (plugin) => {
  currentPlugin.value = plugin
  configForm.value = { webhook_url: '', secret: '', server: 'https://api.day.app', key: '' }
  try {
    const configs = await window.$request.get(`/plugins/${plugin.plugin_id}/configs`)
    for (const c of (configs || [])) {
      configForm.value[c.config_key] = c.config_value
    }
  } catch (e) {}
  showConfigModal.value = true
}

const saveConfig = async () => {
  saving.value = true
  try {
    await window.$request.post(`/plugins/${currentPlugin.value.plugin_id}/install`, configForm.value)
    window.$message.success('配置保存成功')
    showConfigModal.value = false
  } finally {
    saving.value = false
  }
}

const handleTestSend = (plugin) => {
  currentPlugin.value = plugin
  showSendModal.value = true
}

const doSend = async () => {
  sending.value = true
  try {
    await window.$request.post(`/plugins/${currentPlugin.value.plugin_id}/send`, sendForm.value)
    window.$message.success('通知发送成功')
    showSendModal.value = false
  } finally {
    sending.value = false
  }
}

const handleTestExecute = (plugin) => {
  currentPlugin.value = plugin
  executeResult.value = ''
  showExecuteModal.value = true
}

const doExecute = async () => {
  executing.value = true
  try {
    const result = await window.$request.post(`/plugins/${currentPlugin.value.plugin_id}/execute`, executeForm.value)
    executeResult.value = JSON.stringify(result, null, 2)
  } catch (e) {
    executeResult.value = `执行失败: ${e.message}`
  } finally {
    executing.value = false
  }
}

onMounted(() => {
  loadPlugins()
})
</script>

<style scoped>
.plugin-market {
  padding: 0;
}
</style>
