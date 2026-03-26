from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query, Depends
from fastapi.params import Body
from typing import Optional, List
import asyncio
import json
import logging

from . import schemas
from .services import DockerService
from ...core.exception.exceptions import ServerException, NotFoundException
from ...core.pojo.response import BaseResponse
from ...core.db.database import get_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/docker", tags=["Docker管理"])


# ========== 容器管理 ==========

@router.get("/nodes/{node_id}/containers")
async def list_containers(
    node_id: int,
    all: bool = Query(True, description="是否包含停止的容器")
):
    """
    获取节点上的容器列表
    
    Args:
        node_id: 节点ID
        all: 是否包含停止的容器
    
    Returns:
        容器列表
    """
    docker = None
    try:
        docker = DockerService(node_id)
        containers = docker.list_containers(all=all)
        return BaseResponse.success(containers)
    except ValueError as e:
        raise NotFoundException(str(e))
    except RuntimeError as e:
        raise ServerException(str(e))
    except Exception as e:
        logger.error(f"获取容器列表失败: {e}")
        raise ServerException(f"获取容器列表失败: {str(e)}")
    finally:
        if docker:
            docker.close()


@router.get("/nodes/{node_id}/containers/fast")
async def list_containers_fast(node_id: int):
    """
    快速获取容器列表（仅运行中的）
    
    Args:
        node_id: 节点ID
    
    Returns:
        运行中的容器列表
    """
    docker = None
    try:
        docker = DockerService(node_id)
        containers = docker.list_containers_fast()
        return BaseResponse.success(containers)
    except ValueError as e:
        raise NotFoundException(str(e))
    except Exception as e:
        logger.error(f"快速获取容器列表失败: {e}")
        raise ServerException(f"获取容器列表失败: {str(e)}")
    finally:
        if docker:
            docker.close()


@router.post("/nodes/{node_id}/containers/action")
async def container_action(
    node_id: int,
    req: schemas.ContainerAction
):
    """
    容器操作（同步等待）
    
    Args:
        node_id: 节点ID
        req: 操作请求
    
    Returns:
        操作结果
    """
    docker = None
    try:
        docker = DockerService(node_id)
        success, message = docker.container_action(req.container_id, req.action)
        if success:
            return BaseResponse.success(message=message)
        else:
            raise ServerException(message)
    except ValueError as e:
        raise NotFoundException(str(e))
    except Exception as e:
        logger.error(f"容器操作失败: {e}")
        raise ServerException(f"操作失败: {str(e)}")
    finally:
        if docker:
            docker.close()


@router.post("/nodes/{node_id}/containers/action/async")
async def container_action_async(
    node_id: int,
    req: schemas.ContainerAction
):
    """
    容器操作（异步立即返回）
    
    Args:
        node_id: 节点ID
        req: 操作请求
    
    Returns:
        操作结果
    """
    docker = None
    try:
        docker = DockerService(node_id)
        success, message = docker.container_action_async(req.container_id, req.action)
        return BaseResponse.success(message=message, data={"async": True})
    except ValueError as e:
        raise NotFoundException(str(e))
    except Exception as e:
        logger.error(f"异步容器操作失败: {e}")
        raise ServerException(f"操作失败: {str(e)}")
    finally:
        if docker:
            docker.close()


@router.get("/nodes/{node_id}/containers/{container_id}/logs")
async def get_container_logs(
    node_id: int,
    container_id: str,
    tail: int = Query(100, ge=1, le=10000, description="显示最后N行日志")
):
    """
    获取容器日志（静态版本）
    
    Args:
        node_id: 节点ID
        container_id: 容器ID
        tail: 显示最后N行日志
    
    Returns:
        日志内容
    """
    docker = None
    try:
        docker = DockerService(node_id)
        logs = docker.get_container_logs(container_id, tail)
        return BaseResponse.success({"logs": logs})
    except ValueError as e:
        raise NotFoundException(str(e))
    except Exception as e:
        logger.error(f"获取容器日志失败: {e}")
        raise ServerException(f"获取日志失败: {str(e)}")
    finally:
        if docker:
            docker.close()


# ========== Compose 项目管理 ==========

