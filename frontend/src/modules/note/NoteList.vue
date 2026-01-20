<template>
  <n-card title="📝 我的便签" class="max-w-3xl mx-auto">
    <!--    按钮操作-->
    <n-space justify="end" style="margin-bottom: 10px">
      <n-button v-if="!isBatchMode" @click="enterBatchMode">批量操作</n-button>
      <n-button type="primary" @click="showForm=true;isBatchMode=false;resetForm()">添加便签</n-button>
    </n-space>
    <n-divider />

    <!--    批量操作-->
    <n-space justify="end" class="mt-4" style="margin-top: 10px">
      <div v-if="isBatchMode" class="mb-4 flex justify-between items-center bg-gray-50 p-3 rounded">
        <n-space justify="end" >已选择 {{ selectedNoteIds.length }} 个节点</n-space>
        <n-space style="margin-top: 5px">
          <n-button  size="small" type="info" @click="toggleAllNotesAdd"
          >
            {{ allNotesSelectedAdd ? '取消全选' : '全选' }}
          </n-button>
          <n-popconfirm
              @positive-click="batchDeleteNotes"
              negative-text="取消"
              positive-text="确定删除"
          >
            <template #trigger>
              <n-button size="small" type="error">批量删除</n-button>
            </template>
            确定要删除选中的 {{ selectedNoteIds.length }} 个节点吗？
          </n-popconfirm>
          <n-button size="small" @click="cancelBatch">取消</n-button>
        </n-space>
        <n-divider />
      </div>
    </n-space>

    <!-- 添加/编辑表单 -->
    <n-modal v-model:show="showForm"
             preset="card"
             :title="'📝 '+title"
             style="width: auto;height: auto;min-width: 30vw"
             :on-after-leave="()=>resetForm(true)">
      <n-form :model="currentNote" label-placement="left" label-width="auto" >
        <n-form-item path="title" label="标题">
          <n-input v-model:value="currentNote.title" placeholder="请输入标题" />
        </n-form-item>
        <n-form-item path="content" label="内容">
          <n-input
              v-model:value="currentNote.content"
              type="textarea"
              placeholder="请输入内容..."
              :autosize="{
                  minRows: 6,
                  maxRows: 10,
                }"
          />
        </n-form-item>
        <n-space justify="end">
          <n-button type="primary" @click="saveNote">
            {{ isEditing ? '更新便签' : '添加便签' }}
          </n-button>
          <n-button type="warning" @click="resetForm()">重置</n-button>
        </n-space>
      </n-form>
    </n-modal>

    <!-- 便签列表 -->
    <div v-if="notes.length === 0" class="text-center py-8 text-gray-500">
      暂无便签，快添加一条吧！
    </div>

    <n-list v-else style="height: 60vh;overflow-y: auto;">
      <n-list-item v-for="note in notes" :key="note.id" class="mb-3">
        <n-card hoverable size="small" :title="'标题：'+note.title" :bordered="false" class="shadow-sm"
                :style="isBatchMode && selectedNoteIds.includes(note.id) ? { backgroundColor: 'lightgray'}: {backgroundColor: 'whitesmoke'}"
                @click="handleCardClick(note)">
          <template #header-extra>
            <n-checkbox
                v-if="isBatchMode"
                :checked="selectedNoteIds.includes(note.id)"
                @click.stop.prevent="(e) => toggleNoteSelection(note.id, !selectedNoteIds.includes(note.id))"
            />
          </template>
          <template #action>
            <n-space v-if="!isBatchMode" justify="end">
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
          </template>
          <n-input
              v-model:value="note.content"
              type="textarea"
              :disabled="true"
              style="background-color: white;"
              :autosize="{
                  minRows: 3,
                  maxRows: 10,
                }"
          />
        </n-card>
      </n-list-item>
    </n-list>
  </n-card>
</template>

<script setup>
import {ref, onMounted, computed} from 'vue'
import axios from 'axios'
import { useMessage } from 'naive-ui'

const message = useMessage()
const notes = ref([])
const currentNote = ref({ id: null, title: '', content: '' })
const isEditing = ref(false)
const showForm = ref(false)
const title = ref('我的便签')

const loadNotes = async () => {
  try {
    const res = await axios.get('/api/notes')
    notes.value = res.data
  } catch (error) {
    message.error('加载便签失败')
  }
}
const resetForm = (afterFlag=false) => {
  if(afterFlag){
    showForm.value=false
    isEditing.value = false
    title.value = '我的便签'
  }

  currentNote.value = {
    ...currentNote.value,
    title: '',
    content: ''
  }

  if (!isEditing){
    currentNote.value.id = null
  }
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
    resetForm(true)
    loadNotes()
  } catch (error) {
    message.error(isEditing.value ? '更新便签失败' : '添加便签失败')
  }
}

const editNote = (note) => {
  currentNote.value = {...note}
  isEditing.value = true
  showForm.value = true
  title.value = `修改：${currentNote.value.title}`
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


//批量删除
const selectedNoteIds = ref([]) // 批量选择的节点ID
const isBatchMode = ref(false)  // 批量模式开关
// 批量操作方法
const enterBatchMode = () => {
  isBatchMode.value = true
  selectedNoteIds.value = []
}

const cancelBatch = () => {
  isBatchMode.value = false
  selectedNoteIds.value = []
}

const toggleNoteSelection = (noteId, checked) => {
  if (checked) {
    selectedNoteIds.value.push(noteId)
  } else {
    selectedNoteIds.value = selectedNoteIds.value.filter(id => id !== noteId)
  }
}

const batchDeleteNotes = async () => {
  if (selectedNoteIds.value.length === 0) return

  try {
    await axios.post('/api/notes/deleteBatch', { note_ids: selectedNoteIds.value })
    message.success(`成功删除 ${selectedNoteIds.value.length} 个节点`)
    cancelBatch()
    await loadNotes()
  } catch (error) {
    message.error('批量删除失败')
  }
}
// 处理卡片点击（仅在批量模式下生效）
const handleCardClick = (note) => {
  if (!isBatchMode.value) return

  const isChecked = selectedNoteIds.value.includes(note.id)
  toggleNoteSelection(note.id, !isChecked)
}

const allNotesSelectedAdd = computed(() => {
  const activeNotes = notes.value
  return (
      activeNotes.length > 0 &&
      selectedNoteIds.value.length === activeNotes.length &&
      activeNotes.every(note => selectedNoteIds.value.includes(note.id))
  )
})

// 全选/取消全选
const toggleAllNotesAdd = () => {
  if (allNotesSelectedAdd.value) {
    selectedNoteIds.value = []
  } else {
    // 只选择活跃节点
    selectedNoteIds.value = notes.value
        .map(n => n.id)
  }
}


onMounted(loadNotes)
</script>
