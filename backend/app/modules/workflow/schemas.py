from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# ============== 工作流 ==============

class WorkflowBase(BaseModel):
    workflow_id: str = Field(..., description="工作流唯一标识")
    name: str = Field(..., description="工作流名称")
    description: Optional[str] = Field(None, description="描述")
    node_id: int = Field(..., description="所属节点")
    schedule: Optional[str] = Field(None, description="Cron表达式")
    nodes: List[Dict[str, Any]] = Field(default_factory=list, description="节点定义")
    edges: List[Dict[str, Any]] = Field(default_factory=list, description="边定义")
    is_active: bool = Field(default=True, description="是否启用")


class WorkflowCreate(WorkflowBase):
    pass


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    schedule: Optional[str] = None
    nodes: Optional[List[Dict[str, Any]]] = None
    edges: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None


class Workflow(WorkflowBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============== 工作流执行 ==============

class WorkflowExecutionBase(BaseModel):
    workflow_id: str
    status: str = "pending"
    triggered_by: str = "system"


class WorkflowExecutionCreate(WorkflowExecutionBase):
    pass


class WorkflowExecution(WorkflowExecutionBase):
    id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    error: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============== 工作流节点执行 ==============

class WorkflowNodeExecutionBase(BaseModel):
    execution_id: int
    node_id: str
    node_name: Optional[str] = None
    status: str = "pending"


class WorkflowNodeExecutionCreate(WorkflowNodeExecutionBase):
    pass


class WorkflowNodeExecution(WorkflowNodeExecutionBase):
    id: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    output: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============== 查询参数 ==============

class WorkflowQueryParams(BaseModel):
    node_id: Optional[int] = None
    is_active: Optional[bool] = None
    keyword: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


# ============== 操作请求 ==============

class WorkflowTriggerRequest(BaseModel):
    workflow_id: str = Field(..., description="工作流ID")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="输入参数")


class WorkflowNodeAction(BaseModel):
    execution_id: int = Field(..., description="执行ID")
    node_id: str = Field(..., description="节点ID")
    action: str = Field(..., description="操作: skip/retry")


# ============== 节点类型 ==============

class NodeTypes:
    TASK = "task"
    CONDITION = "condition"
    PARALLEL = "parallel"
    WAIT = "wait"
    NOTIFICATION = "notification"


# ============== 工作流版本 ==============

class WorkflowVersionBase(BaseModel):
    workflow_id: str
    version: int
    name: str
    description: Optional[str] = None
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)
    change_note: Optional[str] = None
    created_by: Optional[str] = None


class WorkflowVersionCreate(WorkflowVersionBase):
    pass


class WorkflowVersion(WorkflowVersionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class WorkflowRestoreRequest(BaseModel):
    version_id: int = Field(..., description="要恢复的版本ID")
    change_note: Optional[str] = Field(None, description="恢复说明")


# ============== 内置工作流模板 ==============

BUILTIN_WORKFLOWS = [
    {
        "workflow_id": "app-deploy",
        "name": "应用发布流程",
        "description": "停止服务 → 备份 → 更新代码 → 重启服务",
        "nodes": [
            {"id": "stop", "type": "task", "name": "停止应用服务", "config": {}},
            {"id": "backup-db", "type": "task", "name": "备份数据库", "config": {}},
            {"id": "backup-code", "type": "task", "name": "备份应用代码", "config": {}},
            {"id": "update", "type": "task", "name": "更新代码", "config": {}},
            {"id": "start", "type": "task", "name": "启动应用服务", "config": {}},
            {"id": "notify-success", "type": "notification", "name": "发送成功通知", "config": {}},
            {"id": "rollback-code", "type": "task", "name": "回滚代码", "config": {}},
            {"id": "rollback-db", "type": "task", "name": "回滚数据库", "config": {}},
            {"id": "restore-service", "type": "task", "name": "恢复服务", "config": {}},
            {"id": "notify-failure", "type": "notification", "name": "发送失败告警", "config": {}}
        ],
        "edges": [
            {"source": "stop", "target": "backup-db", "condition": "success"},
            {"source": "backup-db", "target": "backup-code", "condition": "success"},
            {"source": "backup-code", "target": "update", "condition": "success"},
            {"source": "update", "target": "start", "condition": "success"},
            {"source": "start", "target": "notify-success", "condition": "success"},
            # 失败回滚流程
            {"source": "stop", "target": "notify-failure", "condition": "failure"},
            {"source": "backup-db", "target": "rollback-code", "condition": "failure"},
            {"source": "backup-code", "target": "rollback-db", "condition": "failure"},
            {"source": "update", "target": "rollback-code", "condition": "failure"},
            {"source": "start", "target": "rollback-code", "condition": "failure"},
            {"source": "rollback-code", "target": "rollback-db", "condition": "always"},
            {"source": "rollback-db", "target": "restore-service", "condition": "always"},
            {"source": "restore-service", "target": "notify-failure", "condition": "always"}
        ]
    },
    {
        "workflow_id": "data-backup",
        "name": "数据备份与验证流程",
        "description": "创建备份 → 压缩 → 校验 → 上传 → 验证",
        "nodes": [
            {"id": "backup", "type": "task", "name": "创建备份", "config": {}},
            {"id": "compress", "type": "task", "name": "压缩备份", "config": {}},
            {"id": "verify", "type": "task", "name": "完整性校验", "config": {}},
            {"id": "upload", "type": "task", "name": "上传到云存储", "config": {}},
            {"id": "download-check", "type": "task", "name": "下载验证", "config": {}},
            {"id": "cleanup", "type": "task", "name": "清理旧备份", "config": {}},
            {"id": "notify", "type": "notification", "name": "发送通知", "config": {}}
        ],
        "edges": [
            {"source": "backup", "target": "compress", "condition": "success"},
            {"source": "compress", "target": "verify", "condition": "success"},
            {"source": "verify", "target": "upload", "condition": "success"},
            {"source": "upload", "target": "download-check", "condition": "success"},
            {"source": "download-check", "target": "cleanup", "condition": "success"},
            {"source": "cleanup", "target": "notify", "condition": "success"}
        ]
    }
]
