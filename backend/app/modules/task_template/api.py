# app/modules/task_template/api.py
"""
任务模板模块 - FastAPI 路由定义

路由前缀: /task-templates
标签: 任务模板
"""
from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from app.core.pojo.response import BaseResponse
from app.core.db.database import get_engine
from app.modules.task_template import schemas
from app.modules.task_template.services import TaskTemplateService

router = APIRouter(prefix="/task-templates", tags=["任务模板"])


@router.get("", response_model=BaseResponse[schemas.TaskTemplateListResponse])
async def list_templates(
    category: Optional[str] = None,
    is_official: Optional[bool] = None,
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    engine=Depends(get_engine)
):
    """
    获取任务模板列表
    
    Args:
        category: 分类筛选
        is_official: 是否官方筛选
        keyword: 关键词搜索
        page: 页码
        page_size: 每页大小
        engine: 数据库引擎
    
    Returns:
        分页模板列表
    """
    try:
        params = schemas.TaskTemplateQueryParams(
            category=category,
            is_official=is_official,
            keyword=keyword,
            page=page,
            page_size=page_size
        )
        service = TaskTemplateService(engine)
        result = service.get_list(params)
        return BaseResponse.success(result)
    except Exception as e:
        return BaseResponse.error(500, str(e))


@router.get("/{template_id}", response_model=BaseResponse[schemas.TaskTemplateRead])
async def get_template(
    template_id: str,
    engine=Depends(get_engine)
):
    """
    获取模板详情
    
    Args:
        template_id: 模板ID
        engine: 数据库引擎
    
    Returns:
        模板数据
    """
    service = TaskTemplateService(engine)
    result = service.get_by_id(template_id)
    if not result:
        return BaseResponse.error(404, f"模板不存在: {template_id}")
    return BaseResponse.success(result)


@router.post("", response_model=BaseResponse[schemas.TaskTemplateRead])
async def create_template(
    data: schemas.TaskTemplateCreate,
    engine=Depends(get_engine)
):
    """
    创建模板
    
    Args:
        data: 创建数据
        engine: 数据库引擎
    
    Returns:
        创建后的模板数据
    """
    try:
        service = TaskTemplateService(engine)
        existing = service.get_by_id(data.template_id)
        if existing:
            return BaseResponse.error(400, f"模板ID已存在: {data.template_id}")
        
        result = service.create(data)
        return BaseResponse.success(result)
    except Exception as e:
        return BaseResponse.error(500, str(e))


@router.put("/{template_id}", response_model=BaseResponse[schemas.TaskTemplateRead])
async def update_template(
    template_id: str,
    data: schemas.TaskTemplateUpdate,
    engine=Depends(get_engine)
):
    """
    更新模板
    
    Args:
        template_id: 模板ID
        data: 更新数据
        engine: 数据库引擎
    
    Returns:
        更新后的模板数据
    """
    try:
        service = TaskTemplateService(engine)
        existing = service.get_by_id(template_id)
        if not existing:
            return BaseResponse.error(404, f"模板不存在: {template_id}")
        
        result = service.update(template_id, data)
        return BaseResponse.success(result)
    except Exception as e:
        return BaseResponse.error(500, str(e))


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    engine=Depends(get_engine)
):
    """
    删除模板（软删除）
    
    Args:
        template_id: 模板ID
        engine: 数据库引擎
    
    Returns:
        操作结果
    """
    try:
        service = TaskTemplateService(engine)
        existing = service.get_by_id(template_id)
        if not existing:
            return BaseResponse.error(404, f"模板不存在: {template_id}")
        
        # 软删除
        service.update(template_id, schemas.TaskTemplateUpdate(is_active=False))
        return BaseResponse.success(message="删除成功")
    except Exception as e:
        return BaseResponse.error(500, str(e))


@router.post("/{template_id}/apply")
async def apply_template(
    template_id: str,
    data: schemas.TemplateApplyRequest,
    engine=Depends(get_engine)
):
    """
    应用模板 - 从模板创建 cron 任务
    
    Args:
        template_id: 模板ID
        data: 应用请求数据
        engine: 数据库引擎
    
    Returns:
        创建的任务信息
    """
    try:
        data.template_id = template_id
        service = TaskTemplateService(engine)
        result = service.apply_template(data)
        return BaseResponse.success(result, message="模板应用成功")
    except ValueError as e:
        return BaseResponse.error(400, str(e))
    except Exception as e:
        return BaseResponse.error(500, str(e))


@router.get("/categories")
async def get_categories(engine=Depends(get_engine)):
    """
    获取模板分类列表
    
    Args:
        engine: 数据库引擎
    
    Returns:
        分类列表
    """
    from sqlalchemy import distinct
    from app.modules.task_template.models import task_templates_table
    
    query = select(distinct(task_templates_table.c.category)).where(
        task_templates_table.c.is_active == True,
        task_templates_table.c.category.is_not(None)
    )
    
    with engine.connect() as conn:
        result = conn.execute(query)
        categories = [row[0] for row in result]
    
    return BaseResponse.success(categories)
