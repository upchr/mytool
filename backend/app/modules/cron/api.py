from fastapi import APIRouter, HTTPException, WebSocket, Query
from fastapi.params import Body
from app.core.ws.ws_manager import ws_manager
from app.core.db.database import engine, metadata
from . import services, schemas, models
from app.modules.node.schemas import NodeRequest
from ...core.exception.exceptions import NotFoundException, ServerException
from ...core.pojo.response import BaseResponse


from ...core.utils.jwt import verify_jwt_token

router = APIRouter(prefix="/cron", tags=["cron"])


@router.websocket("/executions/{execution_id}/logs")
async def execution_logs_websocket(websocket: WebSocket, execution_id: int, token: str = Query(...)):
    # 验证 token
    # 1. 从查询参数获取 token
    if not token:
        await websocket.close(code=4001, reason="不存在token。请登录")
        return
    # 2. 验证 token
    try:
        payload = verify_jwt_token(token)
        # 可选：验证用户是否有权访问该 execution_id
    except HTTPException as e:
        await websocket.close(code=401, reason=e.detail)
        return
    except Exception as e:
        await websocket.close(code=401, reason="token无效。请登录")
        return


    await ws_manager.connect(websocket, execution_id)
    try:
        while True:
            # 保持连接（实际日志由后台任务推送）
            await websocket.receive_text()
    except Exception:
        ws_manager.disconnect(websocket, execution_id)

# 任务管理
@router.post("/jobs")
def create_cron_job(job: schemas.CronJobCreate):
    """为多个节点创建相同任务"""
    results = []
    for node_id in job.node_ids:
        # 为每个节点创建独立任务
        job_data = job.model_dump()
        job_data['node_id'] = node_id  # 单个节点ID
        del job_data['node_ids']       # 移除列表字段

        result = services.create_cron_job(engine, schemas.CronJobCreateSingle(**job_data))
        results.append(result)
    return BaseResponse.success(results)

@router.post("/jobsList")
def read_jobs(req: NodeRequest):
    return BaseResponse.success(services.get_cron_jobs(engine, req.node_ids or None))

@router.put("/jobs/{job_id}")
def update_cron_job(job_id: int, job_update: schemas.CronJobUpdate):
    # 检查任务是否存在
    existing_job = services.get_cron_job(engine, job_id)
    if not existing_job:
        raise NotFoundException(detail=f"任务不存在")

    # 只允许更新 name, schedule, command, description, is_active
    updated_data = job_update.model_dump(exclude_unset=True)

    success = services.update_cron_job(engine, job_id, updated_data)
    if not success:
        raise ServerException(detail=f"更新任务失败")

    return BaseResponse.success(services.get_cron_job(engine, job_id))

# 任务执行
@router.post("/jobs/execute")
def execute_jobs(request: schemas.ManualExecutionRequest):
    if not request.job_ids and not request.node_ids:
        raise NotFoundException(detail=f"必须指定任务ID或节点ID")
    return BaseResponse.success(services.execute_jobs(engine, request))

@router.get("/jobs/{job_id}/executions")
def read_job_executions(job_id: int, limit: int = 10):
    return BaseResponse.success(services.get_executions(engine, job_id, limit))

@router.get("/executions/{execution_id}")
def read_execution(execution_id: int):
    execution = services.get_execution(engine, execution_id)
    if not execution:
        raise NotFoundException(detail=f"执行记录不存在")
    return BaseResponse.success(execution)

@router.post("/executions/{execution_id}/stop")
async def stop_execution(execution_id: int):
    from app.core.interrupt.execution_manager import execution_manager
    execution_manager.stop_execution(execution_id)
    return BaseResponse.success({"status": "ok", "message": "中断请求已发送"})

@router.patch("/jobs/{job_id}/toggle")
def toggle_job(job_id: int, is_active: bool = Body(..., embed=True)):
    success = services.toggle_job_status(engine, job_id, is_active)
    if not success:
        raise NotFoundException(detail=f"任务不存在")
    return BaseResponse.success({"status": "ok", "is_active": is_active})

@router.delete("/jobs/{job_id}")
def remove_job(job_id: int):
    success = services.remove_job(engine, job_id)
    if success:
        return BaseResponse.success({"status": "ok", "id": job_id})
    raise NotFoundException(detail=f"任务不存在")


@router.post("/jobs/crons")
def get_next_crons(cron: schemas.CronReq):
    return BaseResponse.success(services.get_next_crons(cron))
