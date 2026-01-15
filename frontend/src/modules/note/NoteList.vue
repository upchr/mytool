<template>
  <n-card title="📝 我的便签" class="max-w-3xl mx-auto">
    <!-- 添加/编辑表单 -->
    <n-form :model="currentNote" label-placement="left" label-width="auto">
      <n-form-item path="title" label="标题">
        <n-input v-model:value="currentNote.title" placeholder="请输入标题" />
      </n-form-item>
      <n-form-item path="content" label="内容">
        <n-input
            v-model:value="currentNote.content"
            type="textarea"
            placeholder="请输入内容..."
            :rows="4"
        />
      </n-form-item>
      <n-space justify="end">
        <n-button @click="resetForm">取消</n-button>
        <n-button type="primary" @click="saveNote">
          {{ isEditing ? '更新便签' : '添加便签' }}
        </n-button>
      </n-space>
    </n-form>

    <n-divider />

    <!-- 便签列表 -->
    <div v-if="notes.length === 0" class="text-center py-8 text-gray-500">
      暂无便签，快添加一条吧！
    </div>

    <n-list v-else style="height: 60vh;overflow-y: auto;">
      <n-list-item v-for="note in notes" :key="note.id" class="mb-3">
        <n-card :bordered="false" size="small" class="shadow-sm">
          <template #header>
            <h3 class="font-bold text-lg">{{ note.title }}</h3>
          </template>
          <p>{{ note.content }}</p>
          <template #footer>
            <div class="flex justify-end space-x-2">
              <n-space>

              <n-button size="small" type="info"  @click="editNote(note)">
                编辑
              </n-button>
              <n-popconfirm
                  @positive-click="deleteNote(note.id)"
                  negative-text="取消"
                  positive-text="确定"
              >
                <template #trigger>
                  <n-button size="small" type="error" >删除</n-button>
                </template>
                确定要删除便签 "{{ note.title }}" 吗？
              </n-popconfirm>
              </n-space>
            </div>
          </template>
        </n-card>
      </n-list-item>
    </n-list>
  </n-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useMessage } from 'naive-ui'

const message = useMessage()
const notes = ref([])
const currentNote = ref({ id: null, title: '', content: '' })
const isEditing = ref(false)

const loadNotes = async () => {
  try {
    const res = await axios.get('/api/notes')
    notes.value = res.data
  } catch (error) {
    message.error('加载便签失败')
  }
}

const resetForm = () => {
  currentNote.value = { id: null, title: '', content: '' }
  isEditing.value = false
}

const saveNote = async () => {
  if (!currentNote.value.title.trim() || !currentNote.value.content.trim()) {
    message.warning('标题和内容不能为空')
    return
  }

  try {
    if (isEditing.value) {
      // 更新便签
      await axios.put(`/api/notes/${currentNote.value.id}`, {
        title: currentNote.value.title,
        content: currentNote.value.content
      })
      message.success('便签更新成功')
    } else {
      // 新增便签
      await axios.post('/api/notes', {
        title: currentNote.value.title,
        content: currentNote.value.content
      })
      message.success('便签添加成功')
    }
    resetForm()
    loadNotes()
  } catch (error) {
    message.error(isEditing.value ? '更新便签失败' : '添加便签失败')
  }
}

const editNote = (note) => {
  currentNote.value = {...note}
  isEditing.value = true
}

const deleteNote = async (id) => {
  try {
    await axios.delete(`/api/notes/${id}`)
    message.success('便签删除成功')
    loadNotes()
  } catch (error) {
    message.error('删除便签失败')
  }
}

onMounted(loadNotes)
</script>
