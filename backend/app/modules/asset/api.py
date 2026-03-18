# app/modules/asset/api.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List

from app.core.exception.exceptions import NotFoundException
from app.core.pojo.response import BaseResponse
from app.core.db.database import get_engine
from app.modules.asset import schemas
from app.modules.asset.services import AssetService
# 导入 datetime 用于 ScrapRequest
from datetime import datetime
router = APIRouter(prefix="/asset", tags=["固定资产管理"])


# ========== 固定资产管理 ==========

@router.post("/", response_model=BaseResponse[schemas.AssetRead])
async def create_asset(
        data: schemas.AssetCreate,
        engine=Depends(get_engine)
):
    """
    创建固定资产

    创建新的固定资产记录，系统会自动计算使用天数、日均成本等信息。
    """
    try:
        service = AssetService(engine)
        result = service.create(data)
        return BaseResponse.success(result)
    except Exception as e:
        return BaseResponse.error(400, str(e))


@router.put("/{id}", response_model=BaseResponse[schemas.AssetRead])
async def update_asset(
        id: int,
        data: schemas.AssetUpdate,
        engine=Depends(get_engine)
):
    """
    更新固定资产

    更新固定资产信息，修改价格或日期后会重新计算日均成本等字段。
    """
    try:
        service = AssetService(engine)
        result = service.update(id, data)
        if not result:
            return BaseResponse.error(404, f"资产 ID:{id} 不存在")
        return BaseResponse.success(result)
    except Exception as e:
        return BaseResponse.error(400, str(e))


@router.delete("/{id}", response_model=BaseResponse)
async def delete_asset(
        id: int,
        engine=Depends(get_engine)
):
    """
    删除固定资产

    删除指定的固定资产记录。
    """
    try:
        service = AssetService(engine)
        success = service.delete(id)
        if not success:
            return BaseResponse.error(404, f"资产 ID:{id} 不存在")
        return BaseResponse.success(message="删除成功")
    except ValueError as e:
        return BaseResponse.error(400, str(e))
    except Exception as e:
        return BaseResponse.error(500, str(e))


@router.post("/batch/delete", response_model=BaseResponse)
async def batch_delete_assets(
        request: schemas.BatchOperationRequest,
        engine=Depends(get_engine)
):
    """
    批量删除固定资产

    批量删除多个固定资产记录。
    """
    try:
        service = AssetService(engine)
        count = service.batch_delete(request.ids)
        return BaseResponse.success(message=f"成功删除 {count} 个资产")
    except ValueError as e:
        return BaseResponse.error(400, str(e))
    except Exception as e:
        return BaseResponse.error(500, str(e))


@router.get("/{id}", response_model=BaseResponse[schemas.AssetRead])
async def get_asset(
        id: int,
        engine=Depends(get_engine)
):
    """
    获取固定资产详情

    获取指定固定资产的详细信息，包含自动计算的使用天数、日均成本等字段。
    """
    service = AssetService(engine)
    result = service.get_by_id(id)
    if not result:
        return BaseResponse.error(404, f"资产 ID:{id} 不存在")
    return BaseResponse.success(result)


@router.get("/", response_model=BaseResponse[schemas.AssetListResponse])
async def list_assets(
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量"),
        category: Optional[str] = Query(None, description="资产类别筛选"),
        status: Optional[str] = Query(None, description="状态筛选"),
        search: Optional[str] = Query(None, description="搜索关键词（名称、备注）"),
        sort_by: Optional[str] = Query(None, description="排序字段"),
        sort_order: Optional[str] = Query(None, description="排序方向（asc/desc）"),
        engine=Depends(get_engine)
):
    """
    获取固定资产列表

    分页查询固定资产列表，支持按类别、状态筛选和关键词搜索。
    """
    service = AssetService(engine)
    result = service.get_list(
        page=page,
        page_size=page_size,
        category=category,
        status=status,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return BaseResponse.success(result)


@router.post("/{id}/scrap", response_model=BaseResponse[schemas.AssetRead])
async def scrap_asset(
        id: int,
        request: Optional[schemas.ScrapRequest] = None,
        engine=Depends(get_engine)
):
    """
    报废固定资产

    将资产标记为报废状态，停止日均成本计算。
    """
    try:
        service = AssetService(engine)
        scrap_date = request.scrap_date if request else None
        result = service.scrap(id, scrap_date)
        if not result:
            return BaseResponse.error(404, f"资产 ID:{id} 不存在")
        return BaseResponse.success(result, message="资产已报废")
    except Exception as e:
        return BaseResponse.error(400, str(e))


@router.post("/batch/scrap", response_model=BaseResponse)
async def batch_scrap_assets(
        request: schemas.BatchOperationRequest,
        scrap_date: Optional[datetime] = Query(None, description="报废日期"),
        engine=Depends(get_engine)
):
    """
    批量报废固定资产

    批量将多个资产标记为报废状态。
    """
    try:
        service = AssetService(engine)
        count = service.batch_scrap(request.ids, scrap_date)
        return BaseResponse.success(message=f"成功报废 {count} 个资产")
    except Exception as e:
        return BaseResponse.error(400, str(e))


# ========== 统计分析 ==========

@router.get("/stats/summary", response_model=BaseResponse[schemas.AssetStats])
async def get_asset_stats(engine=Depends(get_engine)):
    """
    获取固定资产统计信息

    返回总资产数量、总价值、按类别统计、按年份统计等信息。
    """
    service = AssetService(engine)
    stats = service.get_stats()
    return BaseResponse.success(stats)


@router.get("/stats/category-distribution", response_model=BaseResponse[List[schemas.CategoryDistribution]])
async def get_category_distribution(engine=Depends(get_engine)):
    """
    获取资产类别分布

    返回各类别的资产数量、价值和占比，用于饼图展示。
    """
    service = AssetService(engine)
    distribution = service.get_category_distribution()
    return BaseResponse.success(distribution)


@router.get("/stats/year-trend", response_model=BaseResponse[List[schemas.YearTrend]])
async def get_year_trend(
        limit: int = Query(10, ge=1, le=20, description="返回年份数量限制"),
        engine=Depends(get_engine)
):
    """
    获取年度购买趋势

    返回各年度的购买数量和金额，用于柱状图展示。
    """
    service = AssetService(engine)
    trend = service.get_year_trend(limit)
    return BaseResponse.success(trend)


@router.get("/stats/top-value", response_model=BaseResponse[List[schemas.AssetRead]])
async def get_top_value_assets(
        limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
        engine=Depends(get_engine)
):
    """
    获取价值最高的资产

    返回价值最高的资产列表，用于排行榜展示。
    """
    service = AssetService(engine)
    assets = service.get_top_value_assets(limit)
    return BaseResponse.success(assets)


@router.get("/stats/expiring-warranty", response_model=BaseResponse[List[schemas.AssetRead]])
async def get_expiring_warranty_assets(
        days: int = Query(30, ge=1, le=365, description="天数阈值"),
        engine=Depends(get_engine)
):
    """
    获取即将过质保的资产

    返回在指定天数内即将过质保的资产列表。
    """
    service = AssetService(engine)
    assets = service.get_expiring_warranty_assets(days)
    return BaseResponse.success(assets)


