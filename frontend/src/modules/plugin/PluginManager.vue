<template>
  <div class="plugin-page">
    <n-card>
      <template #header>
        <n-space justify="space-between">
          <n-text strong style="font-size: 18px">🔌 插件管理</n-text>
          <n-button type="primary" @click="initPlugins" :loading="initing">
            初始化官方插件
          </n-button>
        </n-space>
      </template>

      <!-- 说明 -->
      <n-alert type="info" style="margin-bottom: 16px">
        <template #header>📌 插件是什么？</template>
        插件扩展系统的能力。<b>通知类插件</b>用于发送消息到飞书/钉钉等；<b>执行器插件</b>用于执行命令。
        <br>点击「初始化官方插件」加载 5 个官方预置插件。
      </n-alert>

      <!-- 空状态 -->
      <n-empty v-if="!loading && data.length === 0" description="暂无插件">
        <template #extra>
          <n-button type="primary" @click="initPlugins" :loading="initing">初始化官方插件</n-button>
        </template>
      </n-empty>

      <!-- 插件列表 -->
      <n-list v-else bordered>
        <n-list-item v-for="plugin in data" :key="plugin.id">
          <n-thing>
            <template #header>
              <n-space align="center">
                <span style="font-size: 28px">{{ plugin.icon || '📦' }}</span>
                <div>
                  <n-text strong style="font-size: 16px">{{ plugin.name }}</n-text>
                  <br>
                  <n-space>
                    <n-tag size="small">{{ plugin.plugin_type === 'notification' ? '通知' : '执行器' }}</n-tag>
                    <n-tag v-if="plugin.is_installed" type="success" size="small">已安装</n-tag>
                  </n-space>
                </div>
              </n-space>
            </template>
            <template #header-extra>
              <n-space vertical align="end">
                <n-button v-if="!plugin.is_installed" type="primary" size="small" @click="installPlugin(plugin)">安装</n-button>
                <n-space v-else>
                  <n-button size="small" @click="openConfig(plugin)">配置</n-button>
                  <n-button size="small" type="warning" @click="uninstallPlugin(plugin)">卸载</n-button>
                </n-space>
              </n-space>
            </template>
            <template #description>
              <n-text>{{ plugin.description }}</n-text>
              <n-divider style="margin: 8px 0" />
              <n-text depth="3" style="font-size: 12px">
                ID: {{ plugin.plugin_id }} · 版本: {{ plugin.version }}
              </n-text>
            </template>
          </n-thing>
        </n-list-item>
      </n-list>
    </n-card>

    <!-- 配置对话框 -->
    <n-modal v-model:show="showConfig" preset="card" :title="currentPlugin?.name + ' - 配置'" style="width: 500px">
      <n-alert type="info" style="margin-bottom: 16px">
        <template v-if="currentPlugin?.plugin_id === 'notification-feishu'">
          <b>飞书机器人配置说明：</b><br>
          1. 在飞书群中添加「自定义机器人」<br>
          2. 获取 Webhook 地址<br>
          3. 粘贴到下方
        </template>
        <template v-else-if="currentPlugin?.plugin_id === 'notification-dingtalk'">
          <b>钉钉机器人配置说明：</b><br>
          1. 在钉钉群中添加「自定义机器人」<br>
          2. 安全设置选择「加签」，获取密钥<br>
          3. 填写 Webhook 和密钥
        </template>
        <template v-else-if="currentPlugin?.plugin_id === 'notification-wecom'">
          <b>企业微信机器人配置说明：</b><br>
          1. 在企业微信群中添加机器人<br>
          2. 获取 Webhook 地址
        </template>
        <template v-else-if="currentPlugin?.plugin_id === 'notification-bark'">
          <b>Bark 配置说明：</b><br>
          1. 在 iOS 设备安装 Bark App<br>
          2. 获取服务器地址和 Key
        </template>
        <template v-else>
          请填写下方配置项
        </template>
      </n-alert>
      
      <n-form label-placement="left" label-width="100px">
        <n-form-item label="Webhook">
          <n-input v-model:value="configForm.webhook_url" placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/xxx" />
        </n-form-item>
        <n-form-item v-if="currentPlugin?.plugin_id === 'notification-dingtalk'" label="加签密钥">
          <n-input v-model:value="configForm.secret" placeholder="SEC开头的密钥" />
        </n-form-item>
        <n-form-item v-if="currentPlugin?.plugin_id === 'notification-bark'" label="服务器">
          <n-input v-model:value="configForm.server" placeholder="https://api.day.app" />
        </n-form-item>
        <n-form-item v-if="currentPlugin?.plugin_id === 'notification-bark'" label="Key">
          <n-input v-model:value="configForm.key" placeholder="Bark Key" />
        </n-form-item>
      </n-form>
      
      <template #footer>
        <n-space justify="end">
          <n-button @click="showConfig = false">取消</n-button>
          <n-button type="primary" @click="saveConfig" :loading="saving">保存</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 测试发送通知 -->
    <n-modal v-model:show="showTest" preset="card" title="发送测试通知" style="width: 450px">
      <n-alert type="info" style="margin-bottom: 12px">
        发送一条测试消息到已配置的通知渠道，验证配置是否正确。
      </n-alert>
      <n-form label-placement="left" label-width="60px">
        <n-form-item label="标题">
          <n-input v-model:value="testTitle" placeholder="测试通知" />
        </n-form-item>
        <n-form-item label="内容">
          <n-input v-model:value="testContent" type="textarea" placeholder="这是一条测试消息" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showTest = false">取消</n-button>
          <n-button type="primary" @click="doTestSend" :loading="testing">发送</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const loading = ref(false)
