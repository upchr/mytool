from pydantic import BaseModel, Field,  field_validator
from datetime import datetime
from typing import Optional, List
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
