from pydantic import BaseModel, Field
from typing import List, Optional

class Message(BaseModel):
    role: str = Field(..., description="消息角色: user 或 assistant")
    content: str = Field(..., description="消息内容")
    timestamp: Optional[int] = Field(None, description="时间戳")

class ChatRequest(BaseModel):
    message: str = Field(..., description="用户消息")
    history: Optional[List[Message]] = Field(default_factory=list, description="历史消息")

class ChatResponse(BaseModel):
    content: str = Field(..., description="AI 响应内容")
    role: str = Field(default="assistant", description="响应角色")