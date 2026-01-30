<template>
  <n-modal
      v-model:show="visible"
      :preset="dialogPreset"
      :type="type"
      :title="title"
      :positive-text="positiveText"
      :negative-text="negativeText"
      :show-icon="showIcon"
      :mask-closable="maskClosable"
      :closable="closable"
      @positive-click="handleSubmit"
      @negative-click="handleCancel"
      @close="handleClose"
      class="mediaModal"
  >
<!--    直接title控制-->
<!--    <template #header v-if="$slots.header">
      <slot name="header" />
    </template>-->

    <template #icon v-if="$slots.icon">
      <slot name="icon" />
    </template>

    <div class="dialog-content" :class="contentClass">
      <!-- 表单区域 -->
      <n-form
          ref="formRef"
          :model="localFormData"
          :rules="rules"
          :label-placement="labelPlacement"
          :label-width="labelWidth"
          :label-align="labelAlign"
          :size="size"
          :disabled="disabled"
          :require-mark-placement="requireMarkPlacement"
      >

          <n-form-item
              v-for="field in fields"
              :key="field.name"
              :label="field.label"
              :path="field.name"
              :show-label="field.showLabel"
              :label-style="field.labelStyle"
              :feedback="field.feedback"
          >
            <template v-if="field.type === 'radio'">
              <n-radio-group
                  v-model:value="localFormData[field.name]"
                  :name="field.name"
                  :disabled="field.disabled || props.disabled"
                  @update:value="handleFieldChange(field.name, $event)"
              >
                <n-space>
                  <n-radio
                      v-for="option in field.options"
                      :key="option.value"
                      :value="option.value"
                      :label="option.label"
                  />
                </n-space>
              </n-radio-group>
            </template>
            <!-- Upload 特殊处理 -->
<!--            <template v-else-if="field.type === 'upload'">
              <n-upload
                  v-bind="getFieldProps(field)"
                  :file-list="localFormData[field.name] || []"
                  @update:file-list="handleUploadChange(field.name, $event)"
              />
            </template>-->
            <component
                v-else
                :is="getComponent(field.type)"
                v-bind="getFieldProps(field)"
                v-model:value="formData[field.name]"
                @update:value="handleFieldChange(field.name, $event)"
            />

            <!-- 字段描述 -->
            <template v-if="field.description" #feedback>
              <div class="field-description">
                {{ field.description }}
              </div>
            </template>
          </n-form-item>

        <!-- 自定义表单内容 -->
        <slot name="default" :formData="localFormData" />
      </n-form>

      <!-- 对话框底部插槽 -->
      <slot name="footer" :formData="localFormData" />
    </div>

    <template #action v-if="$slots.action">
      <slot name="action" :formData="localFormData"/>
    </template>
  </n-modal>
</template>

<script setup>
import { ref, watch, computed, nextTick, h } from 'vue'
import {
  NModal,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NSelect,
  NDatePicker,
  NSwitch,
  NCheckbox,
  NRadioGroup,
  NRadio,
  NTimePicker,
  NCascader,
  NColorPicker,
  NUpload,
  NDynamicInput,
  NRate,
  NSlider,
  NH3,
  useMessage
} from 'naive-ui'

const message = useMessage()
const formRef = ref(null)

// 组件映射
const componentMap = {
  input: NInput,
  number: NInputNumber,
  select: NSelect,
  date: NDatePicker,
  datetime: NDatePicker,
  switch: NSwitch,
  textarea: NInput,
  checkbox: NCheckbox,
  radio: NRadioGroup,
  time: NTimePicker,
  cascader: NCascader,
  color: NColorPicker,
  upload: NUpload,
  dynamic: NDynamicInput,
  rate: NRate,
  slider: NSlider,
  custom: 'div' // 自定义组件占位
}

