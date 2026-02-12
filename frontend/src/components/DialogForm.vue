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
          :rules="computedRules"
          :label-placement="labelPlacement"
          :label-width="labelWidth"
          :label-align="labelAlign"
          :size="size"
          :disabled="disabled"
          :require-mark-placement="requireMarkPlacement"
      >
        <!-- 分组模式 -->
        <template v-if="props.useFieldGroups">
          <div
              v-for="(group, groupIndex) in props.fieldGroups"
              :key="groupIndex"
              v-show="group.visible !== false"
              class="field-group"
          >
            <!-- 组标题 -->
            <NH3 v-if="group.title" style="margin: 0 0 16px 0; font-size: 16px">
              {{ group.title }}
            </NH3>

            <!-- 组描述 -->
            <p v-if="group.description" style="margin: 0 0 16px 0; color: #666; font-size: 13px">
              {{ group.description }}
            </p>

            <!-- 组内字段 -->
            <n-form-item
                v-for="field in group.fields"
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
              <template v-else-if="field.type === 'checkbox'">
                <n-checkbox-group
                    v-model:value="localFormData[field.name]"
                    :name="field.name"
                    :disabled="field.disabled || props.disabled"
                    @update:value="handleFieldChange(field.name, $event)"
                >
                  <n-space>
                    <n-checkbox
                        v-for="option in field.options"
                        :key="option.value"
                        :value="option.value"
                        :label="option.label"
                    />
                  </n-space>
                </n-checkbox-group>
              </template>
              <template v-else-if="field.type === 'upload'">
                <n-upload
                    v-bind="getFieldProps(field)"
                    :file-list="localFormData[field.name] || []"
                    @update:file-list="handleUploadChange(field.name, $event)"
                />
              </template>
              <component
                  v-else
                  :is="getComponent(field.type)"
                  v-bind="getFieldProps(field)"
                  v-model:value="localFormData[field.name]"
                  @update:value="handleFieldChange(field.name, $event)"
              />

              <template v-if="field.description" #feedback>
                <div class="field-description">{{ field.description }}</div>
              </template>
            </n-form-item>
          </div>
        </template>

        <!-- 平铺模式（默认） -->
        <template v-else>
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
            <template v-else-if="field.type === 'checkbox'">
              <n-checkbox-group
                  v-model:value="localFormData[field.name]"
                  :name="field.name"
                  :disabled="field.disabled || props.disabled"
                  @update:value="handleFieldChange(field.name, $event)"
              >
                <n-space>
                  <n-checkbox
                      v-for="option in field.options"
                      :key="option.value"
                      :value="option.value"
                      :label="option.label"
                  />
                </n-space>
              </n-checkbox-group>
            </template>
            <!-- Upload 特殊处理 -->
            <template v-else-if="field.type === 'upload'">
              <n-upload
                  v-bind="getFieldProps(field)"
                  :file-list="localFormData[field.name] || []"
                  @update:file-list="handleUploadChange(field.name, $event)"
              />
            </template>
            <component
                v-else
                :is="getComponent(field.type)"
                v-bind="getFieldProps(field)"
                v-model:value="localFormData[field.name]"
                @update:value="handleFieldChange(field.name, $event)"
            />

            <!-- 字段描述 -->
            <template v-if="field.description" #feedback>
              <div class="field-description">
                {{ field.description }}
              </div>
            </template>
          </n-form-item>
        </template>
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
} from 'naive-ui'

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
  // checkbox: NCheckbox,
  // radio: NRadioGroup,
  time: NTimePicker,
  cascader: NCascader,
  color: NColorPicker,
  // upload: NUpload,
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
    type:  [Object, Function],
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
    case 'checkbox':
      return {
        ...baseProps,
        options: field.options || [],
        name: field.name
      }
    case 'upload':
      return {
        ...baseProps,
        action: field.action||'',
        multiple: field.multiple,
        accept: field.accept,
        listType: field.listType || 'text',
        max: field.max||1,
        showPreviewButton: field.showPreviewButton || true,
      }
    default:
      return { ...baseProps, ...field.props }
  }
}

// 字段值变化
const handleFieldChange = (fieldName, value) => {
  emit('field-change', { fieldName, value, formData: localFormData.value })
}
const handleUploadChange = (fieldName, fileList) => {
  localFormData.value[fieldName] = fileList
  emit('field-change', {
    fieldName,
    value: fileList,
    formData: localFormData.value
  })
}

// 表单校验，支持从localFormData复杂验证。或基础验证
const computedRules = computed(() => {
  if (typeof props.rules === 'function') {
    return props.rules(localFormData.value)
  }
  return props.rules
})


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
        window.$message.success(props.successMessage)
      }

      visible.value = false
    } catch (errors) {
      if (!errors) return
      window.$message.error('请检查表单填写是否正确')
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
  validate: () => formRef.value?.validate(),//card自定义action，验证表单
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
