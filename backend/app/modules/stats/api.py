from fastapi import APIRouter, Query
from typing import List
from .services import StatsService

router = APIRouter(prefix="/stats", tags=["系统统计"])


@router.get("/overview")
async def get_overview():
    """获取系统概览统计"""
    return await StatsService.get_overview()


@router.get("/recent-executions")
async def get_recent_executions(limit: int = Query(20, ge=1, le=100)):
    """获取最近执行记录"""
    return await StatsService.get_recent_executions(limit)