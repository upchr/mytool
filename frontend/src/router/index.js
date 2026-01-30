import { useRouter ,createRouter, createWebHistory } from 'vue-router'
import NoteList from '../modules/note/NoteList.vue'
import NodeManager from '../modules/cron/NodeManager.vue'
import JobManager from '../modules/cron/JobManager.vue'
import DatabaseManager from '../modules/database/DatabaseManager.vue'
import VersionManager from '../modules/version/VersionManager.vue'
import NotificationSettings from '../modules/notify/NotificationSettings.vue'
import DialogFormEx from '../modules/example/DialogFormEx.vue'
import {
    AccessibilityOutline as AboutIcon,
    AlarmOutline as ClockIcon, ChatbubbleEllipsesOutline as NotifyIcon,
    ReaderOutline as NoteIcon,
    ServerOutline as DatabaseIcon,
    TvOutline as PCIcon
} from "@vicons/ionicons5";

const routes = [
    { path: '/', component: NoteList },
    { path: '/nodes', component: NodeManager },
    { path: '/jobs', component: JobManager },
    { path: '/database', component: DatabaseManager },
    { path: '/notify', component: NotificationSettings },
    { path: '/versions', component: VersionManager },
    { path: '/example', component: DialogFormEx },
]

const routeLabels = [
    { path: '/', label: '便签管理', icon: NoteIcon, key: 'notes' },
    { path: '/nodes', label: '节点管理', icon: PCIcon, key: 'nodes' },
    { path: '/jobs', label: '任务管理', icon: ClockIcon, key: 'jobs' },
    { path: '/database', label: '数据管理', icon: DatabaseIcon, key: 'database' },
    { path: '/notify', label: '消息通知', icon: NotifyIcon, key: 'notify' },
    { path: '/versions', label: '关于', icon: AboutIcon, key: 'versions' },
    { path: '/example', label: 'example', icon: AboutIcon, key: 'example' },
];

export default createRouter({
    history: createWebHistory(),
    routes,
})
export { routeLabels }
