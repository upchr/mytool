from fastapi import APIRouter, HTTPException,WebSocket
from fastapi.params import Body
from app.core.sh.ssh_client import SSHClient
from app.core.db.database import engine, metadata, logger
from . import services, schemas, models
from .schemas import NodeRequest
from ...core.exception.exceptions import ServerException, NotFoundException
from ...core.pojo.response import BaseResponse

router = APIRouter(prefix="/nodes", tags=["nodes"])

# 节点管理
@router.post("")
def create_node(node: schemas.NodeCreate):
    return BaseResponse.success(services.create_node(engine, node))

# 在 Node 路由下添加
@router.post("/{node_id}/test")
def test_node_connection(node_id: int):
    node = services.get_node(engine, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")
    try:
        ssh_client = SSHClient(schemas.NodeRead(**node))
        ssh_client.connect()
        ssh_client.close()
        return BaseResponse.success(message="连接成功")
    except Exception as e:
        raise ServerException(str(e))

@router.get("/only_active/{active_only}")
def read_nodes(active_only: bool):
    return BaseResponse.success(services.get_nodes(engine,active_only))

@router.get("/{node_id}")
def read_node(node_id: int):
    node = services.get_node(engine, node_id)
    if not node:
        raise NotFoundException(detail=f"节点不存在")
    return BaseResponse.success(node)

@router.delete("/{node_id}")
def remove_node(node_id: int):
    success = services.delete_node(engine, node_id)
    if success:
        return BaseResponse.success({"status": "ok", "id": node_id})
    raise NotFoundException(detail=f"节点不存在")


@router.patch("/{node_id}/toggle")
def toggle_node(node_id: int, is_active: bool = Body(..., embed=True)):
    success = services.toggle_node_status(engine, node_id, is_active)
    if not success:
        raise NotFoundException(detail=f"节点不存在")
    return BaseResponse.success({"status": "ok", "is_active": is_active})

@router.post("/deleteBatch")
def batch_delete_nodes(req:NodeRequest):
    if not req.node_ids:
        raise ServerException(detail=f"节点ID列表不能为空")

    success_count = services.batch_delete_nodes(engine, req.node_ids)
    return BaseResponse.success({"success": True, "deleted_count": success_count})

@router.put("/{node_id}")
def update_node(node_id: int, node: schemas.NodeCreate):
    updated = services.update_node(engine, node_id, node)
    if updated:
        return BaseResponse.success(updated)
    raise NotFoundException(detail=f"节点不存在")




@router.get("/credentials/")
def list_credential_templates():
    return BaseResponse.success(services.get_credential_templates(engine))

# credential templates
@router.post("/credentials/")
def create_credential_template(template: schemas.CredentialTemplateCreate):
    return BaseResponse.success(services.create_credential_template(engine, template))


@router.delete("/credentials/{template_id}")
def delete_credential_template(template_id: int):
    success = services.delete_credential_template(engine, template_id)
    if not success:
        raise NotFoundException(detail=f"模板不存在")
    return BaseResponse.success()

@router.put("/credentials/{template_id}")
def update_node(template_id: int, pj: schemas.CredentialTemplateCreate):
    updated = services.update_pj(engine, template_id, pj)
    if updated:
        return BaseResponse.success(updated)
    raise NotFoundException(detail=f"模板不存在")


