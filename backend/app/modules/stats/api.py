# app/modules/stats/api.py
"""
统计模块 - FastAPI 路由定义

路由前缀: /stats
标签: 系统统计
"""
from fastapi import APIRouter, Depends, Query

from app.core.pojo.response import BaseResponse
from app.core.db.database import get_engine
from app.modules.stats.services import StatsService

router = APIRouter(prefix="/stats", tags=["系统统计"])


@router.get("/overview")
async def get_overview(engine=Depends(get_engine)):
    """
    获取系统概览统计
    
    Returns:
        包含 cron、workflow、node 等统计数据的字典
    """
    try:
        service = StatsService(engine)
        result = service.get_overview()
        return BaseResponse.success(result)
    except Exception as e:
        return BaseResponse.error(500, str(e))


@router.get("/recent-executions")
async def get_recent_executions(
    limit: int = Query(20, ge=1, le=100),
    engine=Depends(get_engine)
):
    """
    获取最近执行记录
    
    Args:
        limit: 返回条数
        engine: 数据库引擎
    
    Returns:
        执行记录列表
    """
    try:
        service = StatsService(engine)
        result = service.get_recent_executions(limit)
        return BaseResponse.success({"executions": result, "total": len(result)})
    except Exception as e:
        return BaseResponse.error(500, str(e))
