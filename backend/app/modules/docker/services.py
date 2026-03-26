from app.core.sh.ssh_client import SSHClient
from app.modules.node.schemas import NodeRead
from app.modules.node import services as node_services
from app.core.db.database import engine
from . import models
import json
import re
from typing import List, Optional, Tuple
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DockerService:
    """Docker 操作服务类"""
    
    def __init__(self, node_id: int):
        self.node_id = node_id
        self._ssh: Optional[SSHClient] = None
    
    def _get_ssh(self) -> SSHClient:
        """获取 SSH 连接（懒加载模式）"""
        if not self._ssh:
            node_data = node_services.get_node(engine, self.node_id)
            if not node_data:
                raise ValueError(f"节点 {self.node_id} 不存在")
            node = NodeRead(**node_data)
            self._ssh = SSHClient(node)
            self._ssh.connect()
        return self._ssh
    
    def close(self):
        """关闭 SSH 连接"""
        if self._ssh:
            try:
                self._ssh.close()
            except Exception as e:
                logger.warning(f"关闭 SSH 连接失败: {e}")
            finally:
                self._ssh = None
    
    def _log_operation(self, operation_type: str, action: str, target: str, status: str, message: str = ""):
        """记录 Docker 操作日志"""
        try:
            with engine.begin() as conn:
                conn.execute(
                    models.docker_operation_logs_table.insert().values(
                        node_id=self.node_id,
                        operation_type=operation_type,
                        action=action,
                        target=target,
                        status=status,
                        message=message,
                        created_at=datetime.now()
                    )
                )
        except Exception as e:
            logger.error(f"记录操作日志失败: {e}")
    
    def list_containers(self, all: bool = True) -> List[dict]:
        """
        获取容器列表
        
        Args:
            all: 是否包含停止的容器
        
        Returns:
            容器信息列表
        """
        ssh = self._get_ssh()
        flag = "-a" if all else ""
        cmd = f"docker ps {flag} --format '{{{{json .}}}}'"
        
        try:
            _, output, error = ssh.execute_command(cmd, timeout=10)
            
            if error and "command not found" in error.lower():
                raise RuntimeError("Docker 未安装或不在 PATH 中")
            
            containers = []
            for line in output.strip().split('\n'):
                if line:
                    try:
                        data = json.loads(line)
                        containers.append({
                            "id": data.get("ID", "")[:12],
                            "name": data.get("Names", ""),
                            "image": data.get("Image", ""),
                            "status": data.get("Status", ""),
                            "state": data.get("State", ""),
                            "ports": data.get("Ports", ""),
                            "created": data.get("CreatedAt", "")
                        })
                    except json.JSONDecodeError:
                        logger.warning(f"解析容器信息失败: {line}")
                        continue
            
            return containers
        except Exception as e:
            logger.error(f"获取容器列表失败: {e}")
            raise
    
    def list_containers_fast(self) -> List[dict]:
        """
        快速获取容器列表（仅运行中的）
        
        Returns:
            运行中的容器列表
        """
        ssh = self._get_ssh()
        cmd = "docker ps --format '{{json .}}'"
        
        try:
            _, output, _ = ssh.execute_command(cmd, timeout=5)
            
            containers = []
            for line in output.strip().split('\n'):
                if line:
                    try:
                        data = json.loads(line)
                        containers.append({
                            "id": data.get("ID", "")[:12],
                            "name": data.get("Names", ""),
                            "image": data.get("Image", ""),
                            "status": data.get("Status", ""),
                            "state": data.get("State", ""),
                            "ports": data.get("Ports", ""),
                            "created": data.get("CreatedAt", "")
                        })
                    except json.JSONDecodeError:
                        continue
            
            return containers
        except Exception as e:
            logger.error(f"快速获取容器列表失败: {e}")
            raise
    
    def container_action(self, container_id: str, action: str) -> Tuple[bool, str]:
        """
        容器操作（同步模式）
        
        Args:
            container_id: 容器ID
            action: 操作类型（start/stop/restart/remove）
        
        Returns:
            (是否成功, 消息)
        """
        ssh = self._get_ssh()
        
        valid_actions = ["start", "stop", "restart", "remove"]
        if action not in valid_actions:
            return False, f"无效操作: {action}"
        
        if action == "remove":
            cmd = f"docker rm -f {container_id}"
        else:
            cmd = f"docker {action} {container_id}"
        
        try:
            exit_code, output, error = ssh.execute_command(cmd, timeout=30)
            
            if exit_code == 0:
                message = f"容器 {container_id} 已{action}"
                self._log_operation("container", action, container_id, "success", message)
                return True, message
            else:
                error_msg = error or output or "操作失败"
                self._log_operation("container", action, container_id, "failed", error_msg)
                return False, error_msg
        except Exception as e:
            error_msg = str(e)
            self._log_operation("container", action, container_id, "failed", error_msg)
            return False, error_msg
    
    def container_action_async(self, container_id: str, action: str) -> Tuple[bool, str]:
        """
        容器操作（异步模式，后台执行）
        
        Args:
            container_id: 容器ID
            action: 操作类型（start/stop/restart/remove）
        
        Returns:
            (是否成功, 消息)
        """
        ssh = self._get_ssh()
        
        valid_actions = ["start", "stop", "restart", "remove"]
        if action not in valid_actions:
            return False, f"无效操作: {action}"
        
        if action == "remove":
            cmd = f"nohup docker rm -f {container_id} > /dev/null 2>&1 &"
        else:
            cmd = f"nohup docker {action} {container_id} > /dev/null 2>&1 &"
        
        try:
            _, _, _ = ssh.execute_command(cmd, timeout=5)
            message = f"容器 {container_id} 正在{action}..."
            self._log_operation("container", f"{action}_async", container_id, "success", message)
            return True, message
        except Exception as e:
            error_msg = str(e)
            self._log_operation("container", f"{action}_async", container_id, "failed", error_msg)
            return False, error_msg
    
    def get_container_logs(self, container_id: str, tail: int = 100) -> str:
        """
        获取容器日志
        
        Args:
            container_id: 容器ID
            tail: 显示最后N行日志
        
        Returns:
            日志内容
        """
        ssh = self._get_ssh()
        cmd = f"docker logs --tail {tail} {container_id} 2>&1"
        
        try:
            _, output, _ = ssh.execute_command(cmd, timeout=30)
            return output
        except Exception as e:
            logger.error(f"获取容器日志失败: {e}")
            raise
    
    def list_compose_projects(self) -> List[dict]:
        """
        列出 Docker Compose 项目（快速版，仅使用 docker compose ls）
        
        Returns:
            Compose 项目列表
        """
        ssh = self._get_ssh()
        projects = []
        
        cmd = "docker compose ls --format json 2>/dev/null || docker-compose ls --format json 2>/dev/null"
        
        try:
            exit_code, output, _ = ssh.execute_command(cmd, timeout=5)
            
            if output.strip():
                try:
                    data = json.loads(output)
                    if isinstance(data, list):
                        for p in data:
                            projects.append({
                                "name": p.get("Name", ""),
                                "status": p.get("Status", ""),
                                "path": "",
                                "services": 0
                            })
                except json.JSONDecodeError:
                    logger.warning("解析 Compose 项目列表失败")
            
            return projects
        except Exception as e:
            logger.error(f"获取 Compose 项目列表失败: {e}")
            raise
    
    def list_compose_projects_with_search(self, search_paths: List[str] = None) -> List[dict]:
        """
        列出 Docker Compose 项目（包含目录搜索）
        
        Args:
            search_paths: 搜索路径列表
        
        Returns:
            Compose 项目列表
        """
        ssh = self._get_ssh()
        projects = []
        
        try:
            cmd = "docker compose ls --format json 2>/dev/null || docker-compose ls --format json 2>/dev/null"
            _, output, _ = ssh.execute_command(cmd, timeout=5)
            
            if output.strip():
                try:
                    data = json.loads(output)
                    if isinstance(data, list):
                        for p in data:
                            projects.append({
                                "name": p.get("Name", ""),
                                "status": p.get("Status", ""),
                                "path": "",
                                "services": 0
                            })
                except json.JSONDecodeError:
                    pass
            
            if search_paths is None:
                search_paths = ["/opt/docker-compose", "/opt/compose", "/root/compose"]
            
            find_cmd = "find " + " ".join(search_paths) + " -name 'docker-compose.yml' -o -name 'docker-compose.yaml' 2>/dev/null"
            _, output, _ = ssh.execute_command(find_cmd, timeout=10)
            
            for filepath in output.strip().split('\n'):
                if filepath:
                    path = os.path.dirname(filepath)
                    name = os.path.basename(path)
                    
                    if not any(p["path"] == path for p in projects):
                        projects.append({
                            "name": name,
                            "path": path,
                            "status": "未知",
                            "services": 0
                        })
            
            return projects
        except Exception as e:
            logger.error(f"搜索 Compose 项目失败: {e}")
            raise
    
    def get_compose_file(self, path: str) -> str:
        """
        读取 Compose 文件内容
        
        Args:
            path: 项目路径
        
        Returns:
            YAML 内容
        
        Raises:
            FileNotFoundError: 未找到 Compose 文件
        """
        ssh = self._get_ssh()
        
        for filename in ["docker-compose.yml", "docker-compose.yaml"]:
            filepath = f"{path}/{filename}"
            cmd = f"cat {filepath} 2>/dev/null"
            _, output, _ = ssh.execute_command(cmd, timeout=10)
            if output.strip():
                return output
        
        raise FileNotFoundError(f"未找到 compose 文件: {path}")
    
    def save_compose_file(self, path: str, content: str) -> Tuple[bool, str]:
        """
        保存 Compose 文件
        
        Args:
            path: 项目路径
            content: YAML 内容
        
        Returns:
            (是否成功, 消息)
        """
        ssh = self._get_ssh()
        
        try:
            ssh.execute_command(f"mkdir -p {path}")
            
            cmd = f"cat > {path}/docker-compose.yml << 'EOFCOMPOSE'\n{content}\nEOFCOMPOSE"
            exit_code, output, error = ssh.execute_command(cmd, timeout=10)
            
            if exit_code == 0:
                message = "保存成功"
                self._log_operation("compose", "save_file", path, "success", message)
                return True, message
            else:
                error_msg = error or "保存失败"
                self._log_operation("compose", "save_file", path, "failed", error_msg)
                return False, error_msg
        except Exception as e:
            error_msg = str(e)
            self._log_operation("compose", "save_file", path, "failed", error_msg)
            return False, error_msg
    
    def compose_action(self, path: str, action: str, services: List[str] = None) -> Tuple[bool, str]:
        """
        Compose 项目操作
        
        Args:
            path: 项目路径
            action: 操作类型（up/down/restart/pull）
            services: 指定服务列表（可选）
        
        Returns:
            (是否成功, 消息)
        """
        ssh = self._get_ssh()
        
        try:
            cmd_check = "docker compose version &>/dev/null && echo 'docker compose' || echo 'docker-compose'"
            _, compose_cmd, _ = ssh.execute_command(cmd_check, timeout=5)
            compose_cmd = compose_cmd.strip()
            
            service_str = " ".join(services) if services else ""
            
            if action == "up":
                cmd = f"cd {path} && {compose_cmd} up -d {service_str}"
            elif action == "down":
                cmd = f"cd {path} && {compose_cmd} down"
            elif action == "restart":
                cmd = f"cd {path} && {compose_cmd} restart {service_str}"
            elif action == "pull":
                cmd = f"cd {path} && {compose_cmd} pull {service_str}"
            else:
                return False, f"无效操作: {action}"
            
            exit_code, output, error = ssh.execute_command(cmd, timeout=120)
            
            if exit_code == 0:
                message = output or "操作成功"
                self._log_operation("compose", action, path, "success", message)
                return True, message
            else:
                error_msg = error or output or "操作失败"
                self._log_operation("compose", action, path, "failed", error_msg)
                return False, error_msg
        except Exception as e:
            error_msg = str(e)
            self._log_operation("compose", action, path, "failed", error_msg)
            return False, error_msg
    
    def exec_container(self, container_id: str, command: str) -> Tuple[bool, str]:
        """
        在容器中执行命令
        
        Args:
            container_id: 容器ID
            command: 要执行的命令
        
        Returns:
            (是否成功, 输出内容)
        """
        ssh = self._get_ssh()
        cmd = f"docker exec {container_id} {command}"
        
        try:
            exit_code, output, error = ssh.execute_command(cmd, timeout=30)
            if exit_code == 0:
                self._log_operation("container", "exec", container_id, "success", output)
                return True, output or ""
            else:
                error_msg = error or "执行失败"
                self._log_operation("container", "exec", container_id, "failed", error_msg)
                return False, error_msg
        except Exception as e:
            error_msg = str(e)
            self._log_operation("container", "exec", container_id, "failed", error_msg)
            return False, error_msg
    
    def get_ssh_client(self) -> SSHClient:
        """获取 SSH 客户端（用于 WebSocket）"""
        return self._get_ssh()
