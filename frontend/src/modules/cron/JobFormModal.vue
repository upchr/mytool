<!-- src/modules/cron/JobFormModal.vue -->
<template>
  <n-modal
      v-model:show="visible"
      preset="card"
      :title="isEdit ? '编辑任务' : '添加新任务'"
      class="mediaModal"
  >
    <n-form
        ref="formRef"
        :model="formData"
        :rules="jobRules"
        label-placement="left"
        label-width="auto"
    >
      <n-form-item path="node_ids" label="所属节点">
        <n-select
            v-model:value="formData.node_ids"
            :options="nodeOptions"
            multiple
            :disabled="isEdit"
            placeholder="请选择节点"
            max-tag-count="responsive"
        >
          <template #action>
            <n-button
                text
                size="small"
                block
                @click="toggleAllNodes"
            >
              {{ allNodesSelected ? '取消全选' : '全选' }}
            </n-button>
          </template>
        </n-select>
      </n-form-item>

      <n-form-item path="name" label="任务名称">
        <n-input v-model:value="formData.name" placeholder="例如：每日备份" />
      </n-form-item>

      <n-form-item path="schedule" label="Cron表达式">
        <n-input
            v-model:value="formData.schedule"
            placeholder="* * * * *【分 时 日 月 周】"
        >
          <template #suffix>
            <n-button text @click="showCronGenerator = true" style="color: grey">
              <n-icon><CalendarOutline /></n-icon>
              生成器
            </n-button>
          </template>
        </n-input>

        <CronGenerator
            v-model:show="showCronGenerator"
            :cron="formData.schedule"
            @update:cron="formData.schedule = $event"
            @close="showCronGenerator = false"
        />
      </n-form-item>

      <n-form-item path="command" label="执行命令">
        <MonacoEditor
            v-model="formData.command"
            language="shell"
            height="200px"
            :style="{ marginTop: '8px' }"
        />
      </n-form-item>

      <n-form-item path="description" label="任务描述">
        <n-input
            v-model:value="formData.description"
            type="textarea"
            placeholder="任务说明"
            :autosize="{ minRows: 2, maxRows: 5 }"
        />
      </n-form-item>

      <n-form-item label="消息通知">
          <n-switch v-model:value="formData.is_notice">
            <template #checked>禁用</template>
            <template #unchecked>通知</template>
          </n-switch>
          <n-input-number v-if="formData.is_notice" style="margin-left: 10px;width:150px"
              v-model:value="formData.error_times" :min="1"
              placeholder="连续错误达到次数时，消息提醒"
          />
      </n-form-item>

      <n-form-item label="任务启用">
        <n-switch v-model:value="formData.is_active">
          <template #checked>停用</template>
          <template #unchecked>启用</template>
        </n-switch>
      </n-form-item>
      <n-space justify="end" class="mt-4">
        <n-button @click="handleCancel">取消</n-button>
        <n-button type="primary" @click="handleSubmit">
          {{ isEdit ? '保存修改' : '保存任务' }}
        </n-button>
      </n-space>
    </n-form>
  </n-modal>
</template>

<script setup>
import {ref, computed, defineProps, defineEmits, watch} from 'vue'
import CronGenerator from '@/components/CronGenerator.vue'
import MonacoEditor from '@/components/MonacoEditor.vue'
import { CalendarOutline } from '@vicons/ionicons5'
import { NModal, NForm, NFormItem, NInput, NSelect, NSwitch, NButton, NIcon } from 'naive-ui'

const props = defineProps({
  visible: Boolean,
  nodes: Array,
  jobData: Object, // 编辑时的数据
  isEdit: Boolean
})

const emit = defineEmits(['update:visible', 'update:jobData', 'submit', 'cancel'])
// 同步 visible 状态.双向
const visible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

// 表单数据.单向
const formData = ref({})
watch(() => props.jobData, (newJobData) => {
  if (newJobData) {
    formData.value = JSON.parse(JSON.stringify(newJobData))
  }
}, { immediate: true })



// 节点选项
const nodeOptions = computed(() =>
    props.nodes.map(node => ({
      label: `${node.name} (${node.host})`,
      value: node.id
    }))
)

// 全选逻辑
const allNodesSelected = computed(() => {
  const activeNodes = props.nodes
  return (
      activeNodes.length > 0 &&
      formData.value.node_ids?.length === activeNodes.length &&
      activeNodes.every(node => formData.value.node_ids.includes(node.id))
  )
})

const toggleAllNodes = () => {
  if (allNodesSelected.value) {
    formData.value.node_ids = []
  } else {
    formData.value.node_ids = props.nodes.map(n => n.id)
  }
}

// Cron 验证规则
const CRON_REGEX = /^(\*|(\*\/\d{1,2})|(\d{1,2})(-\d{1,2})?(\/\d{1,2})?)(,(\*|(\*\/\d{1,2})|(\d{1,2})(-\d{1,2})?(\/\d{1,2})?))*\s+(\*|(\*\/\d{1,2})|([01]?\d|2[0-3])(-([01]?\d|2[0-3]))?(\/\d{1,2})?)(,(\*|(\*\/\d{1,2})|([01]?\d|2[0-3])(-([01]?\d|2[0-3]))?(\/\d{1,2})?))*\s+(\*|(\*\/\d{1,2})|([1-9]|[12]\d|3[01])(-([1-9]|[12]\d|3[01]))?(\/\d{1,2})?)(,(\*|(\*\/\d{1,2})|([1-9]|[12]\d|3[01])(-([1-9]|[12]\d|3[01]))?(\/\d{1,2})?))*\s+(\*|(\*\/\d{1,2})|(1[0-2]|[1-9])(-(1[0-2]|[1-9]))?(\/\d{1,2})?)(,(\*|(\*\/\d{1,2})|(1[0-2]|[1-9])(-(1[0-2]|[1-9]))?(\/\d{1,2})?))*\s+(\*|(\*\/\d{1,2})|[0-6](-[0-6])?(\/\d{1,2})?)(,(\*|(\*\/\d{1,2})|[0-6](-[0-6])?(\/\d{1,2})?))*$/;

const jobRules = {
  node_ids: [{
    required: true,
    validator: (rule, value) => value && value.length > 0,
    message: '请选择至少一个节点',
    trigger: ['blur', 'change']
  }],
  name: { required: true, message: '请输入任务名称', trigger: ['blur'] },
  schedule: [
    { required: true, message: '请输入Cron表达式', trigger: ['blur'] },
    {
      validator: (rule, value) => value && CRON_REGEX.test(value.trim()),
      message: 'Cron表达式格式错误（分 时 日 月 周）',
      trigger: ['blur']
    }
  ],
  command: { required: true, message: '请输入执行命令', trigger: ['blur'] }
}

const formRef = ref(null)
const showCronGenerator = ref(false)

const handleCancel = () => {
  emit('cancel')
  visible.value = false
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    emit('submit', formData.value)
    visible.value = false
  } catch (error) {
    // 验证失败，不关闭模态框
  }
}
</script>
