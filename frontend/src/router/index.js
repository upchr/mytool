import { useRouter ,createRouter, createWebHistory } from 'vue-router'
import NoteList from '../modules/note/NoteList.vue'
import NodeManager from '../modules/node/NodeManager.vue'
import JobManager from '../modules/cron/JobManager.vue'
import DatabaseManager from '../modules/database/DatabaseManager.vue'
import VersionManager from '../modules/version/VersionManager.vue'
import NotificationSettings from '../modules/notify/NotificationSettings.vue'
import DialogFormEx from '../modules/example/DialogFormEx.vue'
import SysPage from '../modules/sys/SysPage.vue'
import SSLDns from '../modules/ssl/DNS.vue'
import SSLApply from '../modules/ssl/apply/Applications.vue'
import SSLStore from '../modules/ssl/store/Store.vue'
import SSLDetail from '../modules/ssl/store/CertificateDetail.vue'
import AIChat from '../modules/ai-chat/AIChat_with_history.vue'
import AIConfig from '../modules/ai-chat/AIConfig.vue'
import KnowledgeBase from '../modules/ai-chat/KnowledgeBase.vue'
import WorkflowManager from '../modules/workflow/WorkflowManager.vue'
import WorkflowExecutionLog from '../modules/workflow/WorkflowExecutionLog.vue'
import AssetList from '../modules/asset/AssetList.vue'
import CPEManager from '../modules/cpe/CPEManager.vue'

import {
    AccessibilityOutline as AboutIcon,
    AlarmOutline as ClockIcon,
    ChatbubbleEllipsesOutline as NotifyIcon,
    ReaderOutline as NoteIcon,
    ServerOutline as DatabaseIcon,
    TvOutline as PCIcon,
    ApertureOutline as VersionIcon,
    BulbOutline as ExampleIcon,
    LockClosedOutline as SSLIcon,
    CreateOutline as SSLApplyIcon,
    List as SSLListIcon,
    BusinessOutline as SSLDNSIcon,
    EyeOutline as SSLMiIcon,
    SettingsOutline as ConfigIcon,
    SparklesOutline as AiIcon,
    GitBranchOutline as WorkflowIcon,
    BookOutline as KnowledgeIcon,
    DiamondOutline as AssetIcon,
    WifiOutline as CPEIcon,
    CubeOutline as DockerIcon,
} from "@vicons/ionicons5";

const routes = [
    { path: '/', component: NoteList },
    { path: '/nodes', component: NodeManager },
    { path: '/jobs', component: JobManager },
    { path: '/workflows', component: WorkflowManager },
    { path: '/workflow-execution-log', component: WorkflowExecutionLog },
    { path: '/notify', component: NotificationSettings },
    { path: '/database', component: DatabaseManager },
    { path: '/versions', component: VersionManager },
    { path: '/sys', component: SysPage },
    { path: '/example', component: DialogFormEx },
    { path: '/ai-chat', component: AIChat },
    { path: '/ai-config', component: AIConfig },
    { path: '/ai-knowledge', component: KnowledgeBase },
    { path: '/asset', component: AssetList },
    { path: '/cpe', component: CPEManager },
    { path: '/docker', component: DockerManager },
    { path: '/ssl-dns', component: SSLDns },
    {
        path: '/ssl-apply',
        component: SSLApply,
        children: [
            {
                path: 'cert/:id',
                component: SSLDetail,
                props: true
            }
        ]
    },
    { path: '/ssl-store', component: SSLStore },
]

const routeLabels = [
    {
        path: '/',
        label: '便签管理',
        icon: NoteIcon,
        key: 'notes'
    },
    {
        path: '/notify',
        label: '消息通知',
        icon: NotifyIcon,
        key: 'notify'
    },
    {
        label: '全流程',
        icon: WorkflowIcon,
        key: 'workflows',
        children: [
            {
                path: '/workflows',
                label: '工作流',
                icon: WorkflowIcon,
                key: 'workflows',
            },
            {
                path: '/nodes',
                label: '节点管理',
                icon: PCIcon,
                key: 'nodes'
            },
            {
                path: '/jobs',
                label: '任务管理',
                icon: ClockIcon,
                key: 'jobs'
            },
            {
                label: '证书管理',
                icon: SSLIcon,
                key: 'ssl',
                children: [
                    {
                        path: '/ssl-apply',
                        label: '证书申请',
                        icon: SSLApplyIcon,
                        key: 'ssl-apply'
                    },
                    {
                        path: '/ssl-dns',
                        label: 'DNS授权',
                        icon: SSLDNSIcon,
                        key: 'ssl-dns'
                    },
                    {
                        path: '/ssl-store',
                        label: '证书仓库',
                        icon: SSLListIcon,
                        key: 'ssl-store'
                    },
                    {
                        path: '/ssl-min',
                        label: '站点监控',
                        icon: SSLMiIcon,
                        key: 'ssl-min'
                    },

                ]
            },
        ]
    },


    {
        path: '/asset',
        label: '固定资产',
        icon: AssetIcon,
        key: 'asset'
    },
    {
        path: '/cpe',
        label: 'CPE 设备',
        icon: CPEIcon,
        key: 'cpe'
    },
    {
        path: '/docker',
        label: 'Docker 管理',
        icon: DockerIcon,
        key: 'docker'
    },
    {
        label: 'AI 助手',
        icon: AiIcon,
        key: 'ai-chat',
        children: [
            {
                path: '/ai-chat',
                label: 'AI 聊天',
                icon: AiIcon,
                key: 'ai-chat-main'
            },
            {
                path: '/ai-config',
                label: 'AI 配置',
                icon: ConfigIcon,
                key: 'ai-config'
            },
            {
                path: '/ai-knowledge',
                label: '知识库管理',
                icon: KnowledgeIcon,
                key: 'ai-knowledge'
            }
        ]
    },

    {
        label: '系统管理',  // 另一个父菜单
        icon: AboutIcon,
        key: 'sys',
        children: [
            {
                path: '/sys',
                label: '系统设置',
                icon: AboutIcon,
                key: 'sys-users'
            },
            {
                path: '/database',
                label: '数据管理',
                icon: DatabaseIcon,
                key: 'sys-database'
            },
        ]
    },
    {
        path: '/versions',
        label: '关于版本',
        icon: VersionIcon,
        key: 'versions'
    },
    {
        label: '示例菜单',
        icon: ExampleIcon,
        key: 'example',
        children: [
            {
                path: '/example',
                label: '示例页面1',
                key: 'example-1'
            },
            {
                path: '/example/page2',
                label: '示例页面2',
                key: 'example-2'
            },
            {
                label: '示例分组1',
                key: 'example-group1',
                children: [
                    {
                        path: '/example/group1/page3',
                        label: '示例页面3',
                        key: 'example-3'
                    },
                    {
                        path: '/example/group1/page4',
                        label: '示例页面4',
                        key: 'example-4'
                    }
                ]
            },
            {
                label: '示例分组2',
                key: 'example-group2',
                children: [
                    {
                        path: '/example/group2/page5',
                        label: '示例页面5',
                        key: 'example-5'
                    },
                    {
                        label: '三级菜单示例',
                        key: 'example-level3',
                        children: [
                            {
                                path: '/example/group2/level3/page6',
                                label: '三级页面',
                                key: 'example-6'
                            }
                        ]
                    }
                ]
            }
        ]
    }
];


export default createRouter({
    history: createWebHistory(),
    routes,
})
export { routeLabels }
outes,
})
export { routeLabels }
