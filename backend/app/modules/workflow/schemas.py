# app/modules/workflow/schemas.py
"""
工作流模块 - Pydantic Schema 定义

Schema 层次：
- Base: 基础字段
- Create: 创建请求
- Update: 更新请求
- Read: 读取响应
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ========== 节点类型常量 ==========

class NodeTypes:
    """工作流节点类型"""
    TASK = "task"                    # 任务节点
    CONDITION = "condition"          # 条件节点
    WAIT = "wait"                    # 等待节点
    NOTIFICATION = "notification"    # 通知节点
    SUBWORKFLOW = "subworkflow"      # 子工作流


# ========== 工作流相关 Schema ==========

class WorkflowBase(BaseModel):
    """工作流基础 Schema"""
    workflow_id: str = Field(..., description="工作流唯一标识", min_length=1, max_length=100)
    name: str = Field(..., description="工作流名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="工作流描述")
    node_id: int = Field(..., description="所属节点ID", gt=0)
    schedule: Optional[str] = Field(None, description="Cron表达式")
    nodes: List[Dict[str, Any]] = Field(default_factory=list, description="节点定义列表")
    edges: List[Dict[str, Any]] = Field(default_factory=list, description="边定义列表")
    is_active: bool = Field(True, description="是否启用")


class WorkflowCreate(WorkflowBase):
    """创建工作流"""
    pass


class WorkflowUpdate(BaseModel):
    """更新工作流"""
    name: Optional[str] = Field(None, description="工作流名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="工作流描述")
    schedule: Optional[str] = Field(None, description="Cron表达式")
    nodes: Optional[List[Dict[str, Any]]] = Field(None, description="节点定义列表")
    edges: Optional[List[Dict[str, Any]]] = Field(None, description="边定义列表")
    is_active: Optional[bool] = Field(None, description="是否启用")


class WorkflowRead(WorkflowBase):
    """工作流读取 Schema"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class WorkflowListResponse(BaseModel):
    """工作流列表响应"""
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    page_size: int = Field(..., description="每页大小")
    items: List[WorkflowRead] = Field(default_factory=list, description="工作流列表")


# ========== 工作流执行相关 Schema ==========

class WorkflowExecutionBase(BaseModel):
    """工作流执行基础 Schema"""
    workflow_id: str = Field(..., description="工作流ID")
    status: str = Field("pending", description="状态")
    triggered_by: str = Field("system", description="触发方式")


class WorkflowExecutionRead(WorkflowExecutionBase):
    """工作流执行读取 Schema"""
    id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    error: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class WorkflowNodeExecutionRead(BaseModel):
    """工作流节点执行读取 Schema"""
    id: int
    execution_id: int
    node_id: str
    node_name: Optional[str] = None
    node_type: Optional[str] = None
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    output: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ========== 工作流版本相关 Schema ==========

class WorkflowVersionBase(BaseModel):
    """工作流版本基础 Schema"""
    workflow_id: str = Field(..., description="工作流ID")
    version: int = Field(..., description="版本号", gt=0)
    name: str = Field(..., description="版本名称")
    description: Optional[str] = Field(None, description="版本描述")
    nodes: List[Dict[str, Any]] = Field(default_factory=list, description="节点定义快照")
    edges: List[Dict[str, Any]] = Field(default_factory=list, description="边定义快照")
    change_note: Optional[str] = Field(None, description="变更说明")
    created_by: Optional[str] = Field(None, description="创建者")


class WorkflowVersionCreate(WorkflowVersionBase):
    """创建工作流版本"""
    pass


class WorkflowVersionRead(WorkflowVersionBase):
    """工作流版本读取 Schema"""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ========== 操作请求 Schema ==========

class WorkflowTriggerRequest(BaseModel):
    """触发工作流请求"""
    workflow_id: str = Field(..., description="工作流ID")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="输入参数")


class WorkflowRestoreRequest(BaseModel):
    """恢复工作流版本请求"""
    version_id: int = Field(..., description="要恢复的版本ID")
    change_note: Optional[str] = Field(None, description="恢复说明")


class WorkflowQueryParams(BaseModel):
    """工作流查询参数"""
    node_id: Optional[int] = Field(None, description="节点ID")
    is_active: Optional[bool] = Field(None, description="是否启用")
    keyword: Optional[str] = Field(None, description="关键词搜索")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页大小")


__all__ = [
    "NodeTypes",
    "WorkflowBase",
    "WorkflowCreate",
    "WorkflowUpdate",
    "WorkflowRead",
    "WorkflowListResponse",
    "WorkflowExecutionBase",
    "WorkflowExecutionRead",
    "WorkflowNodeExecutionRead",
    "WorkflowVersionBase",
    "WorkflowVersionCreate",
    "WorkflowVersionRead",
    "WorkflowTriggerRequest",
    "WorkflowRestoreRequest",
    "WorkflowQueryParams",
]
