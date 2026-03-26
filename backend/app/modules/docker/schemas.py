from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


class ContainerInfo(BaseModel):
    """容器信息模型"""
    id: str = Field(..., description="容器ID（短格式）")
    name: str = Field(..., description="容器名称")
    image: str = Field(..., description="镜像名称")
    status: str = Field(..., description="容器状态描述")
    state: str = Field(..., description="容器状态：running/exited/paused等")
    ports: Optional[str] = Field(None, description="端口映射")
    created: Optional[str] = Field(None, description="创建时间")


class ContainerAction(BaseModel):
    """容器操作请求模型"""
    action: str = Field(..., description="操作类型：start/stop/restart/remove")
    container_id: str = Field(..., description="容器ID", min_length=1)
    
    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        valid_actions = ["start", "stop", "restart", "remove"]
        if v not in valid_actions:
            raise ValueError(f"无效的操作类型，必须是: {', '.join(valid_actions)}")
        return v


class ComposeProject(BaseModel):
    """Docker Compose 项目信息模型"""
    name: str = Field(..., description="项目名称")
    path: str = Field(default="", description="项目路径")
    status: Optional[str] = Field(None, description="项目状态")
    services: Optional[int] = Field(0, description="服务数量")


class ComposeFile(BaseModel):
    """Compose 文件内容模型"""
    path: str = Field(..., description="项目路径", min_length=1)
    content: str = Field(..., description="YAML内容", min_length=1)
    
    @field_validator('path')
    @classmethod
    def validate_path(cls, v):
        if not v.startswith('/'):
            raise ValueError("路径必须是绝对路径，以 / 开头")
        return v


class ComposeAction(BaseModel):
    """Compose 操作请求模型"""
    action: str = Field(..., description="操作类型：up/down/restart/pull")
    path: str = Field(..., description="项目路径", min_length=1)
    services: Optional[List[str]] = Field(None, description="指定服务列表（可选）")
    
    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        valid_actions = ["up", "down", "restart", "pull"]
        if v not in valid_actions:
            raise ValueError(f"无效的操作类型，必须是: {', '.join(valid_actions)}")
        return v
    
    @field_validator('path')
    @classmethod
    def validate_path(cls, v):
        if not v.startswith('/'):
            raise ValueError("路径必须是绝对路径，以 / 开头")
        return v


class ContainerLogs(BaseModel):
    """容器日志请求模型"""
    container_id: str = Field(..., description="容器ID", min_length=1)
    tail: int = Field(100, ge=1, le=10000, description="显示最后N行日志")
    follow: bool = Field(False, description="是否实时跟踪日志")


class TerminalInput(BaseModel):
    """终端输入模型"""
    input: str = Field(..., description="输入内容")


class TerminalResize(BaseModel):
    """终端窗口大小调整模型"""
    rows: int = Field(..., ge=10, le=200, description="行数")
    cols: int = Field(..., ge=40, le=500, description="列数")


class DockerOperationLog(BaseModel):
    """Docker 操作日志模型"""
    id: int
    node_id: int
    operation_type: str
    target: str
    status: str
    message: str
    created_at: datetime
    
    model_config = {"from_attributes": True}