@router.get("/nodes/{node_id}/compose")
async def list_compose_projects(node_id: int):
    """
    获取节点上的 Compose 项目列表（快速版）
    
    Args:
        node_id: 节点ID
    
    Returns:
        Compose 项目列表
    """
    docker = None
    try:
        docker = DockerService(node_id)
        projects = docker.list_compose_projects()
        return BaseResponse.success(projects)
    except ValueError as e:
        raise NotFoundException(str(e))
    except Exception as e:
        logger.error(f"获取 Compose 项目列表失败: {e}")
        raise ServerException(f"获取项目列表失败: {str(e)}")
    finally:
        if docker:
            docker.close()


@router.get("/nodes/{node_id}/compose/search")
async def list_compose_projects_with_search(node_id: int):
    """
    获取节点上的 Compose 项目列表（包含目录搜索）
    
    Args:
        node_id: 节点ID
    
    Returns:
        Compose 项目列表
    """
    docker = None
    try:
        docker = DockerService(node_id)
        projects = docker.list_compose_projects_with_search()
        return BaseResponse.success(projects)
    except ValueError as e:
        raise NotFoundException(str(e))
    except Exception as e:
        logger.error(f"搜索 Compose 项目失败: {e}")
        raise ServerException(f"搜索项目失败: {str(e)}")
    finally:
        if docker:
            docker.close()


@router.get("/nodes/{node_id}/compose/file")
async def get_compose_file(
    node_id: int,
    path: str = Query(..., description="项目路径")
):
    """
    读取 Compose 文件内容
    
    Args:
        node_id: 节点ID
        path: 项目路径
    
    Returns:
        文件内容
    """
    docker = None
    try:
        docker = DockerService(node_id)
        content = docker.get_compose_file(path)
        return BaseResponse.success({"path": path, "content": content})
    except FileNotFoundError as e:
        raise NotFoundException(str(e))
    except ValueError as e:
        raise NotFoundException(str(e))
    except Exception as e:
        logger.error(f"读取 Compose 文件失败: {e}")
        raise ServerException(f"读取文件失败: {str(e)}")
    finally:
        if docker:
            docker.close()


@router.post("/nodes/{node_id}/compose/file")
async def save_compose_file(
    node_id: int,
    req: schemas.ComposeFile
):
    """
    保存 Compose 文件
    
    Args:
        node_id: 节点ID
        req: 文件内容
    
    Returns:
        保存结果
    """
    docker = None
    try:
        docker = DockerService(node_id)
        success, message = docker.save_compose_file(req.path, req.content)
        if success:
            return BaseResponse.success(message=message)
        else:
            raise ServerException(message)
    except ValueError as e:
        raise ServerException(str(e))
    except Exception as e:
        logger.error(f"保存 Compose 文件失败: {e}")
        raise ServerException(f"保存文件失败: {str(e)}")
    finally:
        if docker:
            docker.close()


@router.post("/nodes/{node_id}/compose/action")
async def compose_action(
    node_id: int,
    req: schemas.ComposeAction
):
    """
    Compose 项目操作
    
    Args:
        node_id: 节点ID
        req: 操作请求
    
    Returns:
        操作结果
    """
    docker = None
    try:
        docker = DockerService(node_id)
        success, message = docker.compose_action(req.path, req.action, req.services)
        if success:
            return BaseResponse.success(message=message, data={"output": message})
        else:
            raise ServerException(message)
    except ValueError as e:
        raise ServerException(str(e))
    except Exception as e:
        logger.error(f"Compose 操作失败: {e}")
        raise ServerException(f"操作失败: {str(e)}")
    finally:
        if docker:
            docker.close()


# ========== 操作日志 ==========

@router.get("/nodes/{node_id}/logs")
async def get_operation_logs(
    node_id: int,
    limit: int = Query(50, ge=1, le=500, description="返回记录数")
):
    """
    获取 Docker 操作日志
    
    Args:
        node_id: 节点ID
        limit: 返回记录数
    
    Returns:
        操作日志列表
    """
    try:
        from sqlalchemy import select, desc
        from .models import docker_operation_logs_table
        
        with get_engine().connect() as conn:
            stmt = (
                select(docker_operation_logs_table)
                .where(docker_operation_logs_table.c.node_id == node_id)
                .order_by(desc(docker_operation_logs_table.c.created_at))
                .limit(limit)
            )
            result = conn.execute(stmt)
            logs = [dict(row) for row in result.mappings()]
            
            return BaseResponse.success(logs)
    except Exception as e:
        logger.error(f"获取操作日志失败: {e}")
        raise ServerException(f"获取日志失败: {str(e)}")


