from fastapi import APIRouter, Depends, HTTPException,WebSocket
from fastapi.params import Body
from . import services, schemas, models
from app.core.database import engine, metadata
from .ssh_client import SSHClient
from .ws_manager import ws_manager

router = APIRouter(prefix="/cron", tags=["cron"])

# 初始化数据库表
metadata.create_all(engine, tables=[
    models.nodes_table,
    models.cron_jobs_table,
    models.job_executions_table
])

@router.websocket("/executions/{execution_id}/logs")
async def execution_logs_websocket(websocket: WebSocket, execution_id: int):
    await ws_manager.connect(websocket, execution_id)
    try:
        while True:
            # 保持连接（实际日志由后台任务推送）
            await websocket.receive_text()
    except Exception:
        ws_manager.disconnect(websocket, execution_id)
# 节点管理
@router.post("/nodes")
def create_node(node: schemas.NodeCreate):
    return services.create_node(engine, node)
# 在 Node 路由下添加
@router.post("/nodes/{node_id}/test")
def test_node_connection(node_id: int):
    node = services.get_node(engine, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")

    try:
        ssh_client = SSHClient(schemas.NodeRead(**node))
        ssh_client.connect()
        ssh_client.close()
        return {"success": True, "message": "连接成功"}
    except Exception as e:
        return {"success": False, "message": str(e)}
@router.get("/nodes", response_model=list[schemas.NodeRead])
def read_nodes():
    return services.get_nodes(engine)

@router.get("/nodes/{node_id}", response_model=schemas.NodeRead)
def read_node(node_id: int):
    node = services.get_node(engine, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")
    return node
@router.delete("/nodes/{node_id}", response_model=dict)
def remove_node(node_id: int):
    success = services.delete_node(engine, node_id)
    if success:
        return {"status": "ok", "id": node_id}
    return {"status": "not found", "id": node_id}
# 任务管理
@router.post("/jobs")
def create_job(job: schemas.CronJobCreate):
    return services.create_cron_job(engine, job)

@router.get("/jobs", response_model=list[schemas.CronJobRead])
def read_jobs(node_id: int = None):
    return services.get_cron_jobs(engine, node_id)

# 任务执行
@router.post("/jobs/execute", response_model=list[schemas.JobExecutionRead])
def execute_jobs(request: schemas.ManualExecutionRequest):
    if not request.job_ids and not request.node_ids:
        raise HTTPException(status_code=400, detail="必须指定任务ID或节点ID")
    return services.execute_jobs(engine, request)

@router.get("/jobs/{job_id}/executions", response_model=list[schemas.JobExecutionRead])
def read_job_executions(job_id: int, limit: int = 10):
    return services.get_executions(engine, job_id, limit)

@router.get("/executions/{execution_id}", response_model=schemas.JobExecutionRead)
def read_execution(execution_id: int):
    execution = services.get_execution(engine, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    return execution
@router.post("/executions/{execution_id}/stop")
def stop_execution(execution_id: int):
    from .execution_manager import execution_manager
    execution_manager.stop_execution(execution_id)
    return {"status": "ok", "message": "中断请求已发送"}

@router.patch("/jobs/{job_id}/toggle")
def toggle_job(job_id: int, is_active: bool = Body(..., embed=True)):
    success = services.toggle_job_status(engine, job_id, is_active)
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"status": "ok", "is_active": is_active}

@router.delete("/jobs/{job_id}", response_model=dict)
def remove_job(job_id: int):
    success = services.remove_job(engine, job_id)
    if success:
        return {"status": "ok", "id": job_id}
    return {"status": "not found", "id": job_id}
