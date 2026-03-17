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