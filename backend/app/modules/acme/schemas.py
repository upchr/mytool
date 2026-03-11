# app/modules/acme/schemas.py
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator
import json


# ========== DNS授权相关Schema ==========

class DNSAuthBase(BaseModel):
    """DNS授权基础Schema"""
    name: str = Field(..., description="授权名称", min_length=1, max_length=100)
    provider: str = Field(..., description="提供商：tencent/aliyun/cloudflare", pattern="^(tencent|aliyun|cloudflare)$")
    description: Optional[str] = Field(None, description="描述", max_length=500)
    is_active: bool = Field(True, description="是否启用")


class DNSAuthCreate(DNSAuthBase):
    """创建DNS授权"""
    secret_id: str = Field(..., description="Secret ID", min_length=1, max_length=500)
    secret_key: str = Field(..., description="Secret Key", min_length=1, max_length=500)


class DNSAuthUpdate(BaseModel):
    """更新DNS授权"""
    name: Optional[str] = Field(None, description="授权名称", min_length=1, max_length=100)
    provider: Optional[str] = Field(None, description="提供商", pattern="^(tencent|aliyun|cloudflare)$")
    description: Optional[str] = Field(None, description="描述", max_length=500)
    secret_id: Optional[str] = Field(None, description="Secret ID", min_length=1, max_length=500)
    secret_key: Optional[str] = Field(None, description="Secret Key", min_length=1, max_length=500)
    is_active: Optional[bool] = Field(None, description="是否启用")


class DNSAuthRead(DNSAuthBase):
    """DNS授权读取（完整版，内部使用）"""
    id: int
    secret_id: str
    secret_key: str
    last_used_at: Optional[datetime] = None
    total_applications: int
    total_success: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DNSAuthReadSensitive(BaseModel):
    """DNS授权读取（脱敏版，对外API使用）"""
    id: int
    name: str
    provider: str
    description: Optional[str] = None
    is_active: bool
    last_used_at: Optional[datetime] = None
    total_applications: int
    total_success: int
    created_at: datetime
    updated_at: datetime
    secret_id: str = Field(..., description="已脱敏的Secret ID")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, obj):
        """脱敏处理"""
        if isinstance(obj, dict):
            secret_id = obj.get('secret_id', '')
            obj = obj.copy()
        else:
            secret_id = getattr(obj, 'secret_id', '')
            obj = obj.__dict__.copy()

        # 显示前4位和后4位
        masked = f"{secret_id[:4]}****{secret_id[-4:]}" if secret_id and len(secret_id) > 8 else "****"
        obj['secret_id'] = masked
        return cls(**obj)


# ========== 证书申请相关Schema ==========

class ApplicationBase(BaseModel):
    """证书申请基础Schema"""
    dns_auth_id: int = Field(..., description="DNS授权ID", gt=0)
    domains: List[str] = Field(..., description="域名列表", min_items=1)
    algorithm: str = Field("RSA", description="算法：RSA/ECC", pattern="^(RSA|ECC)$")
    renew_before: int = Field(30, description="到期前多少天自动续期", ge=1, le=90)

    email: Optional[str] = Field(None, description="申请人邮箱", max_length=100)

    auto_renew: bool = Field(True, description="是否自动续期")
    description: Optional[str] = Field(None, description="备注", max_length=500)
    auto_notice: Optional[bool] = Field(None, description="是否推送")
    when_notice: Optional[str] = Field(None, description="推送时机", pattern="^(completed|failed)$")

    node_id: Optional[int] = Field(None, description="上传节点id", gt=0)
    crt_path: Optional[str] = Field(None, description="crt_path", max_length=500)
    key_path: Optional[str] = Field(None, description="key_path", max_length=500)


    @field_validator('domains')
    def validate_domains(cls, v):
        """简单域名格式验证"""
        for domain in v:
            if not domain or '.' not in domain:
                raise ValueError(f'无效域名: {domain}')
        return v

class PendingRenewApplication(BaseModel):
    id: int
    dns_auth_id: int
    domains: List[str]
    algorithm: str
    renew_before: int
    email: Optional[str] = None

    auto_renew: bool
    next_renew_at: Optional[datetime] = None
    description: Optional[str] =None

    node_id: int
    crt_path: str
    key_path: str

    @field_validator('domains', mode='before')
    def parse_domains(cls, v):
        """自动解析 JSON 字符串"""
        if isinstance(v, str):
            return json.loads(v)
        return v

class ApplicationCreate(ApplicationBase):
    """创建证书申请"""
    pass


class ApplicationUpdate(BaseModel):
    """更新证书申请"""
    dns_auth_id: Optional[int] = Field(None, description="DNS授权ID", gt=0)
    domains: Optional[List[str]] = Field(None, description="域名列表", min_items=1)
    algorithm: Optional[str] = Field(None, description="算法", pattern="^(RSA|ECC)$")
    renew_before: Optional[int] = Field(None, description="续期提前天数", ge=1, le=90)
    email: Optional[str] = Field(None, description="申请人邮箱", max_length=100)

    auto_renew: Optional[bool] = Field(None, description="是否自动续期")
    description: Optional[str] = Field(None, description="备注", max_length=500)
    auto_notice: Optional[bool] = Field(None, description="是否推送")
    when_notice: Optional[str] = Field(None, description="推送时机", pattern="^(completed|failed)$")
    status: Optional[str] = Field(None, description="状态", pattern="^(pending|processing|completed|failed)$")

    node_id: int = Field(..., description="上传节点id", gt=0)
    crt_path: Optional[str] = Field(None, description="crt_path", max_length=500)
    key_path: Optional[str] = Field(None, description="key_path", max_length=500)

