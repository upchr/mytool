<template>
  <div class="ai-chat-container">
    <div class="chat-layout">
      <!-- 左侧历史对话列表 -->
      <div class="history-sidebar" v-if="showHistory">
        <n-card title="💬 历史对话" class="history-card" size="small">
          <template #header-extra>
            <n-button text type="primary" @click="createNewConversation" title="新建对话">
              <template #icon>
                <n-icon :component="AddIcon" />
              </template>
            </n-button>
          </template>
          
          <div class="history-list">
            <div
              v-for="conv in conversations"
              :key="conv.id"
              :class="['history-item', { active: currentConversationId === conv.id }]"
              @click="loadConversation(conv.id)"
            >
              <div class="history-title">{{ conv.title }}</div>
              <div class="history-time">{{ formatDateTime(conv.updated_at) }}</div>
              <div class="history-actions">
                <n-button text size="tiny" type="error" @click.stop="deleteConversation(conv.id)">
                  <template #icon>
                    <n-icon :component="DeleteIcon" />
                  </template>
                </n-button>
              </div>
            </div>
            
            <n-empty v-if="conversations.length === 0" description="暂无历史对话" size="small" />
          </div>
        </n-card>
      </div>
      
      <!-- 右侧聊天区域 -->
      <div class="chat-main">
        <n-card :title="currentConversationTitle" class="chat-card">
          <template #header-extra>
            <n-select
                v-model:value="currentConfigId"
                :options="configOptions"
                placeholder="选择配置"
                size="small"
                style="width: 200px"
                @update:value="handleConfigChange"
                :loading="loadingConfigs"
            >
              <template #render-label="{ option }">
                <div class="config-option">
                  <n-icon :component="option.is_enabled ? CheckmarkCircleIcon : RadioIcon" :size="14" />
                  <span>{{ option.label }}</span>
                  <n-tag v-if="option.is_enabled" type="success" size="tiny" style="margin-left: 4px">当前</n-tag>
                </div>
              </template>
            </n-select>
          </template>
          <div class="chat-messages" ref="messagesContainer">
            <div
                v-for="(message, index) in messages"
                :key="index"
                :class="['message', message.role]"
            >
              <div class="message-avatar">
                <n-icon :size="24" :component="message.role === 'user' ? PersonIcon : RobotIcon" />
              </div>
              <div class="message-content">
                <div class="message-text markdown-body" v-html="renderMarkdown(message.content)"></div>
                <div class="message-time">{{ formatTime(message.timestamp) }}</div>
              </div>
            </div>

            <!-- API Key 配置提示 -->
            <div v-if="!isConfigured" class="config-notice">
              <n-alert type="info" title="💡 配置提示" :bordered="false">
                当前未配置 AI API Key，仅支持模拟响应。
                <br/>
                📖 获取密钥方法：访问
                <a href="https://platform.iflow.cn/profile?tab=apiKey" target="_blank" rel="noopener noreferrer">
                  iFlow 开放平台
                </a>
                申请 API Key，然后在系统设置中配置。
              </n-alert>
            </div>
          </div>

          <div class="chat-input">
            <n-input
                v-model:value="inputMessage"
                type="textarea"
                placeholder="输入消息..."
                :autosize="{ minRows: 2, maxRows: 6 }"
                @keydown.enter.exact="sendMessage"
                :disabled="isLoading"
            />
            <div class="chat-actions">
              <n-button
                  type="primary"
                  :loading="isLoading"
                  @click="sendMessage"
                  :disabled="!inputMessage.trim()"
              >
                发送
              </n-button>
              <n-button @click="clearMessages" :disabled="messages.length === 0">
                清空
              </n-button>
            </div>
          </div>
        </n-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import {ref, nextTick, onMounted, computed} from 'vue'
import {NCard, NInput, NButton, NIcon, useMessage, NAlert, NEmpty, NSelect, NTag} from 'naive-ui'
import {PersonOutline as PersonIcon, ChatbubbleEllipsesOutline as RobotIcon, AddOutline as AddIcon, TrashBinOutline as DeleteIcon, CheckmarkCircleOutline as CheckmarkCircleIcon, RadioOutline as RadioIcon} from '@vicons/ionicons5'
import {getAuthToken} from '@/utils/auth'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.min.css'

const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const messagesContainer = ref(null)
const message = useMessage()
const isConfigured = ref(true) // API Key 配置状态

// AI 配置相关
const configList = ref([])
const currentConfigId = ref(null)
const loadingConfigs = ref(false)

const configOptions = computed(() => {
  return configList.value.map(config => ({
    label: `${config.name || '未命名配置'} - ${config.model}`,
    value: config.id,
    is_enabled: config.is_enabled,
    api_base: config.api_base
  }))
})

