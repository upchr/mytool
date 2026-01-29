from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, Field

T = TypeVar('T')

class BaseResponse(BaseModel, Generic[T]):
    """基础响应模型"""
    code: int = Field(default=200, description="状态码")
    message: str = Field(default="success", description="消息")
    data: Optional[T] = Field(default=None, description="数据")

class ErrorResponse(BaseModel):
    """错误响应模型"""
    code: int = Field(..., description="错误码")
    message: str = Field(..., description="错误消息")
    detail: Optional[Any] = Field(default=None, description="错误详情")

class PaginatedResponse(BaseResponse[list[T]]):
    """分页响应模型"""
    total: int = Field(..., description="总条数")
    page: int = Field(..., description="当前页")
    page_size: int = Field(..., description="每页条数")
    has_next: bool = Field(..., description="是否有下一页")
