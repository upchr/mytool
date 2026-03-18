# app/modules/asset/schemas.py
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator
import json


# ========== 固定资产相关Schema ==========

class AssetBase(BaseModel):
    """固定资产基础Schema"""
    name: str = Field(..., description="资产名称", min_length=1, max_length=200)
    category: str = Field(..., description="资产类别", pattern="^(electronics|home|office|vehicle|other)$")
    price: float = Field(..., description="购买价格", gt=0)
    purchase_date: datetime = Field(..., description="购买日期")
    description: Optional[str] = Field(None, description="备注说明")
    image_url: Optional[str] = Field(None, description="资产图片URL", max_length=500)
    warranty_months: Optional[int] = Field(None, description="质保期（月）", ge=0)


class AssetCreate(AssetBase):
    """创建固定资产"""
    pass


class AssetUpdate(BaseModel):
    """更新固定资产"""
    name: Optional[str] = Field(None, description="资产名称", min_length=1, max_length=200)
    category: Optional[str] = Field(None, description="资产类别", pattern="^(electronics|home|office|vehicle|other)$")
    price: Optional[float] = Field(None, description="购买价格", gt=0)
    purchase_date: Optional[datetime] = Field(None, description="购买日期")
    description: Optional[str] = Field(None, description="备注说明")
    image_url: Optional[str] = Field(None, description="资产图片URL", max_length=500)
    status: Optional[str] = Field(None, description="状态", pattern="^(active|scrapped)$")
    warranty_months: Optional[int] = Field(None, description="质保期（月）", ge=0)


class AssetRead(AssetBase):
    """固定资产读取（含计算字段）"""
    id: int
    status: str
    scrapped_date: Optional[datetime] = None
    warranty_expire_date: Optional[datetime] = None

    # 计算字段
    usage_days: int = Field(default=0, description="使用天数")
    daily_cost: float = Field(default=0.0, description="日均成本")
    remaining_warranty_days: Optional[int] = Field(default=None, description="剩余质保天数")
    is_warranty_expired: bool = Field(default=False, description="质保是否已过期")

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


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


class AssetListResponse(PaginatedResponse):
    """固定资产列表响应"""
    items: List[AssetRead]


# ========== 统计相关Schema ==========

class AssetStats(BaseModel):
    """固定资产统计"""
    total: int  # 总资产数量
    active: int  # 使用中资产
    scrapped: int  # 已报废资产
    total_value: float  # 总资产价值
    daily_cost_sum: float  # 日均成本总和

    # 按类别统计
    by_category: Dict[str, Dict[str, Any]]  # {category: {count, value}}

    # 按年份统计
    by_year: Dict[int, Dict[str, Any]]  # {year: {count, value}}


class CategoryDistribution(BaseModel):
    """类别分布"""
    category: str
    count: int
    value: float
    percentage: float


class YearTrend(BaseModel):
    """年度购买趋势"""
    year: int
    count: int
    value: float


# ========== 批量操作Schema ==========

class BatchOperationRequest(BaseModel):
    """批量操作请求"""
    ids: List[int] = Field(..., description="ID列表", min_items=1)


class ScrapRequest(BaseModel):
    """报废请求"""
    scrap_date: Optional[datetime] = Field(None, description="报废日期，默认为当前时间")


# ========== 导入导出Schema ==========

class AssetImportItem(BaseModel):
    """资产导入项"""
    name: str
    category: str
    price: float
    purchase_date: str  # YYYY-MM-DD 格式
    description: Optional[str] = None
    warranty_months: Optional[int] = None


class AssetImportResponse(BaseModel):
    """资产导入响应"""
    success_count: int
    failed_count: int
    failed_items: List[Dict[str, Any]]  # [{item, error}]


__all__ = [
    "AssetBase", "AssetCreate", "AssetUpdate", "AssetRead",
    "PageParams", "AssetListResponse",
    "AssetStats", "CategoryDistribution", "YearTrend",
    "BatchOperationRequest", "ScrapRequest",
    "AssetImportItem", "AssetImportResponse"
]