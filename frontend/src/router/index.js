import { createRouter, createWebHistory } from 'vue-router'
import NoteList from '../modules/note/NoteList.vue'
import NodeManager from '../modules/cron/NodeManager.vue'
import JobManager from '../modules/cron/JobManager.vue'

const routes = [
    { path: '/', component: NoteList },
    { path: '/nodes', component: NodeManager },
    { path: '/jobs', component: JobManager },
]

export default createRouter({
    history: createWebHistory(),
    routes
})
