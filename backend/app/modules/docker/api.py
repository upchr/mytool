from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.params import Body
from typing import Optional, List
import asyncio
import json

from . import schemas
from .services import DockerService
from ...core.exception.exceptions import ServerException, NotFoundException
from ...core.pojo.response import BaseResponse

router = APIRouter(prefix="/docker", tags=["docker"])


# ========== 容器管理 ==========

@router.get("/nodes/{node_id}/containers")
async def list_containers(node_id: int, all: bool = True):
    """获取节点上的容器列表"""
    try:
        docker = DockerService(node_id)
        containers = docker.list_containers(all=all)
        return BaseResponse.success(containers)
    except Exception as e:
        raise ServerException(str(e))
    finally:
        docker.close()


@router.post("/nodes/{node_id}/containers/action")
async def container_action(node_id: int, req: schemas.ContainerAction):
    """容器操作：start/stop/restart/remove"""
    try:
        docker = DockerService(node_id)
        success, message = docker.container_action(req.container_id, req.action)
        if success:
            return BaseResponse.success(message=message)
        else:
            raise ServerException(message)
    except Exception as e:
        raise ServerException(str(e))
    finally:
        docker.close()


@router.get("/nodes/{node_id}/containers/{container_id}/logs")
async def get_container_logs(
    node_id: int,
    container_id: str,
    tail: int = Query(100, ge=1, le=10000)
):
    """获取容器日志"""
    try:
        docker = DockerService(node_id)
        logs = docker.get_container_logs(container_id, tail)
        return BaseResponse.success({"logs": logs})
    except Exception as e:
        raise ServerException(str(e))
    finally:
        docker.close()


# ========== Compose 项目管理 ==========

@router.get("/nodes/{node_id}/compose")
async def list_compose_projects(node_id: int):
    """获取节点上的 Compose 项目列表"""
    try:
        docker = DockerService(node_id)
        projects = docker.list_compose_projects()
        return BaseResponse.success(projects)
    except Exception as e:
        raise ServerException(str(e))
    finally:
        docker.close()


@router.get("/nodes/{node_id}/compose/file")
async def get_compose_file(node_id: int, path: str):
    """读取 Compose 文件内容"""
    try:
        docker = DockerService(node_id)
        content = docker.get_compose_file(path)
        return BaseResponse.success({"path": path, "content": content})
    except FileNotFoundError as e:
        raise NotFoundException(str(e))
    except Exception as e:
        raise ServerException(str(e))
    finally:
        docker.close()


@router.post("/nodes/{node_id}/compose/file")
async def save_compose_file(node_id: int, req: schemas.ComposeFile):
    """保存 Compose 文件"""
    try:
        docker = DockerService(node_id)
        success, message = docker.save_compose_file(req.path, req.content)
        if success:
            return BaseResponse.success(message=message)
        else:
            raise ServerException(message)
    except Exception as e:
        raise ServerException(str(e))
    finally:
        docker.close()


@router.post("/nodes/{node_id}/compose/action")
async def compose_action(node_id: int, req: schemas.ComposeAction):
    """Compose 项目操作：up/down/restart/pull"""
    try:
        docker = DockerService(node_id)
        success, message = docker.compose_action(req.path, req.action, req.services)
        if success:
            return BaseResponse.success(message=message, data={"output": message})
        else:
            raise ServerException(message)
    except Exception as e:
        raise ServerException(str(e))
    finally:
        docker.close()


# ========== WebSocket 终端 ==========

@router.websocket("/nodes/{node_id}/containers/{container_id}/terminal")
async def container_terminal(
    websocket: WebSocket,
    node_id: int,
    container_id: str,
    shell: str = "sh"
):
    """容器终端 WebSocket"""
    await websocket.accept()
    
    docker = None
    channel = None
    
    try:
        from app.core.sh.ssh_client import SSHClient
        from app.modules.node import services as node_services
        from app.modules.node.schemas import NodeRead
        from app.core.db.database import engine
        import paramiko
        
        # 获取节点信息
        node_data = node_services.get_node(engine, node_id)
        if not node_data:
            await websocket.send_text(json.dumps({"error": "节点不存在"}))
            return
        
        node = NodeRead(**node_data)
        ssh = SSHClient(node)
        ssh.connect()
        
        # 创建 Docker exec 通道
        transport = ssh.client.get_transport()
        channel = transport.open_session()
        
        # 请求伪终端
        channel.get_pty(term="xterm", width=80, height=24)
        
        # 执行 docker exec
        channel.exec_command(f"docker exec -it {container_id} {shell}")
        
        # 双向转发
        async def recv_from_container():
            """从容器接收数据并发送到 WebSocket"""
            while True:
                if channel.recv_ready():
                    data = channel.recv(1024)
                    if data:
                        await websocket.send_text(data.decode('utf-8', errors='replace'))
                    else:
                        break
                await asyncio.sleep(0.01)
        
        async def send_to_container():
            """从 WebSocket 接收数据并发送到容器"""
            while True:
                try:
                    data = await websocket.receive_text()
                    msg = json.loads(data)
                    
                    if "input" in msg:
                        channel.send(msg["input"])
                    elif "resize" in msg:
                        resize = msg["resize"]
                        channel.resize_pty(
                            width=resize.get("cols", 80),
                            height=resize.get("rows", 24)
                        )
                except Exception:
                    break
        
        # 并行运行两个任务
        await asyncio.gather(
            recv_from_container(),
            send_to_container()
        )
        
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({"error": str(e)}))
        except:
            pass
    finally:
        if channel:
            channel.close()
        if docker:
            docker.close()
        try:
            await websocket.close()
        except:
            pass