// 历史对话相关
const showHistory = ref(true)
const conversations = ref([])
const currentConversationId = ref(null)
const currentConversationTitle = ref('AI 助手')

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  highlight: (code, lang) => {
    try {
      if (lang && hljs.getLanguage(lang)) {
        return `<pre class="hljs"><code>${hljs.highlight(code, {language: lang}).value}</code></pre>`
      }
      return `<pre class="hljs"><code>${hljs.highlightAuto(code).value}</code></pre>`
    } catch {
      const escaped = md.utils.escapeHtml(code)
      return `<pre class="hljs"><code>${escaped}</code></pre>`
    }
  }
})

const renderMarkdown = (text) => md.render(String(text ?? ''))

// 格式化时间
const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit'})
}

const formatDateTime = (dateTimeStr) => {
  if (!dateTimeStr) return ''
  const date = new Date(dateTimeStr)
  return date.toLocaleString('zh-CN', { 
    month: '2-digit', 
    day: '2-digit', 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const appendAssistantDelta = (assistantMsg, delta) => {
  // 使用 Vue 的响应式更新
  const newContent = `${assistantMsg.content || ''}${delta || ''}`
  assistantMsg.content = newContent

  // 强制触发视图更新
  // console.log('🌊 收到流式数据:', delta, '| 当前内容:', newContent)

  // 强制触发响应式更新（重要！）
  messages.value = [...messages.value]

  scrollToBottom()
}

// 加载对话列表
const loadConversations = async () => {
  try {
    const result = await window.$request.get('/ai-chat/conversations')
    conversations.value = result || []
  } catch (e) {
    console.warn('加载对话列表失败:', e)
  }
}

// 加载指定对话
const loadConversation = async (conversationId) => {
  try {
    currentConversationId.value = conversationId
    const conversation = await window.$request.get(`/ai-chat/conversations/${conversationId}`)
    
    // 加载消息
    messages.value = conversation.messages.map(msg => ({
      role: msg.role,
      content: msg.content,
      timestamp: new Date(msg.created_at).getTime()
    }))
    
    currentConversationTitle.value = conversation.title
    scrollToBottom()
  } catch (e) {
    console.error('加载对话失败:', e)
    message.error('加载对话失败')
  }
}

// 创建新对话
const createNewConversation = async () => {
  const defaultTitle = `新对话 ${new Date().toLocaleString('zh-CN', {month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'})}`
  
  try {
    const result = await window.$request.post('/ai-chat/conversations', {
      title: defaultTitle
    })
    currentConversationId.value = result.id
    currentConversationTitle.value = result.title
    messages.value = []
    await loadConversations()
    message.success('已创建新对话')
  } catch (e) {
    console.error('创建对话失败:', e)
    message.error('创建对话失败')
  }
}

// 删除对话
const deleteConversation = async (conversationId) => {
  try {
    await window.$request.delete(`/ai-chat/conversations/${conversationId}`)
    
    if (currentConversationId.value === conversationId) {
      currentConversationId.value = null
      currentConversationTitle.value = 'AI 助手'
      messages.value = []
    }
    await loadConversations()
    message.success('对话已删除')
  } catch (e) {
    console.error('删除对话失败:', e)
    message.error('删除对话失败')
  }
}

// 保存消息到数据库
const saveMessageToDB = async (role, content) => {
  if (!currentConversationId.value) return
  
  try {
    await window.$request.post(`/ai-chat/conversations/${currentConversationId.value}/messages`, {
      role: role,
      content: content
    })
  } catch (e) {
    console.warn('保存消息失败:', e)
  }
}

// 发送消息
const sendMessage = async () => {
  const content = inputMessage.value.trim()
  if (!content || isLoading.value) return

  // 添加用户消息
  messages.value.push({
    role: 'user',
    content,
    timestamp: Date.now()
  })

  inputMessage.value = ''
  scrollToBottom()
  
  // 保存到数据库
  await saveMessageToDB('user', content)

  try {
    isLoading.value = true
    // 先创建一个空的 assistant 消息，后续流式追加
    const assistantMsg = {
      role: 'assistant',
      content: '',
      timestamp: Date.now()
    }
    messages.value.push(assistantMsg)
    scrollToBottom()

    const token = getAuthToken()
    const res = await fetch('/api/ai-chat/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        message: content,
        history: messages.value.slice(0, -2), // 排除当前 user + 这个空 assistant
        conversation_id: currentConversationId.value
      })
    })

    if (!res.ok || !res.body) {
      throw new Error(`stream request failed: ${res.status}`)
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''
    let receivedCount = 0

    while (true) {
      const {value, done} = await reader.read()
      if (done) break

      const text = decoder.decode(value, {stream: true})
      buffer += text
      receivedCount++

      // SSE 以 \n\n 分隔事件
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''

      for (const part of parts) {
        const lines = part.split('\n')
        for (const line of lines) {
          if (!line.startsWith('data:')) continue
          const jsonStr = line.slice(5).trim()
          try {
            const data = JSON.parse(jsonStr)
            if (data.delta) {
              appendAssistantDelta(assistantMsg, data.delta)
              // 每次更新后强制刷新视图
              await nextTick()
            }
            if (data.error) throw new Error(data.error)
          } catch (e) {
            // JSON 解析失败直接跳过
            console.warn('JSON 解析失败:', jsonStr, e)
            continue
          }
        }
      }
    }

    // 流式完成后，保存完整的 AI 回复到数据库
    if (assistantMsg.content) {
      await saveMessageToDB('assistant', assistantMsg.content)
    }
    
  } catch (error) {
    message.error('发送消息失败，请重试')
    console.error('AI chat error:', error)
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

// 清空消息
const clearMessages = () => {
  messages.value = []
  message.success('消息已清空')
}

// 加载配置列表
const loadConfigList = async () => {
  loadingConfigs.value = true
  try {
    const data = await window.$request.get('/ai-chat/config/list')
    configList.value = data || []
    // 设置当前激活的配置
    const activeConfig = configList.value.find(c => c.is_enabled)
    if (activeConfig) {
      currentConfigId.value = activeConfig.id
    }
  } catch (error) {
    console.error('加载配置列表失败:', error)
  } finally {
    loadingConfigs.value = false
  }
}

// 切换配置
const handleConfigChange = async (configId) => {
  try {
    await window.$request.post(`/ai-chat/config/${configId}/set-active`)
    const config = configList.value.find(c => c.id === configId)
    const configName = config ? config.name : configId
    message.success(`已切换到配置: ${configName}`)
    // 重新加载配置列表以更新状态
    await loadConfigList()
  } catch (error) {
    console.error('切换配置失败:', error)
    message.error('切换配置失败')
    // 恢复原来的选择
    const activeConfig = configList.value.find(c => c.is_enabled)
    if (activeConfig) {
      currentConfigId.value = activeConfig.id
    }
  }
}

// 初始化欢迎消息和检查配置
onMounted(async () => {
  messages.value.push({
    role: 'assistant',
    content: '您好！我是 AI 助手，有什么可以帮助您的吗？',
    timestamp: Date.now()
  })
  
  // 检查 API Key 配置状态
  try {
    const result = await window.$request.get('/ai-chat/config')
    isConfigured.value = result?.configured ?? false
  } catch (e) {
    console.warn('检查 AI 配置失败:', e)
  }
  
  // 加载配置列表
  await loadConfigList()
  
  // 加载历史对话列表
  await loadConversations()
})
</script>

<style scoped>
.ai-chat-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.chat-layout {
  display: flex;
  gap: 16px;
  height: calc(100vh - 140px);
}

.history-sidebar {
  width: 300px;
  flex-shrink: 0;
  overflow-y: auto;
}

.history-card {
  height: 100%;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-item {
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #eee;
  position: relative;
}

.history-item:hover {
  background: #f5f5f5;
}

.history-item.active {
  background: #e6f7ff;
  border-color: #1890ff;
}

.history-title {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-time {
  font-size: 12px;
  color: #999;
}

.history-actions {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  opacity: 0;
  transition: opacity 0.2s;
}

.history-item:hover .history-actions {
  opacity: 1;
}

.chat-main {
  flex: 1;
  min-width: 0;
}

.chat-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #f5f5f5;
  border-radius: 8px;
  margin-bottom: 16px;
  max-height: calc(100vh - 300px);
}

.config-notice {
  margin-top: 16px;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message {
  display: flex;
  margin-bottom: 16px;
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 12px;
}

.message.user .message-avatar {
  background: #1976d2;
  color: white;
}

.message.assistant .message-avatar {
  background: #4caf50;
  color: white;
}

.message-content {
  max-width: 70%;
  display: flex;
  flex-direction: column;
}

.message.user .message-content {
  align-items: flex-end;
}

.message-text {
  padding: 12px 16px;
  border-radius: 12px;
  background: white;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  line-height: 1.6;
  word-wrap: break-word;
}

.markdown-body :deep(pre) {
  margin: 8px 0 0;
  padding: 12px;
  border-radius: 10px;
  overflow: auto;
}

.markdown-body :deep(code) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 13px;
}

.message.user .message-text {
  background: #1976d2;
  color: white;
}

.message-time {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.chat-input {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chat-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

/* 深色模式适配 */
.dark .chat-messages {
  background: #1e1e1e;
}

.dark .message-text {
  background: #2d2d2d;
  color: #e0e0e0;
}

.dark .message.user .message-text {
  background: #1976d2;
  color: white;
}

.dark .message-time {
  color: #888;
}

.dark .history-item {
  border-color: #333;
}

.dark .history-item:hover {
  background: #2a2a2a;
}

.dark .history-item.active {
  background: #1a3a5a;
  border-color: #1890ff;
}

.config-option {
  display: flex;
  align-items: center;
  gap: 6px;
}

.config-option :deep(.n-icon) {
  color: #1976d2;
}

.dark .config-option :deep(.n-icon) {
  color: #4dabf7;
}
</style>
