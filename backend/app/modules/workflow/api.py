from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from .schemas import (
    Workflow,
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowExecution,
    WorkflowNodeExecution,
    WorkflowQueryParams,
    WorkflowTriggerRequest
)
from .services import WorkflowService

router = APIRouter(prefix="/workflows", tags=["任务链/工作流"])


@router.get("", response_model=List[Workflow])
async def list_workflows(
    node_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """获取工作流列表"""
    params = WorkflowQueryParams(
        node_id=node_id,
        is_active=is_active,
        keyword=keyword,
        page=page,
        page_size=page_size
    )
    workflows, total = await WorkflowService.list_workflows(params)
    return workflows


@router.get("/{workflow_id}", response_model=Workflow)
async def get_workflow(workflow_id: str):
    """获取工作流详情"""
    workflow = await WorkflowService.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    return workflow


@router.post("", response_model=Workflow)
async def create_workflow(data: WorkflowCreate):
    """创建工作流"""
    existing = await WorkflowService.get_workflow(data.workflow_id)
    if existing:
        raise HTTPException(status_code=400, detail="工作流ID已存在")
    return await WorkflowService.create_workflow(data)


@router.put("/{workflow_id}", response_model=Workflow)
async def update_workflow(workflow_id: str, data: WorkflowUpdate):
    """更新工作流"""
    workflow = await WorkflowService.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    return await WorkflowService.update_workflow(workflow_id, data)


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """删除工作流"""
    workflow = await WorkflowService.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    await WorkflowService.delete_workflow(workflow_id)
    return {"message": "删除成功"}


@router.post("/trigger")
async def trigger_workflow(data: WorkflowTriggerRequest):
    """触发工作流执行"""
    workflow = await WorkflowService.get_workflow(data.workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    execution_id = await WorkflowService.trigger_workflow(
        data.workflow_id,
        "manual",
        data.inputs
    )
    return {"message": "触发成功", "execution_id": execution_id}


@router.get("/executions/{execution_id}", response_model=WorkflowExecution)
async def get_execution(execution_id: int):
    """获取执行记录"""
    execution = await WorkflowService.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    return execution


@router.get("/{workflow_id}/executions", response_model=List[WorkflowExecution])
async def get_workflow_executions(workflow_id: str, limit: int = Query(20, ge=1, le=100)):
    """获取工作流的执行记录"""
    workflow = await WorkflowService.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    return await WorkflowService.get_executions(workflow_id, limit)


@router.get("/executions/{execution_id}/nodes", response_model=List[WorkflowNodeExecution])
async def get_node_executions(execution_id: int):
    """获取执行的节点记录"""
    return await WorkflowService.get_node_executions(execution_id)
