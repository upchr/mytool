from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from typing import Optional, List, Literal
from croniter import croniter
# 节点相关
class NodeBase(BaseModel):
    name: str
    host: str
    port: int = 22
    username: str
    auth_type: str = "password"
    password: Optional[str] = None
    private_key: Optional[str] = None
    is_active: bool = True

class NodeCreate(NodeBase):
    pass

class NodeRead(NodeBase):
    id: int

    model_config = {"from_attributes": True}

# 任务相关
class CronJobBase(BaseModel):
    node_id: int
    name: str
    schedule: str
    command: str
    description: Optional[str] = None
    is_active: bool = True

class CronJobCreate(BaseModel):
    node_ids: list[int]  # 👈 改为列表
    name: str
    schedule: str
    command: str
    description: str = ""
    is_active: bool = False

    @field_validator('schedule')
    def validate_cron(cls, v):
        try:
            croniter(v)
            return v
        except:
            raise ValueError('无效的Cron表达式')
class CronJobUpdate(BaseModel):
    name: Optional[str] = None
    schedule: Optional[str] = None
    command: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class CronJobCreateSingle(BaseModel):
    node_id: int  # 单个节点
    name: str
    schedule: str
    command: str
    description: str = ""
    is_active: bool = False

class CronJobRead(CronJobBase):
    id: int
    next_run: Optional[datetime] = None
    model_config = {"from_attributes": True}

class NodeRequest(BaseModel):
    node_ids: List[int]

class CredentialTemplateCreate(BaseModel):
    name: str
    username: str
    auth_type: Literal['password', 'ssh_key']
    password: Optional[str] = None
    private_key: Optional[str] = None

    @model_validator(mode='after')
    def check_auth_fields(self):
        if self.auth_type == 'password' and not self.password:
            raise ValueError('密码认证必须提供密码')
        if self.auth_type == 'ssh_key' and not self.private_key:
            raise ValueError('SSH密钥认证必须提供私钥')
        return self

class CredentialTemplateRead(CredentialTemplateCreate):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

# 执行日志
class JobExecutionBase(BaseModel):
    job_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "pending"
    output: Optional[str] = None
    error: Optional[str] = None
    triggered_by: str

class JobExecutionRead(JobExecutionBase):
    id: int

    model_config = {"from_attributes": True}

# 手动执行请求
class ManualExecutionRequest(BaseModel):
    node_ids: List[int] = Field(default_factory=list)
    job_ids: List[int] = Field(default_factory=list)