// Props
const props = defineProps({
  // 基础属性
  visible: Boolean,
  type: String,
  title: String,
  positiveText: {
    type: String,
    default: '确认'
  },
  negativeText: {
    type: String,
    default: '取消'
  },

  // 表单数据
  formData: {
    type: Object,
    default: () => ({})
  },

  // 字段配置
  fields: {
    type: Array,
    default: () => []
  },

  // 字段分组
  fieldGroups: {
    type: Array,
    default: () => []
  },

  // 使用分组模式
  useFieldGroups: {
    type: Boolean,
    default: false
  },

  // 验证规则
  rules: {
    type: Object,
    default: () => ({})
  },

  // 表单配置
  labelPlacement: {
    type: String,
    default: 'left'
  },
  labelWidth: {
    type: [String, Number],
    default: 'auto'
  },
  labelAlign: {
    type: String,
    default: 'left'
  },
  size: {
    type: String,
    default: 'medium'
  },
  disabled: Boolean,
  requireMarkPlacement: {
    type: String,
    default: 'right'
  },

  // 对话框配置
  dialogPreset: {
    type: String,
    default: 'dialog'
  },
  showIcon: {
    type: Boolean,
    default: true
  },
  maskClosable: {
    type: Boolean,
    default: true
  },
  closable: {
    type: Boolean,
    default: true
  },
  contentClass: String,

  // 提交配置
  validateOnSubmit: {
    type: Boolean,
    default: true
  },
  showSuccessMessage: {
    type: Boolean,
    default: false
  },
  successMessage: {
    type: String,
    default: '操作成功'
  },
  loading: Boolean
})

// Emits
const emit = defineEmits([
  'update:visible',
  'update:formData',
  'submit',
  'cancel',
  'close',
  'field-change',
  'validate'
])

// 计算属性
const visible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

const localFormData = ref({})

// 初始化
watch(() => props.formData, (newVal) => {
  localFormData.value = JSON.parse(JSON.stringify(newVal))
}, { immediate: true, deep: true })

// 深度克隆
const deepClone = (obj) => {
  if (obj === null || typeof obj !== 'object') return obj
  if (obj instanceof Date) return new Date(obj.getTime())
  if (obj instanceof Array) return obj.map(item => deepClone(item))
  if (typeof obj === 'object') {
    const cloned = {}
    Object.keys(obj).forEach(key => {
      cloned[key] = deepClone(obj[key])
    })
    return cloned
  }
  return obj
}

// 获取组件
const getComponent = (type) => {
  return componentMap[type] || NInput
}

// 获取字段属性
const getFieldProps = (field) => {
  const baseProps = {
    placeholder: field.placeholder || `请输入${field.label}`,
    clearable: field.clearable !== false,
    disabled: field.disabled || props.disabled,
    size: field.size || props.size
  }

  // 根据字段类型添加特定属性
  switch (field.type) {
    case 'input':
      return {
        ...baseProps,
        type: field.inputType || 'text',
        maxlength: field.maxlength,
        showCount: field.showCount,
        round: field.round
      }
    case 'number':
      return {
        ...baseProps,
        min: field.min,
        max: field.max,
        step: field.step || 1,
        precision: field.precision
      }
    case 'select':
      return {
        ...baseProps,
        options: field.options || [],
        filterable: field.filterable,
        multiple: field.multiple,
        tag: field.tag,
        maxTagCount: field.maxTagCount
      }
    case 'date':
      return {
        ...baseProps,
        type: 'date',
        valueFormat: field.valueFormat || 'yyyy-MM-dd',
        isDateDisabled: field.isDateDisabled
      }
    case 'datetime':
      return {
        ...baseProps,
        type: 'datetime',
        valueFormat: field.valueFormat || 'yyyy-MM-dd HH:mm:ss'
      }
    case 'textarea':
      return {
        ...baseProps,
        type: 'textarea',
        rows: field.rows || 3,//会被autosize覆盖
        autosize: field.autosize,
        maxlength: field.maxlength,
        showCount: field.showCount
      }
    case 'radio':
      return {
        ...baseProps,
        options: field.options || [],
        name: field.name
      }
    case 'upload':
      return {
        ...baseProps,
        action: field.action,
        multiple: field.multiple,
        accept: field.accept,
        listType: field.listType || 'text',
        max: field.max
      }
    default:
      return { ...baseProps, ...field.props }
  }
}

