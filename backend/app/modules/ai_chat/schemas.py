from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Message(BaseModel):
    role: str = Field(..., description="消息角色: user 或 assistant")
    content: str = Field(..., description="消息内容")
    timestamp: Optional[int] = Field(None, description="时间戳")


class ChatRequest(BaseModel):
    message: str = Field(..., description="用户消息")
    history: Optional[List[Message]] = Field(default_factory=list, description="历史消息")
    conversation_id: Optional[int] = Field(None, description="对话ID，用于保存历史")


class ChatResponse(BaseModel):
    content: str = Field(..., description="AI 响应内容")
    role: str = Field(default="assistant", description="响应角色")


class MessageSchema(BaseModel):
    """消息数据模型"""
    id: Optional[int] = None
    conversation_id: int
    role: str
    content: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConversationSchema(BaseModel):
    """对话数据模型"""
    id: Optional[int] = None
    title: str
    user_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    messages: List[MessageSchema] = []

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    """创建对话请求"""
    title: str = Field(default="新对话", description="对话标题")


class ConversationUpdate(BaseModel):
    """更新对话请求"""
    title: Optional[str] = None


class MessageCreate(BaseModel):
    """创建消息请求"""
    role: str
    content: str


class AIConfigSchema(BaseModel):
    """AI 配置数据模型"""
    id: Optional[int] = None
    name: Optional[str] = None
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    model: Optional[str] = None
    is_enabled: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AIConfigUpdate(BaseModel):
    """更新 AI 配置请求"""
    name: Optional[str] = Field(None, description="配置名称")
    api_key: Optional[str] = Field(None, description="API Key")
    api_base: Optional[str] = Field(None, description="API Base URL")
    model: Optional[str] = Field(None, description="模型名称")
    is_enabled: Optional[bool] = Field(None, description="是否启用")


class AIConfigCreate(BaseModel):
    """创建 AI 配置请求"""
    name: str = Field(..., description="配置名称")
    api_key: str = Field(..., description="API Key")
    api_base: str = Field(..., description="API Base URL")
    model: str = Field(..., description="模型名称")
    is_enabled: bool = Field(True, description="是否启用")


class AIConfigResponse(BaseModel):
    """AI 配置响应"""
    id: int
    name: Optional[str] = None
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    model: Optional[str] = None
    is_enabled: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TestConnectionRequest(BaseModel):
    """测试连接请求"""
    api_key: str = Field(..., description="API Key")
    api_base: str = Field(..., description="API Base URL")
    model: str = Field(..., description="模型名称")
    message: str = Field(default="你好，这是一个测试消息", description="测试消息")


# ========== 知识库相关 Schema ==========

class KnowledgeBaseSchema(BaseModel):
    """知识库数据模型"""
    id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class KnowledgeBaseCreate(BaseModel):
    """创建知识库请求"""
    name: str = Field(..., description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")


class KnowledgeBaseUpdate(BaseModel):
    """更新知识库请求"""
    name: Optional[str] = Field(None, description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")
    is_active: Optional[bool] = Field(None, description="是否启用")


class KnowledgeDocumentSchema(BaseModel):
    """知识文档数据模型"""
    id: Optional[int] = None
    knowledge_base_id: int
    title: str
    content: str
    category: Optional[str] = None
    tags: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class KnowledgeDocumentCreate(BaseModel):
    """创建知识文档请求"""
    knowledge_base_id: int = Field(..., description="知识库ID")
    title: str = Field(..., description="文档标题")
    content: str = Field(..., description="文档内容")
    category: Optional[str] = Field(None, description="文档分类")
    tags: Optional[str] = Field(None, description="文档标签，逗号分隔")


class KnowledgeDocumentUpdate(BaseModel):
    """更新知识文档请求"""
    title: Optional[str] = Field(None, description="文档标题")
    content: Optional[str] = Field(None, description="文档内容")
    category: Optional[str] = Field(None, description="文档分类")
    tags: Optional[str] = Field(None, description="文档标签，逗号分隔")
    is_active: Optional[bool] = Field(None, description="是否启用")


class KnowledgeSearchRequest(BaseModel):
    """知识检索请求"""
    query: str = Field(..., description="检索查询")
    knowledge_base_id: Optional[int] = Field(None, description="知识库ID，不指定则搜索所有")
    limit: int = Field(default=5, description="返回结果数量")


class KnowledgeSearchResult(BaseModel):
    """知识检索结果"""
    document_id: int
    document_title: str
    chunk_index: int
    content: str
    category: Optional[str] = None
    score: float = 0.0


class ChatRequestWithKnowledge(BaseModel):
    """带知识库的聊天请求"""
    message: str = Field(..., description="用户消息")
    history: Optional[List[Message]] = Field(default_factory=list, description="历史消息")
    conversation_id: Optional[int] = Field(None, description="对话ID")
    use_knowledge: bool = Field(default=True, description="是否使用知识库")
    knowledge_base_id: Optional[int] = Field(None, description="指定知识库ID")