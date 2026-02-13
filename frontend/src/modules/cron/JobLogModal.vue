<!-- src/modules/cron/JobLogModal.vue -->
<template>
  <n-modal
      v-model:show="visible"
      @after-leave="handleClose"
      preset="card"
      title="执行日志"
      style="width: 1200px; max-height: 80vh; min-height: 60vh"
  >
    <div class="space-y-4">
      <div class="flex justify-between items-center" style="margin-bottom: 20px">
        <n-tag :type="getLogStatusType(execution?.status)">
          {{ execution?.status }}
        </n-tag>
        <n-button
            v-if="['running', 'pending'].includes(execution?.status)"
            size="small"
            type="error"
            style="margin-left: 10px"
            @click="stopExecution"
        >
          中断执行
        </n-button>
        <n-text depth="3" style="margin-left: 10px">执行ID: {{ execution?.id }}</n-text>
      </div>

      <!-- STDOUT -->
      <div>
        <n-text depth="3">STDOUT:</n-text>
        <div
            ref="stdoutRef"
            :class="stdOutClass"
        >
          {{ execution?.output || '无输出' }}
        </div>
      </div>

      <!-- STDERR -->
      <div>
        <n-text depth="3">STDERR:</n-text>
        <div
            ref="stderrRef"
            :class="stdErrClass"
        >
          {{ execution?.error || '无错误' }}
        </div>
      </div>
    </div>
  </n-modal>
</template>

<script setup>
import {ref, computed, onUnmounted, nextTick, watch} from 'vue'
import { useThemeStore } from '@/stores/theme'
import { getAuthToken } from '@/utils/auth'
import { NModal, NTag, NButton, NText } from 'naive-ui'

const props = defineProps({
  visible: Boolean,
  execution: Object,
  onConnectWebSocket: Function,
  onStopExecution: Function
})

const emit = defineEmits(['update:visible', 'close'])

const themeStore = useThemeStore()
const stdoutRef = ref(null)
const stderrRef = ref(null)
let ws = null

// 同步 visible 状态
const visible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

// 样式类
const stdOutClass = computed(() => {
  return [
    'stdClass',
    themeStore.theme?.name === 'dark' ? 'stdOutClassM' : 'stdOutClass'
  ]
})

const stdErrClass = computed(() => {
  return [
    'stdClass',
    themeStore.theme?.name === 'dark' ? 'stdErrClassM' : 'stdErrClass'
  ]
})

// 连接 WebSocket
const connectWebSocket = (executionId) => {
  const wsUrl = `/api/cron/executions/${executionId}/logs?token=${encodeURIComponent(getAuthToken())}`

  ws = new WebSocket(wsUrl)
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    if (props.execution && props.execution.id === executionId) {
      if (data.end_time) {
        // 更新父组件的 execution 数据
        emit('update-execution', data)
      } else {
        // 实时更新日志
        emit('update-log', { output: data.output, error: data.error })
      }

      // 自动滚动
      nextTick(() => {
        const isAtBottom = isScrollAtBottom(stdoutRef.value)
        if (isAtBottom) {
          scrollToBottom(stdoutRef.value)
          scrollToBottom(stderrRef.value)
        }
      })
    }
  }

  ws.onclose = () => {
    console.log('WebSocket closed')
  }

  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
  }
}

// 滚动工具函数
const isScrollAtBottom = (element) => {
  const margin = 100
  return element.scrollHeight - element.scrollTop - element.clientHeight < margin
}

const scrollToBottom = (element) => {
  if (element) {
    element.scrollTop = element.scrollHeight
  }
}

// 停止执行
const stopExecution = async () => {
  if (ws) {
    ws.close()
    ws = null
  }
  if (props.onStopExecution) {
    await props.onStopExecution(props.execution)
  }
}

// 关闭处理
const handleClose = () => {
  if (ws) {
    ws.close()
    ws = null
  }
  emit('close')
}

// 监听 execution 变化
watch(() => props.execution, (newVal) => {
  if (newVal && newVal.status === 'running') {
    connectWebSocket(newVal.id)
  }
}, { immediate: true })

// 清理
onUnmounted(() => {
  if (ws) {
    ws.close()
  }
})

// 状态类型
const getLogStatusType = (status) => {
  switch (status) {
    case 'success': return 'success'
    case 'failed': return 'error'
    case 'running': return 'info'
    case 'cancelled': return 'warning'
    default: return 'default'
  }
}
</script>

<style scoped>
.stdClass {
  height: 25vh;
  overflow-y: auto;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
  padding: 10px;
}
.stdOutClass { background-color: whitesmoke; }
.stdErrClass { background-color: wheat; }
.stdOutClassM { background-color: rgb(24, 24, 28); }
.stdErrClassM { background-color: gray; }
</style>
