# app/modules/task_template/schemas.py
"""
任务模板模块 - Pydantic Schema 定义
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ========== 任务模板相关 Schema ==========

class TaskTemplateBase(BaseModel):
    """任务模板基础 Schema"""
    template_id: str = Field(..., description="模板唯一标识", min_length=1, max_length=100)
    name: str = Field(..., description="模板名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="模板描述")
    category: Optional[str] = Field(None, description="分类")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    icon: str = Field("📝", description="图标")
    script_type: str = Field("shell", description="脚本类型")
    script_content: Optional[str] = Field(None, description="脚本内容")
    config_schema: Optional[Dict[str, Any]] = Field(None, description="配置项 Schema")
    default_cron: Optional[str] = Field(None, description="默认 Cron 表达式")
    cron_description: Optional[str] = Field(None, description="Cron 说明")
    is_official: bool = Field(True, description="是否官方模板")
    is_active: bool = Field(True, description="是否启用")


class TaskTemplateCreate(TaskTemplateBase):
    """创建任务模板"""
    pass


class TaskTemplateUpdate(BaseModel):
    """更新任务模板"""
    name: Optional[str] = Field(None, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    category: Optional[str] = Field(None, description="分类")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    icon: Optional[str] = Field(None, description="图标")
    script_type: Optional[str] = Field(None, description="脚本类型")
    script_content: Optional[str] = Field(None, description="脚本内容")
    config_schema: Optional[Dict[str, Any]] = Field(None, description="配置项 Schema")
    default_cron: Optional[str] = Field(None, description="默认 Cron 表达式")
    cron_description: Optional[str] = Field(None, description="Cron 说明")
    is_active: Optional[bool] = Field(None, description="是否启用")


class TaskTemplateRead(TaskTemplateBase):
    """任务模板读取 Schema"""
    id: int
    download_count: int
    rating_count: int
    rating_avg: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TaskTemplateListResponse(BaseModel):
    """任务模板列表响应"""
    total: int
    page: int
    page_size: int
    items: List[TaskTemplateRead]


# ========== 应用模板请求 ==========

class TemplateApplyRequest(BaseModel):
    """应用模板请求"""
    template_id: str = Field(..., description="模板ID")
    node_id: int = Field(..., description="节点ID", gt=0)
    variables: Dict[str, Any] = Field(default_factory=dict, description="变量替换")
    schedule: Optional[str] = Field(None, description="Cron 表达式")
    name: Optional[str] = Field(None, description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    is_active: Optional[bool] = Field(None, description="是否立即激活")


# ========== 查询参数 ==========

class TaskTemplateQueryParams(BaseModel):
    """任务模板查询参数"""
    category: Optional[str] = Field(None, description="分类")
    is_official: Optional[bool] = Field(None, description="是否官方")
    keyword: Optional[str] = Field(None, description="关键词搜索")
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


__all__ = [
    "TaskTemplateBase",
    "TaskTemplateCreate",
    "TaskTemplateUpdate",
    "TaskTemplateRead",
    "TaskTemplateListResponse",
    "TemplateApplyRequest",
    "TaskTemplateQueryParams",
]
