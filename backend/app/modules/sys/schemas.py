from typing import Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class SysBase(BaseModel):
    """系统基础 Schema"""
    password: str = Field(..., description="密码", min_length=6)


class ResetSysBase(BaseModel):
    """重置密码 Schema"""
    old_password: str = Field(..., description="旧密码", min_length=6)
    password: str = Field(..., description="新密码", min_length=6)


class LoginRequest(BaseModel):
    """登录请求 Schema"""
    password: str = Field(..., description="密码", min_length=6)


class LoginResponse(BaseModel):
    """登录响应 Schema"""
    token: str = Field(..., description="JWT令牌")
    remaining_attempts: Optional[int] = Field(None, description="剩余尝试次数")


class SendResetCodeRequest(BaseModel):
    """发送重置验证码请求 Schema"""
    class Config:
        extra = "allow"  # 允许额外字段


class VerifyResetCodeRequest(BaseModel):
    """验证重置验证码并更新密码请求 Schema"""
    code: str = Field(..., description="验证码", min_length=6, max_length=10)
    new_password: str = Field(..., description="新密码", min_length=6)


class ResetPasswordResponse(BaseModel):
    """重置密码响应 Schema"""
    message: str = Field(..., description="响应消息")
    code: Optional[str] = Field(None, description="验证码（测试环境返回）")


class LoginFailedRecord(BaseModel):
    """登录失败记录 Schema"""
    id: int
    ip_address: str
    failed_time: datetime
    user_agent: Optional[str]
