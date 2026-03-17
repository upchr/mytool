from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# ============== 任务模板 ==============

class TaskTemplateBase(BaseModel):
    template_id: str = Field(..., description="模板唯一标识")
    name: str = Field(..., description="模板名称")
    version: str = Field(default="1.0.0", description="模板版本")
    author: str = Field(default="MyTool Team", description="作者")
    description: Optional[str] = Field(None, description="模板描述")
    category: str = Field(..., description="分类")
    tags: List[str] = Field(default_factory=list, description="标签")
    difficulty: str = Field(default="入门", description="难度")
    icon: Optional[str] = Field(None, description="图标")
    is_official: bool = Field(default=True, description="是否官方")
    is_enabled: bool = Field(default=True, description="是否启用")


class TaskTemplateCreate(TaskTemplateBase):
    pass


class TaskTemplateUpdate(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    difficulty: Optional[str] = None
    icon: Optional[str] = None
    is_enabled: Optional[bool] = None


class TaskTemplate(TaskTemplateBase):
    id: int
    download_count: int = 0
    rating_count: int = 0
    rating_avg: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============== 模板Schema ==============

class TemplateSchemaBase(BaseModel):
    template_id: str
    schema_json: Dict[str, Any] = Field(..., description="参数配置Schema")


class TemplateSchemaCreate(TemplateSchemaBase):
    pass


class TemplateSchema(TemplateSchemaBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============== 模板脚本 ==============

class TemplateScriptBase(BaseModel):
    template_id: str
    script_type: str = Field(default="python", description="脚本类型")
    script_content: str = Field(..., description="脚本内容")


class TemplateScriptCreate(TemplateScriptBase):
    pass


class TemplateScript(TemplateScriptBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============== Cron建议 ==============

class TemplateCronSuggestionBase(BaseModel):
    template_id: str
    label: str = Field(..., description="建议标签")
    cron_value: str = Field(..., description="Cron表达式")
    is_default: bool = Field(default=False, description="是否默认")
    sort_order: int = Field(default=0, description="排序")


class TemplateCronSuggestionCreate(TemplateCronSuggestionBase):
    pass


class TemplateCronSuggestion(TemplateCronSuggestionBase):
    id: int

    class Config:
        from_attributes = True


# ============== 评分 ==============

class TemplateRatingBase(BaseModel):
    template_id: str
    user_id: int
    rating: int = Field(..., ge=1, le=5, description="评分1-5")
    comment: Optional[str] = Field(None, description="评论")


class TemplateRatingCreate(TemplateRatingBase):
    pass


class TemplateRating(TemplateRatingBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============== 查询参数 ==============

class TemplateQueryParams(BaseModel):
    category: Optional[str] = None
    tag: Optional[str] = None
    difficulty: Optional[str] = None
    is_official: Optional[bool] = None
    keyword: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


# ============== 完整模板详情 ==============

class TaskTemplateDetail(TaskTemplate):
    schema: Optional[TemplateSchema] = None
    script: Optional[TemplateScript] = None
    cron_suggestions: List[TemplateCronSuggestion] = Field(default_factory=list)


# ============== 一键应用请求 ==============

class TemplateApplyRequest(BaseModel):
    template_id: str = Field(..., description="模板ID")
    node_id: int = Field(..., description="节点ID")
    variables: Dict[str, Any] = Field(default_factory=dict, description="模板变量替换")
    schedule: Optional[str] = Field(None, description="Cron表达式，不填则使用默认建议")
    name: Optional[str] = Field(None, description="任务名称，不填则使用模板名称")
    description: Optional[str] = Field(None, description="任务描述")
    is_active: Optional[bool] = Field(None, description="是否立即激活")
    error_times: Optional[int] = Field(None, description="连续失败次数阈值")


# 兼容旧名称
TemplateImportRequest = TemplateApplyRequest
