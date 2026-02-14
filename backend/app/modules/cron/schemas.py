from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from typing import Optional, List, Literal
from croniter import croniter

# 任务相关
class CronJobBase(BaseModel):
    node_id: int
    name: str
    schedule: str
    command: str
    description: Optional[str] = None
    is_active: bool = True
    is_notice: bool = False
    error_times: int

class CronJobCreate(BaseModel):
    node_ids: list[int]  # 👈 改为列表
    name: str
    schedule: str
    command: str
    description: str = ""
    is_active: bool = False
    is_notice: bool = False
    error_times: int
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
    is_notice: Optional[bool] = None
    error_times: Optional[int] = None

class CronJobCreateSingle(BaseModel):
    node_id: int  # 单个节点
    name: str
    schedule: str
    command: str
    description: str = ""
    is_active: bool = False
    is_notice: bool = False
    error_times: int
class CronJobRead(CronJobBase):
    id: int
    next_run: Optional[datetime] = None
    model_config = {"from_attributes": True}

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


class CronReq(BaseModel):
    cron: str

class CronNextRes(BaseModel):
    next_run: Optional[datetime] = None

