<template>
  <div class="workflow-node" :class="[typeClass, { selected: isSelected }]">
    <div class="node-header">
      <n-icon :component="nodeIcon" :size="16" />
      <span class="node-title">{{ data.name || '节点' }}</span>
    </div>
    
    <div class="node-body">
      <span class="node-type-label">{{ typeLabel }}</span>
    </div>
    
    <div class="node-actions" v-if="isSelected">
      <n-button
        size="tiny"
        quaternary
        @click.stop="$emit('config')"
      >
        <template #icon>
          <ion-icon :icon="settingsOutline" />
        </template>
      </n-button>
      <n-button
        size="tiny"
        quaternary
        type="error"
        @click.stop="$emit('delete')"
      >
        <template #icon>
          <ion-icon :icon="trashOutline" />
        </template>
      </n-button>
    </div>
    
    <Handle type="target" :position="Position.Left" class="handle" />
    <Handle type="source" :position="Position.Right" class="handle" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Handle, Position } from '@vue-flow/core'
import {
  settingsOutline,
  trashOutline,
  constructOutline,
  gitCompareOutline,
  hourglassOutline,
  notificationsOutline
} from '@vicons/ionicons5'

const props = defineProps({
  data: {
    type: Object,
    default: () => ({})
  },
  id: {
    type: String,
    required: true
  },
  type: {
    type: String,
    default: 'task'
  },
  selected: {
    type: Boolean,
    default: false
  }
})

defineEmits(['delete', 'config'])

const nodeIcon = computed(() => {
  switch (props.type) {
    case 'task':
      return constructOutline
    case 'condition':
      return gitCompareOutline
    case 'wait':
      return hourglassOutline
    case 'notification':
      return notificationsOutline
    default:
      return constructOutline
  }
})

const typeLabel = computed(() => {
  switch (props.type) {
    case 'task':
      return '任务'
    case 'condition':
      return '条件'
    case 'wait':
      return '等待'
    case 'notification':
      return '通知'
    default:
      return '节点'
  }
})

const typeClass = computed(() => `node-${props.type}`)

const isSelected = computed(() => props.selected)
</script>

<style scoped>
.workflow-node {
  min-width: 160px;
  background: #fff;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: relative;
  transition: all 0.2s;
}

.workflow-node:hover {
  border-color: #18a058;
  box-shadow: 0 4px 12px rgba(24, 160, 88, 0.2);
}

.workflow-node.node-task {
  border-color: #2080f0;
}

.workflow-node.node-condition {
  border-color: #f0a020;
}

.workflow-node.node-wait {
  border-color: #8a8a8a;
}

.workflow-node.node-notification {
  border-color: #722ed1;
}

.workflow-node.selected {
  border-color: #18a058 !important;
  box-shadow: 0 0 0 3px rgba(24, 160, 88, 0.2);
}

.node-header {
  padding: 8px 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
  border-bottom: 1px solid #f0f0f0;
}

.node-title {
  font-size: 14px;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.node-body {
  padding: 8px 12px;
}

.node-type-label {
  font-size: 12px;
  color: #8a8a8a;
}

.node-actions {
  position: absolute;
  top: -12px;
  right: -12px;
  display: flex;
  gap: 4px;
  background: #fff;
  padding: 2px;
  border-radius: 6px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

.handle {
  width: 10px;
  height: 10px;
  background: #18a058;
  border: 2px solid #fff;
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.1);
}
</style>