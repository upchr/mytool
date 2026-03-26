from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.params import Body
from typing import Optional, List
import asyncio
import json
import threading

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


@router.get("/nodes/{node_id}/containers/fast")
async def list_containers_fast(node_id: int):
    """快速获取容器列表（仅运行中的）"""
    try:
        docker = DockerService(node_id)
        containers = docker.list_containers_fast()
        return BaseResponse.success(containers)
    except Exception as e:
        raise ServerException(str(e))
    finally:
        docker.close()


@router.post("/nodes/{node_id}/containers/action")
async def container_action(node_id: int, req: schemas.ContainerAction):
    """容器操作：start/stop/restart/remove - 同步等待"""
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


@router.post("/nodes/{node_id}/containers/action/async")
async def container_action_async(node_id: int, req: schemas.ContainerAction):
    """容器操作：start/stop/restart/remove - 异步立即返回"""
    try:
        docker = DockerService(node_id)
        success, message = docker.container_action_async(req.container_id, req.action)
        return BaseResponse.success(message=message, data={"async": True})
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
    """获取容器日志 - 静态版本"""
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
    """获取节点上的 Compose 项目列表 - 快速版（仅 docker compose ls）"""
    try:
        docker = DockerService(node_id)
        projects = docker.list_compose_projects()
        return BaseResponse.success(projects)
    except Exception as e:
        raise ServerException(str(e))
    finally:
        docker.close()


@router.get("/nodes/{node_id}/compose/search")
async def list_compose_projects_with_search(node_id: int):
    """获取节点上的 Compose 项目列表 - 包含目录搜索"""
    try:
        docker = DockerService(node_id)
        projects = docker.list_compose_projects_with_search()
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


# ========== WebSocket 实时日志 ==========

@router.websocket("/nodes/{node_id}/containers/{container_id}/logs/stream")
async def container_logs_stream(
    websocket: WebSocket,
    node_id: int,
    container_id: str,
    tail: int = 100,
    follow: bool = True
):
    """容器日志 WebSocket 实时流"""
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
        
        # 创建 SSH channel
        transport = ssh.client.get_transport()
        channel = transport.open_session()
        
        # 执行 docker logs --follow
        follow_flag = "-f" if follow else ""
        cmd = f"docker logs {follow_flag} --tail {tail} {container_id} 2>&1"
        channel.exec_command(cmd)
        
        # 接收日志并发送到 WebSocket
        while True:
            if channel.recv_ready():
                data = channel.recv(4096)
                if data:
                    try:
                        text = data.decode('utf-8', errors='replace')
                        await websocket.send_text(json.dumps({"log": text}))
                    except:
                        pass
                else:
                    break
            elif channel.exit_status_ready():
                break
            await asyncio.sleep(0.05)
        
        await websocket.send_text(json.dumps({"done": True}))
        
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


# ========== WebSocket 终端 ==========

@router.websocket("/nodes/{node_id}/containers/{container_id}/terminal")
async def container_terminal(
    websocket: WebSocket,
    node_id: int,
    container_id: str,
    shell: str = "sh"
):
    """容器终端 WebSocket - 修复版"""
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
        channel.get_pty(term="xterm", width=120, height=40)
        
        # 执行 docker exec
        channel.exec_command(f"docker exec -it {container_id} {shell}")
        
        # 等待一下让终端初始化
        await asyncio.sleep(0.2)
        
        # 使用线程来处理接收
        loop = asyncio.get_event_loop()
        output_queue = asyncio.Queue()
        
        async def recv_from_container():
            """从容器接收数据并发送到 WebSocket"""
            while True:
                try:
                    if channel.recv_ready():
                        data = channel.recv(1024)
                        if data:
                            text = data.decode('utf-8', errors='replace')
                            await websocket.send_text(json.dumps({"output": text}))
                        else:
                            break
                    elif channel.exit_status_ready():
                        break
                    await asyncio.sleep(0.01)
                except Exception as e:
                    break
        
        async def send_to_container():
            """从 WebSocket 接收数据并发送到容器"""
            while True:
                try:
                    # 使用 receive_text 超时机制
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                    msg = json.loads(data)
                    
                    if "input" in msg:
                        # 直接发送原始输入
                        channel.send(msg["input"])
                    elif "resize" in msg:
                        resize = msg["resize"]
                        channel.resize_pty(
                            width=resize.get("cols", 120),
                            height=resize.get("rows", 40)
                        )
                except asyncio.TimeoutError:
                    # 超时继续等待
                    continue
                except WebSocketDisconnect:
                    break
                except Exception as e:
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
