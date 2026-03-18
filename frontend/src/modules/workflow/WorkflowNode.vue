<template>
  <div class="workflow-node" :class="[`node-${type}`, { selected: selected }]">
    <div class="node-header">
      <span class="node-icon">{{ nodeIcon }}</span>
      <span class="node-title">{{ data.label || '节点' }}</span>
    </div>
    
    <div class="node-type">{{ nodeTypeLabel }}</div>
    
    <div class="node-actions" v-show="selected">
      <n-button size="tiny" quaternary @click.stop="$emit('edit')">
        <template #icon><n-icon><CreateOutline /></n-icon></template>
      </n-button>
      <n-button size="tiny" quaternary type="error" @click.stop="$emit('delete')">
        <template #icon><n-icon><TrashOutline /></n-icon></template>
      </n-button>
    </div>
    
    <Handle type="target" :position="Position.Left" class="handle" />
    <Handle type="source" :position="Position.Right" class="handle" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Handle, Position } from '@vue-flow/core'
import { CreateOutline, TrashOutline } from '@vicons/ionicons5'

const props = defineProps({
  id: String,
  data: { type: Object, default: () => ({}) },
  type: { type: String, default: 'task' },
  selected: { type: Boolean, default: false }
})

defineEmits(['edit', 'delete'])

const nodeIcon = computed(() => {
  const icons = { task: '⚙️', condition: '🔷', wait: '⏱️', notification: '📢' }
  return icons[props.type] || '📦'
})

const nodeTypeLabel = computed(() => {
  const labels = { task: '执行任务', condition: '条件判断', wait: '等待', notification: '发送通知' }
  return labels[props.type] || '节点'
})
</script>

<style scoped>
.workflow-node {
  min-width: 160px;
  background: #fff;
  border: 2px solid #e0e0e0;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  position: relative;
  transition: all 0.2s;
}

.workflow-node:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.workflow-node.node-task { border-color: #2080f0; }
.workflow-node.node-condition { border-color: #f0a020; }
.workflow-node.node-wait { border-color: #8a8a8a; }
.workflow-node.node-notification { border-color: #722ed1; }

.workflow-node.selected {
  box-shadow: 0 0 0 3px rgba(24, 160, 88, 0.3);
}

.node-header {
  padding: 10px 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.node-icon {
  font-size: 18px;
}

.node-title {
  font-weight: 500;
  font-size: 13px;
}

.node-type {
  padding: 6px 12px;
  font-size: 11px;
  color: #999;
}

.node-actions {
  position: absolute;
  top: -8px;
  right: -8px;
  display: flex;
  gap: 2px;
  background: #fff;
  padding: 2px;
  border-radius: 6px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.15);
}

.handle {
  width: 12px !important;
  height: 12px !important;
  background: #18a058 !important;
  border: 2px solid #fff !important;
}
</style>
