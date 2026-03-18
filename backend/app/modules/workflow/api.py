# app/modules/workflow/api.py
"""
工作流模块 - FastAPI 路由定义

路由前缀: /workflows
标签: 工作流管理

注意：具名路由要放在动态路由（/{id}）前面，防止路由匹配失效
"""
from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from app.core.pojo.response import BaseResponse
from app.core.db.database import get_engine
from app.modules.workflow import schemas
from app.modules.workflow.services import WorkflowService, WorkflowVersionService

router = APIRouter(prefix="/workflows", tags=["工作流管理"])


# ========== 工作流管理 ==========

@router.post("", response_model=BaseResponse[schemas.WorkflowRead])
async def create_workflow(
    data: schemas.WorkflowCreate,
    engine=Depends(get_engine)
):
    """创建工作流"""
    try:
        service = WorkflowService(engine)
        existing = service.get_by_id(data.workflow_id)
        if existing:
            return BaseResponse.error(400, f"工作流ID已存在: {data.workflow_id}")
        
        result = service.create(data)
        return BaseResponse.success(result)
    except Exception as e:
        return BaseResponse.error(500, str(e))


@router.get("", response_model=BaseResponse[schemas.WorkflowListResponse])
async def list_workflows(
    node_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    engine=Depends(get_engine)
):
    """获取工作流列表"""
    try:
        params = schemas.WorkflowQueryParams(
            node_id=node_id,
            is_active=is_active,
            keyword=keyword,
            page=page,
            page_size=page_size
        )
        service = WorkflowService(engine)
        result = service.get_list(params)
        return BaseResponse.success(result)
    except Exception as e:
        return BaseResponse.error(500, str(e))


# ========== 工作流执行（具名路由，放在动态路由前面） ==========

@router.post("/trigger")
async def trigger_workflow(
    data: schemas.WorkflowTriggerRequest,
    engine=Depends(get_engine)
):
    """触发工作流执行"""
    try:
        service = WorkflowService(engine)
        workflow = service.get_by_id(data.workflow_id)
        if not workflow:
            return BaseResponse.error(404, f"工作流不存在: {data.workflow_id}")
        
        execution_id = service.trigger(data.workflow_id, "manual", data.inputs)
        return BaseResponse.success(
            {"execution_id": execution_id},
            message="工作流触发成功"
        )
    except Exception as e:
        return BaseResponse.error(500, str(e))


@router.get("/executions/{execution_id}", response_model=BaseResponse[schemas.WorkflowExecutionRead])
async def get_execution(
    execution_id: int,
    engine=Depends(get_engine)
):
    """获取执行记录详情"""
    service = WorkflowService(engine)
    result = service.get_execution(execution_id)
    if not result:
        return BaseResponse.error(404, f"执行记录不存在: {execution_id}")
    return BaseResponse.success(result)


@router.get("/executions/{execution_id}/nodes")
async def get_node_executions(
    execution_id: int,
    engine=Depends(get_engine)
):
    """获取节点执行记录"""
    service = WorkflowService(engine)
    result = service.get_node_executions(execution_id)
    return BaseResponse.success(result)


# ========== 版本管理（具名路由，放在动态路由前面） ==========

@router.get("/versions/{version_id}")
async def get_workflow_version(
    version_id: int,
    engine=Depends(get_engine)
):
    """获取版本详情"""
    service = WorkflowVersionService(engine)
    result = service.get_version(version_id)
    if not result:
        return BaseResponse.error(404, f"版本不存在: {version_id}")
    return BaseResponse.success(result)


# ========== 工作流 CRUD（动态路由放在最后） ==========

@router.get("/{workflow_id}", response_model=BaseResponse[schemas.WorkflowRead])
async def get_workflow(
    workflow_id: str,
    engine=Depends(get_engine)
):
    """获取工作流详情"""
    service = WorkflowService(engine)
    result = service.get_by_id(workflow_id)
    if not result:
        return BaseResponse.error(404, f"工作流不存在: {workflow_id}")
    return BaseResponse.success(result)


@router.put("/{workflow_id}", response_model=BaseResponse[schemas.WorkflowRead])
async def update_workflow(
    workflow_id: str,
    data: schemas.WorkflowUpdate,
    engine=Depends(get_engine)
):
    """更新工作流"""
    try:
        service = WorkflowService(engine)
        existing = service.get_by_id(workflow_id)
        if not existing:
            return BaseResponse.error(404, f"工作流不存在: {workflow_id}")
        
        result = service.update(workflow_id, data)
        return BaseResponse.success(result)
    except Exception as e:
        return BaseResponse.error(500, str(e))


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    engine=Depends(get_engine)
):
    """删除工作流（软删除）"""
    try:
        service = WorkflowService(engine)
        existing = service.get_by_id(workflow_id)
        if not existing:
            return BaseResponse.error(404, f"工作流不存在: {workflow_id}")
        
        success = service.delete(workflow_id)
        if success:
            return BaseResponse.success(message="删除成功")
        return BaseResponse.error(500, "删除失败")
    except Exception as e:
        return BaseResponse.error(500, str(e))


@router.get("/{workflow_id}/executions")
async def get_workflow_executions(
    workflow_id: str,
    limit: int = Query(20, ge=1, le=100),
    engine=Depends(get_engine)
):
    """获取工作流的执行记录列表"""
    service = WorkflowService(engine)
    workflow = service.get_by_id(workflow_id)
    if not workflow:
        return BaseResponse.error(404, f"工作流不存在: {workflow_id}")
    
    result = service.get_executions(workflow_id, limit)
    return BaseResponse.success(result)


@router.post("/{workflow_id}/versions")
async def create_workflow_version(
    workflow_id: str,
    change_note: Optional[str] = None,
    engine=Depends(get_engine)
):
    """创建工作流版本"""
    try:
        service = WorkflowVersionService(engine)
        result = service.create_version(workflow_id, change_note)
        return BaseResponse.success(result, message="版本创建成功")
    except ValueError as e:
        return BaseResponse.error(400, str(e))
    except Exception as e:
        return BaseResponse.error(500, str(e))


@router.get("/{workflow_id}/versions")
async def list_workflow_versions(
    workflow_id: str,
    engine=Depends(get_engine)
):
    """获取工作流版本列表"""
    workflow_service = WorkflowService(engine)
    workflow = workflow_service.get_by_id(workflow_id)
    if not workflow:
        return BaseResponse.error(404, f"工作流不存在: {workflow_id}")
    
    version_service = WorkflowVersionService(engine)
    result = version_service.list_versions(workflow_id)
    return BaseResponse.success(result)


@router.post("/{workflow_id}/versions/restore")
async def restore_workflow_version(
    workflow_id: str,
    data: schemas.WorkflowRestoreRequest,
    engine=Depends(get_engine)
):
    """恢复到指定版本"""
    try:
        workflow_service = WorkflowService(engine)
        workflow = workflow_service.get_by_id(workflow_id)
        if not workflow:
            return BaseResponse.error(404, f"工作流不存在: {workflow_id}")
        
        version_service = WorkflowVersionService(engine)
        result = version_service.restore_version(data.version_id, data.change_note)
        return BaseResponse.success(result, message="版本恢复成功")
    except ValueError as e:
        return BaseResponse.error(400, str(e))
    except Exception as e:
        return BaseResponse.error(500, str(e))
