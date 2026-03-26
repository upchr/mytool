from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ContainerInfo(BaseModel):
    """容器信息"""
    id: str
    name: str
    image: str
    status: str
    state: str  # running, exited, paused, etc.
    ports: Optional[str] = None
    created: Optional[str] = None


class ContainerAction(BaseModel):
    """容器操作请求"""
    action: str  # start, stop, restart, remove
    container_id: str


class ComposeProject(BaseModel):
    """Compose 项目信息"""
    name: str
    path: str
    status: Optional[str] = None
    services: Optional[int] = None


class ComposeFile(BaseModel):
    """Compose 文件内容"""
    path: str
    content: str


class ComposeAction(BaseModel):
    """Compose 操作请求"""
    action: str  # up, down, restart, pull
    path: str
    services: Optional[List[str]] = None


class ContainerLogs(BaseModel):
    """容器日志请求"""
    container_id: str
    tail: int = 100
    follow: bool = False


class TerminalInput(BaseModel):
    """终端输入"""
    data: str


class TerminalResize(BaseModel):
    """终端窗口大小调整"""
    rows: int
    cols: int