# ========== WebSocket 实时日志 ==========

@router.websocket("/nodes/{node_id}/containers/{container_id}/logs/stream")
async def container_logs_stream(
    websocket: WebSocket,
    node_id: int,
    container_id: str,
    tail: int = 100,
    follow: bool = True
):
    """
    容器日志 WebSocket 实时流
    
    Args:
        websocket: WebSocket 连接
        node_id: 节点ID
        container_id: 容器ID
        tail: 显示最后N行日志
        follow: 是否实时跟踪
    """
    await websocket.accept()
    
    docker = None
    channel = None
    
    try:
        from app.core.sh.ssh_client import SSHClient
        from app.modules.node import services as node_services
        from app.modules.node.schemas import NodeRead
        from app.core.db.database import engine as db_engine
        import paramiko
        
        node_data = node_services.get_node(db_engine, node_id)
        if not node_data:
            await websocket.send_text(json.dumps({"error": "节点不存在"}))
            return
        
        node = NodeRead(**node_data)
        ssh = SSHClient(node)
        ssh.connect()
        
        transport = ssh.client.get_transport()
        channel = transport.open_session()
        
        follow_flag = "-f" if follow else ""
        cmd = f"docker logs {follow_flag} --tail {tail} {container_id} 2>&1"
        channel.exec_command(cmd)
        
        while True:
            if channel.recv_ready():
                data = channel.recv(4096)
                if data:
                    try:
                        text = data.decode('utf-8', errors='replace')
                        await websocket.send_text(json.dumps({"log": text}))
                    except Exception:
                        pass
                else:
                    break
            elif channel.exit_status_ready():
                break
            await asyncio.sleep(0.05)
        
        await websocket.send_text(json.dumps({"done": True}))
        
    except WebSocketDisconnect:
        logger.info(f"日志 WebSocket 断开连接: node_id={node_id}, container_id={container_id}")
    except Exception as e:
        logger.error(f"日志 WebSocket 错误: {e}")
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
    """
    容器终端 WebSocket
    
    Args:
        websocket: WebSocket 连接
        node_id: 节点ID
        container_id: 容器ID
        shell: Shell 类型（sh/bash/zsh）
    """
    await websocket.accept()
    
    docker = None
    channel = None
    
    try:
        from app.core.sh.ssh_client import SSHClient
        from app.modules.node import services as node_services
        from app.modules.node.schemas import NodeRead
        from app.core.db.database import engine as db_engine
        import paramiko
        
        node_data = node_services.get_node(db_engine, node_id)
        if not node_data:
            await websocket.send_text(json.dumps({"error": "节点不存在"}))
            return
        
        node = NodeRead(**node_data)
        ssh = SSHClient(node)
        ssh.connect()
        
        transport = ssh.client.get_transport()
        channel = transport.open_session()
        
        channel.get_pty(term="xterm", width=120, height=40)
        
        channel.exec_command(f"docker exec -it {container_id} {shell}")
        
        await asyncio.sleep(0.2)
        
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
                    logger.error(f"终端接收错误: {e}")
                    break
        
        async def send_to_container():
            """从 WebSocket 接收数据并发送到容器"""
            while True:
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                    msg = json.loads(data)
                    
                    if "input" in msg:
                        channel.send(msg["input"])
                    elif "resize" in msg:
                        resize = msg["resize"]
                        channel.resize_pty(
                            width=resize.get("cols", 120),
                            height=resize.get("rows", 40)
                        )
                except asyncio.TimeoutError:
                    continue
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"终端发送错误: {e}")
                    break
        
        await asyncio.gather(
            recv_from_container(),
            send_to_container()
        )
        
    except WebSocketDisconnect:
        logger.info(f"终端 WebSocket 断开连接: node_id={node_id}, container_id={container_id}")
    except Exception as e:
        logger.error(f"终端 WebSocket 错误: {e}")
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
