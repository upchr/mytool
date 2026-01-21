import { createRouter, createWebHistory } from 'vue-router'
import NoteList from '../modules/note/NoteList.vue'
import NodeManager from '../modules/cron/NodeManager.vue'
import JobManager from '../modules/cron/JobManager.vue'
import DatabaseManager from '../modules/database/DatabaseManager.vue'

const routes = [
    { path: '/', component: NoteList },
    { path: '/nodes', component: NodeManager },
    { path: '/jobs', component: JobManager },
    { path: '/database', component: DatabaseManager },
]

export default createRouter({
    history: createWebHistory(),
    routes
})
