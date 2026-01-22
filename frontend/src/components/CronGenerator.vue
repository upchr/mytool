<template>
  <n-modal v-model:show="show" preset="card" title="Cron 生成器" style="width: 800px">
    <div class="cron-generator">
      <!-- 分钟 -->
      <div class="field-group">
        <label>分钟</label>
        <n-select
            v-model:value="minute"
            :options="minuteOptions"
            @update:value="updateCron"
        />
        <n-input v-if="minute === 'custom'" v-model:value="customMinute" placeholder="输入分钟值" @input="updateCron" />
      </div>

      <!-- 小时 -->
      <div class="field-group">
        <label>小时</label>
        <n-select
            v-model:value="hour"
            :options="hourOptions"
            @update:value="updateCron"
        />
        <n-input v-if="hour === 'custom'" v-model:value="customHour" placeholder="输入小时值" @input="updateCron" />
      </div>

      <!-- 日期（天） -->
      <div class="field-group">
        <label>日期（天）</label>
        <n-select
            v-model:value="day"
            :options="dayOptions"
            @update:value="updateCron"
        />
        <n-input v-if="day === 'custom'" v-model:value="customDay" placeholder="输入日期值" @input="updateCron" />
      </div>

      <!-- 月份 -->
      <div class="field-group">
        <label>月份</label>
        <n-select
            v-model:value="month"
            :options="monthOptions"
            @update:value="updateCron"
        />
        <n-input v-if="month === 'custom'" v-model:value="customMonth" placeholder="输入月份值" @input="updateCron" />
      </div>

      <!-- 星期 -->
      <div class="field-group">
        <label>星期（0=周一）</label>
        <n-select
            v-model:value="weekday"
            :options="weekdayOptions"
            @update:value="updateCron"
        />
        <n-input v-if="weekday === 'custom'" v-model:value="customWeekday" placeholder="输入星期值" @input="updateCron" />
      </div>

      <n-space vertical>
        <n-card title="当前表达式" size="small" hoverable>
          <n-tag type="info">
            {{ cronExpression }}
          </n-tag>
        </n-card>
        <n-card title="执行时间预览" size="medium" hoverable>
          <div v-for="(time, index) in previewTimes" :key="index" class="time-item">
            {{ formatDate(time.next_run) }}
          </div>
        </n-card>
      </n-space>

      <!-- 按钮 -->
      <div class="actions">
        <n-button @click="emit('close')">取消</n-button>
        <n-button type="primary" @click="fillCron">填入 Cron</n-button>
      </div>
    </div>
  </n-modal>
</template>

<script setup>
import {ref, computed, onMounted, watch} from 'vue'
import axios from "axios";
import {useMessage} from 'naive-ui'
const message = useMessage()

const minute = ref('*/5')
const hour = ref('*/6')
const day = ref('*')
const month = ref('*')
const weekday = ref('*')

// 自定义字段
const customMinute = ref('')
const customHour = ref('')
const customDay = ref('')
const customMonth = ref('')
const customWeekday = ref('')
const previewTimes = ref([])

// 选项配置
const minuteOptions = [
  { label: '每分钟 *', value: '*' },
  { label: '每 5 分钟', value: '*/5' },
  { label: '每 15 分钟', value: '*/15' },
  { label: '整分', value: '0' },
  { label: '自定义', value: 'custom' }
]

const hourOptions = [
  { label: '每小时 *', value: '*' },
  { label: '每 6 小时', value: '*/6' },
  { label: '每 12 小时', value: '*/12' },
  { label: '凌晨 0 点', value: '0' },
  { label: '上午 8 点', value: '8' },
  { label: '下午 6 点', value: '18' },
  { label: '自定义', value: 'custom' }
]

const dayOptions = [
  { label: '每天 *', value: '*' },
  { label: '每月 1 日', value: '1' },
  { label: '每月 1-5 日', value: '1-5' },
  { label: '每月最后一天', value: 'L' },
  { label: '自定义', value: 'custom' }
]

const monthOptions = [
  { label: '每月 *', value: '*' },
  { label: '1 月', value: '1' },
  { label: '12 月', value: '12' },
  { label: '每季度', value: '*/3' },
  { label: '每半年', value: '*/6' },
  { label: '自定义', value: 'custom' }
]

const weekdayOptions = [
  { label: '每天 *', value: '*' },
  { label: '周一', value: '0' },
  { label: '周日', value: '6' },
  { label: '周一到周五', value: '0-4' },
  { label: '周一和周五', value: '0,4' },
  { label: '自定义', value: 'custom' }
]
const formatDate = (isoString) => {
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',  // 显示四位年份
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 计算属性：Cron 表达式
const cronExpression = computed(() => {
  const m = minute.value === 'custom' ? customMinute.value : minute.value
  const h = hour.value === 'custom' ? customHour.value : hour.value
  const d = day.value === 'custom' ? customDay.value : day.value
  const mo = month.value === 'custom' ? customMonth.value : month.value
  const w = weekday.value === 'custom' ? customWeekday.value : weekday.value

  return `${m} ${h} ${d} ${mo} ${w}`
})


// 更新 Cron 表达式
const updateCron = async () => {
  try {
    const res = await axios.post('/api/cron/jobs/crons',{cron: cronExpression.value})
    previewTimes.value = res.data
  } catch (error) {
    message.error('执行时间预览api调用错误')
  }
  // 触发更新
}

// 填入 Cron 表达式
const fillCron = () => {
  emit('update:cron', cronExpression.value)
  emit('close')
}

// 定义事件
// const emit = defineEmits()
const emit = defineEmits(['update:cron', 'close'])
//传值
const show = defineModel({ type: Boolean, default: false })
const props = defineProps({
  cron: {
    type: String,
  }
})
watch(() => props.cron, (newCron) => {
  try{
    const parts = newCron.split(' ')  // Cron 表达式有 5 个部分
    if (parts.length === 5) {
      minute.value = parts[0]
      hour.value = parts[1]
      day.value = parts[2]
      month.value = parts[3]
      weekday.value = parts[4]
    }
  }catch (e) {
    message.error('加载cron表达式失败')
  }
}, { immediate: true })
// 初始化
onMounted(() => {
  updateCron()
})
</script>

<style scoped>
.cron-generator {
  display: grid;
  gap: 16px;
}

.field-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.field-group label {
  width: 80px;
  text-align: right;
}

.current-expression {
  margin-top: 16px;
  padding: 12px;
  background-color: #f5f5f5;
  border-radius: 4px;
}

.current-expression code {
  font-family: monospace;
  color: #2c3e50;
}

.preview {
  margin-top: 16px;
  padding: 12px;
  background-color: #f5f5f5;
  border-radius: 4px;
}

.time-item {
  margin: 4px 0;
}

.actions {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
