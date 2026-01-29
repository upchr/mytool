from fastapi import APIRouter, HTTPException,WebSocket
from fastapi.params import Body
from app.core.sh.ssh_client import SSHClient
from app.core.db.database import engine, metadata
from . import services, schemas, models
from .schemas import NodeRequest

router = APIRouter(prefix="/nodes", tags=["nodes"])

# 节点管理
@router.post("")
def create_node(node: schemas.NodeCreate):
    return services.create_node(engine, node)

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
        return {"success": True, "message": "连接成功"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.get("/only_active/{active_only}", response_model=list[schemas.NodeRead])
def read_nodes(active_only: bool):
    return services.get_nodes(engine,active_only)

@router.get("/{node_id}", response_model=schemas.NodeRead)
def read_node(node_id: int):
    node = services.get_node(engine, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")
    return node

@router.delete("/{node_id}", response_model=dict)
def remove_node(node_id: int):
    success = services.delete_node(engine, node_id)
    if success:
        return {"status": "ok", "id": node_id}
    return {"status": "not found", "id": node_id}

@router.patch("/{node_id}/toggle")
def toggle_node(node_id: int, is_active: bool = Body(..., embed=True)):
    success = services.toggle_node_status(engine, node_id, is_active)
    if not success:
        raise HTTPException(status_code=404, detail="节点不存在")
    return {"status": "ok", "is_active": is_active}

@router.post("/deleteBatch")
def batch_delete_nodes(req:NodeRequest):
    if not req.node_ids:
        raise HTTPException(status_code=400, detail="节点ID列表不能为空")

    success_count = services.batch_delete_nodes(engine, req.node_ids)
    return {"success": True, "deleted_count": success_count}

@router.put("/{node_id}", response_model=dict)
def update_node(node_id: int, node: schemas.NodeCreate):
    updated = services.update_node(engine, node_id, node)
    if updated:
        return updated
    return {"status": "not found", "id": node_id}



@router.get("/credentials/", response_model=list[schemas.CredentialTemplateRead])
def list_credential_templates():
    return services.get_credential_templates(engine)

# credential templates
@router.post("/credentials/", response_model=schemas.CredentialTemplateRead)
def create_credential_template(template: schemas.CredentialTemplateCreate):
    return services.create_credential_template(engine, template)

@router.delete("/credentials/{template_id}")
def delete_credential_template(template_id: int):
    success = services.delete_credential_template(engine, template_id)
    if not success:
        raise HTTPException(404, "模板不存在")
    return {"status": "ok"}
@router.put("/credentials/{template_id}", response_model=dict)
def update_node(template_id: int, pj: schemas.CredentialTemplateCreate):
    updated = services.update_pj(engine, template_id, pj)
    if updated:
        return updated
    return {"detail": "not found", "id": template_id}