// 字段值变化
const handleFieldChange = (fieldName, value) => {
  emit('field-change', { fieldName, value, formData: localFormData.value })
}

// 提交表单
const handleSubmit = async () => {
  if (props.loading) return

  if (props.validateOnSubmit && formRef.value) {
    try {
      await formRef.value.validate((errors) => {
        emit('validate', errors)
        if (errors) {
          throw new Error('验证失败')
        }
      })

      emit('submit', localFormData.value)
      if (props.showSuccessMessage) {
        message.success(props.successMessage)
      }

      visible.value = false
    } catch (errors) {
      if (!errors) return
      message.error('请检查表单填写是否正确')
    }
  } else {
    emit('submit', localFormData.value)
    visible.value = false
  }
}
// 取消
const handleCancel = () => {
  emit('cancel')
  visible.value = false
  resetForm()
}

// 关闭
const handleClose = () => {
  emit('close')
  resetForm()
}

// 重置表单
const resetForm = () => {
  localFormData.value = deepClone(props.formData)
  nextTick(() => {
    formRef.value?.restoreValidation()
  })
}

// 暴露方法
defineExpose({
  // 表单方法
  validate: () => formRef.value?.validate(),
  restoreValidation: () => formRef.value?.restoreValidation(),
  scrollToField: (path, options) => formRef.value?.scrollToField(path, options),

  // 数据方法
  getFormData: () => deepClone(localFormData.value),
  setFormData: (data) => {
    localFormData.value = deepClone(data)
  },
  resetFormData: resetForm,

  // 字段方法
  getFieldValue: (fieldName) => localFormData.value[fieldName],
  setFieldValue: (fieldName, value) => {
    localFormData.value[fieldName] = value
  },

  // 对话框方法
  show: () => visible.value = true,
  hide: () => visible.value = false,
  toggle: () => visible.value = !visible.value
})
</script>

<style scoped>
.dialog-content {
  max-height: 70vh;
  overflow-y: auto;
  padding-right: 4px;
}

.field-group {
  margin-bottom: 32px;
  padding-bottom: 20px;
  border-bottom: 1px dashed #e5e5e5;
}