const initing = ref(false)
const saving = ref(false)
const testing = ref(false)
const data = ref([])

const showConfig = ref(false)
const showTest = ref(false)
const currentPlugin = ref(null)
const configForm = ref({ webhook_url: '', secret: '', server: 'https://api.day.app', key: '' })
const testTitle = ref('测试通知')
const testContent = ref('这是一条来自 ToolsPlus 的测试消息')

const loadPlugins = async () => {
  loading.value = true
  try {
    const result = await window.$request.get('/plugins', { params: { page: 1, page_size: 100 } })
    data.value = result.items || []
  } finally {
    loading.value = false
  }
}

const initPlugins = async () => {
  initing.value = true
  try {
    await window.$request.post('/plugins/init')
    window.$message.success('初始化成功！已加载 5 个官方插件')
    loadPlugins()
  } catch (e) {
    window.$message.error('初始化失败: ' + e.message)
  } finally {
    initing.value = false
  }
}

const installPlugin = async (plugin) => {
  try {
    await window.$request.post(`/plugins/${plugin.plugin_id}/install`)
    window.$message.success('安装成功！请点击「配置」填写参数')
    loadPlugins()
  } catch (e) {}
}

const uninstallPlugin = async (plugin) => {
  window.$dialog.warning({
    title: '确认卸载',
    content: `确定卸载 ${plugin.name}？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      await window.$request.post(`/plugins/${plugin.plugin_id}/uninstall`)
      window.$message.success('已卸载')
      loadPlugins()
    }
  })
}

const openConfig = async (plugin) => {
  currentPlugin.value = plugin
  configForm.value = { webhook_url: '', secret: '', server: 'https://api.day.app', key: '' }
  try {
    const configs = await window.$request.get(`/plugins/${plugin.plugin_id}/configs`)
    for (const c of (configs || [])) {
      configForm.value[c.config_key] = c.config_value
    }
  } catch (e) {}
  showConfig.value = true
}

const saveConfig = async () => {
  saving.value = true
  try {
    await window.$request.post(`/plugins/${currentPlugin.value.plugin_id}/install`, configForm.value)
    window.$message.success('配置已保存')
    showConfig.value = false
  } finally {
    saving.value = false
  }
}

const doTestSend = async () => {
  testing.value = true
  try {
    await window.$request.post(`/plugins/${currentPlugin.value.plugin_id}/send`, {
      title: testTitle.value,
      content: testContent.value
    })
    window.$message.success('发送成功！请检查目标渠道是否收到消息')
    showTest.value = false
  } catch (e) {
    window.$message.error('发送失败: ' + e.message)
  } finally {
    testing.value = false
  }
}

onMounted(() => {
  loadPlugins()
})
</script>

<style scoped>
.plugin-page {
  padding: 0;
}
</style>
