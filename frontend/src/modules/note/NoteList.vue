<template>
  <n-card title="📝 我的便签" class="max-w-3xl mx-auto">
    <n-space justify="start" style="margin-bottom: 10px">
      <n-input v-model:value="searchTitle" class="titleSearch" placeholder="输入标题搜索" />
      <n-button type="primary" @click="searchTitleOp">搜索</n-button>
      <n-button type="default" @click="searchTitle='';searchTitleOp()">重置</n-button>
    </n-space>
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
             class=" mediaModal"
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
                  minRows: 10,
                  maxRows: 18,
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
    <n-space v-if="notes.length === 0" >
      暂无便签，快添加一条吧！
    </n-space>
    <n-list v-else style="height: 70vh;overflow-y: auto;">
      <n-list-item v-for="note in notes" :key="note.id" class="mb-3">
        <n-card hoverable size="small" :title="'标题：'+note.title" :bordered="false" class="shadow-sm"
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
              readonly
              :autosize="{
                  minRows: 3,
                  maxRows: 18,
                }"
          />
        </n-card>
      </n-list-item>
    </n-list>
  </n-card>
</template>

<script setup>
import {ref, onMounted, computed} from 'vue'

const notes = ref([])
const currentNote = ref({ id: null, title: '', content: '' })
const isEditing = ref(false)
const showForm = ref(false)
const title = ref('我的便签')
const searchTitle = ref('')

const loadNotes = async () => {
  try {
    const res = await window.$request.get('/notes')
    notes.value = res
  } catch (error) {
    window.$message.error('加载便签失败')
  }
}

const searchTitleOp = async () => {
  try {
    if (searchTitle.value){
      const res = await window.$request.get(`/notes/${searchTitle.value}`)
      notes.value = res
    }else{
      await loadNotes()
    }
  } catch (error) {
    window.$message.error('加载便签失败')
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
    window.$message.warning('标题和内容不能为空')
    return
  }

  try {

    if (isEditing.value) {
      // 更新便签
      await window.$request.put(`/notes/${currentNote.value.id}`, {
        title: currentNote.value.title,
        content: currentNote.value.content
      })
      window.$message.success('便签更新成功')
    } else {
      // 新增便签
      await window.$request.post('/notes', {
        title: currentNote.value.title,
        content: currentNote.value.content
      })
      window.$message.success('便签添加成功')
    }
    resetForm(true)
    loadNotes()
  } catch (error) {
    window.$message.error(isEditing.value ? '更新便签失败' : '添加便签失败')
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
    await window.$request.delete(`/notes/${id}`)
    window.$message.success('便签删除成功')
    loadNotes()
  } catch (error) {
    window.$message.error('删除便签失败')
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
    await window.$request.post('/notes/deleteBatch', { note_ids: selectedNoteIds.value })
    window.$message.success(`成功删除 ${selectedNoteIds.value.length} 个节点`)
    cancelBatch()
    await loadNotes()
  } catch (error) {
    window.$message.error('批量删除失败')
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


<style scoped>
.titleSearch{
  width: 253px
}
@media (max-width: 1000px) {
  .titleSearch {
    width: 130px
  }
}
</style>