.field-group:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.field-description {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

/* 滚动条样式 */
.dialog-content::-webkit-scrollbar {
  width: 6px;
}

.dialog-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.dialog-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.dialog-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>

<!--
<template>
  <n-card title="12312">222</n-card>

  <n-modal
      v-model:show="visible"
      preset="dialog"
      :title="title"
      :positive-text="positiveText"
      :negative-text="negativeText"
      @positive-click="handleSubmit"
      @negative-click="handleCancel"
      @close="handleClose"
  >
    <n-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-placement="left"
        label-width="auto"
        :style="{ marginTop: '20px' }"
    >
      <n-form-item
          v-for="field in fields"
          :key="field.name"
          :label="field.label"
          :path="field.name"
      >
        &lt;!&ndash; 文本框 &ndash;&gt;
        <n-input
            v-if="field.type === 'input'"
            v-model:value="formData[field.name]"
            :placeholder="field.placeholder || `请输入${field.label}`"
            clearable
        />

        &lt;!&ndash; 数字输入框 &ndash;&gt;
        <n-input-number
            v-else-if="field.type === 'number'"
            v-model:value="formData[field.name]"
            :placeholder="field.placeholder"
            :min="field.min"
            :max="field.max"
            :step="field.step"
            clearable
        />

        &lt;!&ndash; 选择器 &ndash;&gt;
        <n-select
            v-else-if="field.type === 'select'"
            v-model:value="formData[field.name]"
            :options="field.options"
            :placeholder="field.placeholder || `请选择${field.label}`"
            clearable
            filterable
        />

        &lt;!&ndash; 日期选择 &ndash;&gt;
        <n-date-picker
            v-else-if="field.type === 'date'"
            v-model:value="formData[field.name]"
            type="date"
            :placeholder="field.placeholder || `请选择${field.label}`"
            clearable
        />

        &lt;!&ndash; 开关 &ndash;&gt;
        <n-switch
            v-else-if="field.type === 'switch'"
            v-model:value="formData[field.name]"
            :checked-value="field.checkedValue ?? true"
            :unchecked-value="field.uncheckedValue ?? false"
        />

        &lt;!&ndash; 多行文本 &ndash;&gt;
        <n-input
            v-else-if="field.type === 'textarea'"
            v-model:value="formData[field.name]"
            type="textarea"
            :placeholder="field.placeholder || `请输入${field.label}`"
            :rows="field.rows || 3"
            clearable
        />

        &lt;!&ndash; 自定义插槽 &ndash;&gt;
        <slot
            v-else-if="field.type === 'custom'"
            :name="field.slotName"
            :field="field"
            :formData="formData"
        />
      </n-form-item>
    </n-form>
  </n-modal>
</template>

<script setup>
import { ref, watch, computed, nextTick } from 'vue'
import {
  NModal,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NSelect,
  NDatePicker,
  NSwitch,
  useMessage
} from 'naive-ui'

const message = useMessage()
const formRef = ref(null)

// Props
const props = defineProps({
  // 对话框显示控制
  visible: {
    type: Boolean,
    default: false
  },
  // 标题
  title: {
    type: String,
    default: '表单'
  },
  // 确认按钮文本
  positiveText: {
    type: String,
    default: '确认'
  },
  // 取消按钮文本
  negativeText: {
    type: String,
    default: '取消'
  },
  // 表单字段配置
  fields: {
    type: Array,
    default: () => []
  },
  // 表单数据
  formData: {
    type: Object,
    default: () => ({})
  },
  // 验证规则
  rules: {
    type: Object,
    default: () => ({})
  },
  // 是否在提交时验证
  validateOnSubmit: {
    type: Boolean,
    default: true
  }
})

// Emits
const emit = defineEmits([
  'update:visible',
  'update:formData',
  'submit',
  'cancel',
  'close'
])

// 对话框显示状态
const visible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

// 本地表单数据（深度拷贝，避免直接修改props）
const localFormData = ref({})

// 初始化表单数据
watch(() => props.formData, (newVal) => {
  localFormData.value = JSON.parse(JSON.stringify(newVal))
}, { immediate: true, deep: true })

// 提交表单
const handleSubmit = async () => {
  if (props.validateOnSubmit && formRef.value) {
    try {
      await formRef.value.validate()
      emit('submit', localFormData.value)
      emit('update:formData', localFormData.value)
      visible.value = false
    } catch (errors) {
      message.error('请检查表单填写是否正确')
    }
  } else {
    emit('submit', localFormData.value)
    emit('update:formData', localFormData.value)
    visible.value = false
  }
}

// 取消
const handleCancel = () => {
  emit('cancel')
  visible.value = false
}

// 关闭
const handleClose = () => {
  emit('close')
}

// 暴露方法给父组件
defineExpose({
  validate: () => formRef.value?.validate(),
  restoreValidation: () => formRef.value?.restoreValidation(),
  getFormData: () => localFormData.value,
  resetFormData: () => {
    localFormData.value = JSON.parse(JSON.stringify(props.formData))
    formRef.value?.restoreValidation()
  }
})
</script>

<style scoped>
/* 自定义样式 */
:deep(.n-dialog) {
  width: 600px;
  max-width: 90vw;
}

:deep(.n-form-item) {
  margin-bottom: 24px;
}
</style>
-->
