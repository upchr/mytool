<template>
  <div class="ai-chat-container">
    <n-card title="AI 助手" class="chat-card">
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
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { NCard, NInput, NButton, NIcon, useMessage } from 'naive-ui'
import { PersonOutline as PersonIcon, ChatbubbleEllipsesOutline as RobotIcon } from '@vicons/ionicons5'
import request from '@/utils/request'
import { getAuthToken } from '@/utils/auth'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.min.css'

const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const messagesContainer = ref(null)
const message = useMessage()

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  highlight: (code, lang) => {
    try {
      if (lang && hljs.getLanguage(lang)) {
        return `<pre class="hljs"><code>${hljs.highlight(code, { language: lang }).value}</code></pre>`
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
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
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
  assistantMsg.content = `${assistantMsg.content || ''}${delta || ''}`
  scrollToBottom()
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
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      },
      body: JSON.stringify({
        message: content,
        history: messages.value.slice(0, -2) // 排除当前 user + 这个空 assistant
      })
    })

    if (!res.ok || !res.body) {
      throw new Error(`stream request failed: ${res.status}`)
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      // SSE 以 \n\n 分隔事件
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''

      for (const part of parts) {
        const line = part.split('\n').find((l) => l.startsWith('data:'))
        if (!line) continue
        const jsonStr = line.slice(5).trim()
        try {
          const data = JSON.parse(jsonStr)
          if (data.delta) appendAssistantDelta(assistantMsg, data.delta)
          if (data.error) throw new Error(data.error)
        } catch (e) {
          // JSON 解析失败直接跳过
          continue
        }
      }
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

// 初始化欢迎消息
onMounted(() => {
  messages.value.push({
    role: 'assistant',
    content: '您好！我是 AI 助手，有什么可以帮助您的吗？',
    timestamp: Date.now()
  })
})
</script>

<style scoped>
.ai-chat-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.chat-card {
  height: calc(100vh - 140px);
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
</style>