class ApplicationRead(ApplicationBase):
    """证书申请读取"""
    id: int
    status: str
    last_execution_id: Optional[int] = None
    next_renew_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== 执行历史相关Schema ==========

class ExecutionBase(BaseModel):
    """执行历史基础Schema"""
    application_id: int = Field(..., description="申请ID", gt=0)
    triggered_by: str = Field("system", description="触发方式：system/manual", pattern="^(system|manual)$")
    status: str = Field("pending", description="状态", pattern="^(pending|processing|success|failed)$")


class ExecutionCreate(ExecutionBase):
    """创建执行历史"""
    pass


class ExecutionRead(BaseModel):
    """执行历史读取"""
    id: int
    application_id: int
    status: str
    triggered_by: str
    cert_id: Optional[int] = None
    error: Optional[str] = None
    log: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== 证书相关Schema ==========

class CertificateBase(BaseModel):
    """证书基础Schema"""
    application_id: Optional[int] = Field(None, description="申请ID", gt=0)
    execution_id: Optional[int] = Field(None, description="执行ID", gt=0)
    domains: List[str] = Field(..., description="域名列表")
    issuer: Optional[str] = Field(None, description="颁发者", max_length=200)
    algorithm: str = Field(..., description="算法", pattern="^(RSA|ECC)$")
    not_before: datetime = Field(..., description="生效时间")
    not_after: datetime = Field(..., description="过期时间")
    is_active: bool = Field(True, description="是否有效")


class CertificateCreate(CertificateBase):
    """创建证书"""
    cert_path: Optional[str] = Field(None, description="证书文件路径", max_length=500)
    key_path: Optional[str] = Field(None, description="私钥文件路径", max_length=500)
    fullchain_path: Optional[str] = Field(None, description="完整链文件路径", max_length=500)


class CertificateRead(CertificateBase):
    """证书读取"""
    id: int
    cert_path: Optional[str] = None
    key_path: Optional[str] = None
    fullchain_path: Optional[str] = None
    renewed_by: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CertificateDetail(CertificateBase):
    """证书读取"""
    id: int
    cert_path: Optional[str] = None
    cert: Optional[str] = None
    key_path: Optional[str] = None
    key: Optional[str] = None
    fullchain_path: Optional[str] = None
    renewed_by: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== 下载日志相关Schema ==========

class DownloadLogBase(BaseModel):
    """下载日志基础Schema"""
    cert_id: int = Field(..., description="证书ID", gt=0)
    downloaded_by: Optional[str] = Field(None, description="下载用户/来源", max_length=100)


class DownloadLogCreate(DownloadLogBase):
    """创建下载日志"""
    pass


class DownloadLogRead(DownloadLogBase):
    """下载日志读取"""
    id: int
    downloaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== 请求/响应Schema ==========

class BatchOperationRequest(BaseModel):
    """批量操作请求"""
    ids: List[int] = Field(..., description="ID列表", min_items=1)


class RenewRequest(BaseModel):
    """续期请求"""
    application_id: int = Field(..., description="申请ID", gt=0)
    force: bool = Field(False, description="是否强制续期（忽略时间检查）")


class ExecuteRequest(BaseModel):
    """手动执行请求"""
    application_id: int = Field(..., description="申请ID", gt=0)
    triggered_by: str = Field("manual", description="触发方式")


# ========== 分页查询参数 ==========

class PageParams(BaseModel):
    """分页参数"""
    page: int = Field(1, description="页码", ge=1)
    page_size: int = Field(20, description="每页数量", ge=1, le=100)


# ========== 列表响应Schema ==========

class PaginatedResponse(BaseModel):
    """分页响应基础类"""
    total: int
    page: int
    page_size: int
    pages: int


class DNSAuthListResponse(PaginatedResponse):
    """DNS授权列表响应"""
    items: List[DNSAuthReadSensitive]


class ApplicationListResponse(PaginatedResponse):
    """申请列表响应"""
    items: List[ApplicationRead]


class ExecutionListResponse(PaginatedResponse):
    """执行历史列表响应"""
    items: List[ExecutionRead]


class CertificateListResponse(PaginatedResponse):
    """证书列表响应"""
    items: List[CertificateRead]


# ========== 统计相关Schema ==========

class DNSAuthStats(BaseModel):
    """DNS授权统计"""
    total: int
    active: int
    total_applications_sum: int
    total_success_sum: int
    success_rate: float


class ApplicationStats(BaseModel):
    """申请统计"""
    total: int
    pending: int
    processing: int
    completed: int
    failed: int
    auto_renew_enabled: int


class CertificateStats(BaseModel):
    """证书统计"""
    total: int
    active: int
    expired: int
    expiring_soon: int
    by_algorithm: Dict[str, int]


__all__ = [
    "DNSAuthBase", "DNSAuthCreate", "DNSAuthUpdate", "DNSAuthRead", "DNSAuthReadSensitive",
    "ApplicationBase", "ApplicationCreate", "ApplicationUpdate", "ApplicationRead",
    "ExecutionBase", "ExecutionCreate", "ExecutionRead",
    "CertificateBase", "CertificateCreate", "CertificateRead",
    "DownloadLogBase", "DownloadLogCreate", "DownloadLogRead",
    "BatchOperationRequest", "RenewRequest", "ExecuteRequest",
    "PageParams", "DNSAuthListResponse", "ApplicationListResponse",
    "ExecutionListResponse", "CertificateListResponse",
    "DNSAuthStats", "ApplicationStats", "CertificateStats",
    "PendingRenewApplication"
]
