import { useRouter ,createRouter, createWebHistory } from 'vue-router'
import NoteList from '../modules/note/NoteList.vue'
import NodeManager from '../modules/cron/NodeManager.vue'
import JobManager from '../modules/cron/JobManager.vue'
import DatabaseManager from '../modules/database/DatabaseManager.vue'
import VersionManager from '../modules/version/VersionManager.vue'
import NotificationSettings from '../modules/notify/NotificationSettings.vue'
import DialogFormEx from '../modules/example/DialogFormEx.vue'
import SysPage from '../modules/sys/SysPage.vue'
import {
    AccessibilityOutline as AboutIcon,
    AlarmOutline as ClockIcon, ChatbubbleEllipsesOutline as NotifyIcon,
    ReaderOutline as NoteIcon,
    ServerOutline as DatabaseIcon,
    TvOutline as PCIcon,
    ApertureOutline as VersionIcon,
    BulbOutline as ExampleIcon,
} from "@vicons/ionicons5";

const routes = [
    { path: '/', component: NoteList },
    { path: '/nodes', component: NodeManager },
    { path: '/jobs', component: JobManager },
    { path: '/notify', component: NotificationSettings },
    { path: '/database', component: DatabaseManager },
    { path: '/versions', component: VersionManager },
    { path: '/sys', component: SysPage },
    { path: '/example', component: DialogFormEx },
]

const routeLabels = [
    { path: '/', label: '便签管理', icon: NoteIcon, key: 'notes' },
    { path: '/nodes', label: '节点管理', icon: PCIcon, key: 'nodes' },
    { path: '/jobs', label: '任务管理', icon: ClockIcon, key: 'jobs' },
    { path: '/notify', label: '消息通知', icon: NotifyIcon, key: 'notify' },
    { path: '/database', label: '数据管理', icon: DatabaseIcon, key: 'database' },
    { path: '/versions', label: '系统版本', icon: VersionIcon, key: 'versions' },
    { path: '/sys', label: '个人', icon: AboutIcon, key: 'sys' },
    { path: '/example', label: '示例', icon: ExampleIcon, key: 'example' },
];

export default createRouter({
    history: createWebHistory(),
    routes,
})
export { routeLabels }
