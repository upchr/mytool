<template>
  <div style="padding: 20px; max-width: 800px; margin: auto; font-family: Arial">
    <h1>📝 我的便签</h1>
    <form @submit.prevent="addNote" style="margin-bottom: 20px;">
      <input v-model="newNote.title" placeholder="标题" required
             style="width:100%; padding:8px; margin-bottom:8px;" />
      <textarea v-model="newNote.content" placeholder="内容..." required
                style="width:100%; height:100px; padding:8px;"></textarea>
      <button type="submit" style="margin-top:8px; padding:6px 12px;">添加</button>
    </form>

    <div v-for="note in notes" :key="note.id"
         style="border:1px solid #ddd; padding:12px; margin-bottom:12px; border-radius:4px;">
      <h3>{{ note.title }}</h3>
      <p>{{ note.content }}</p>
      <button @click="deleteNote(note.id)"
              style="background:#ff4444; color:white; border:none; padding:4px 8px; border-radius:3px;">
        删除
      </button>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  data() {
    return {
      notes: [],
      newNote: { title: '', content: '' }
    }
  },
  async mounted() {
    await this.loadNotes()
  },
  methods: {
    async loadNotes() {
      const res = await axios.get('/api/notes')
      this.notes = res.data
    },
    async addNote() {
      await axios.post('/api/notes', this.newNote)
      this.newNote = { title: '', content: '' }
      await this.loadNotes()
    },
    async deleteNote(id) {
      await axios.delete(`/api/notes/${id}`)
      await this.loadNotes()
    }
  }
}
</script>
