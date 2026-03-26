from app.core.sh.ssh_client import SSHClient
from app.modules.node.schemas import NodeRead
from app.modules.node import services as node_services
from app.core.db.database import engine
import json
import re
from typing import List, Optional, Tuple
import os


class DockerService:
    """Docker 操作服务"""
    
    def __init__(self, node_id: int):
        self.node_id = node_id
        self._ssh: Optional[SSHClient] = None
    
    def _get_ssh(self) -> SSHClient:
        """获取 SSH 连接"""
        if not self._ssh:
            node_data = node_services.get_node(engine, self.node_id)
            if not node_data:
                raise ValueError(f"节点 {self.node_id} 不存在")
            node = NodeRead(**node_data)
            self._ssh = SSHClient(node)
            self._ssh.connect()
        return self._ssh
    
    def close(self):
        """关闭连接"""
        if self._ssh:
            self._ssh.close()
            self._ssh = None
    
    def list_containers(self, all: bool = True) -> List[dict]:
        """获取容器列表 - 优化版"""
        ssh = self._get_ssh()
        flag = "-a" if all else ""
        # 使用更高效的格式化输出
        cmd = f"docker ps {flag} --format '{{{{json .}}}}'"
        _, output, _ = ssh.execute_command(cmd, timeout=10)
        
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
    
    def list_containers_fast(self) -> List[dict]:
        """快速获取容器列表（仅运行中的）"""
        ssh = self._get_ssh()
        cmd = "docker ps --format '{{json .}}'"
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
    
    def container_action(self, container_id: str, action: str) -> Tuple[bool, str]:
        """容器操作：start/stop/restart/remove"""
        ssh = self._get_ssh()
        
        valid_actions = ["start", "stop", "restart", "remove"]
        if action not in valid_actions:
            return False, f"无效操作: {action}"
        
        if action == "remove":
            cmd = f"docker rm -f {container_id}"
        else:
            cmd = f"docker {action} {container_id}"
        
        exit_code, output, error = ssh.execute_command(cmd, timeout=30)
        
        if exit_code == 0:
            return True, f"容器 {container_id} 已{action}"
        else:
            return False, error or output
    
    def container_action_async(self, container_id: str, action: str) -> Tuple[bool, str]:
        """容器操作 - 异步模式（后台执行）"""
        ssh = self._get_ssh()
        
        valid_actions = ["start", "stop", "restart", "remove"]
        if action not in valid_actions:
            return False, f"无效操作: {action}"
        
        if action == "remove":
            cmd = f"nohup docker rm -f {container_id} > /dev/null 2>&1 &"
        else:
            cmd = f"nohup docker {action} {container_id} > /dev/null 2>&1 &"
        
        _, output, error = ssh.execute_command(cmd, timeout=5)
        return True, f"容器 {container_id} 正在{action}..."
    
    def get_container_logs(self, container_id: str, tail: int = 100) -> str:
        """获取容器日志"""
        ssh = self._get_ssh()
        cmd = f"docker logs --tail {tail} {container_id} 2>&1"
        _, output, _ = ssh.execute_command(cmd, timeout=30)
        return output
    
    def list_compose_projects(self) -> List[dict]:
        """列出 compose 项目 - 优化版"""
        ssh = self._get_ssh()
        
        projects = []
        
        # 方法1: 使用 docker compose ls (新版本) - 一次性获取
        cmd = "docker compose ls --format json 2>/dev/null || docker-compose ls --format json 2>/dev/null"
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
            except:
                pass
        
        return projects
    
    def list_compose_projects_with_search(self, search_paths: List[str] = None) -> List[dict]:
        """列出 compose 项目 - 包含目录搜索（较慢）"""
        ssh = self._get_ssh()
        
        projects = []
        
        # 先用 docker compose ls
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
            except:
                pass
        
        # 默认搜索路径
        if search_paths is None:
            search_paths = ["/opt/docker-compose", "/opt/compose", "/root/compose"]
        
        # 合并搜索命令 - 一次性执行
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
    
    def get_compose_file(self, path: str) -> str:
        """读取 compose 文件内容"""
        ssh = self._get_ssh()
        
        # 尝试 .yml 和 .yaml
        for filename in ["docker-compose.yml", "docker-compose.yaml"]:
            filepath = f"{path}/{filename}"
            cmd = f"cat {filepath} 2>/dev/null"
            _, output, _ = ssh.execute_command(cmd, timeout=10)
            if output.strip():
                return output
        
        raise FileNotFoundError(f"未找到 compose 文件: {path}")
    
    def save_compose_file(self, path: str, content: str) -> Tuple[bool, str]:
        """保存 compose 文件"""
        ssh = self._get_ssh()
        
        # 确保目录存在
        ssh.execute_command(f"mkdir -p {path}")
        
        # 使用 heredoc 方式写入（避免转义问题）
        cmd = f"cat > {path}/docker-compose.yml << 'EOFCOMPOSE'\n{content}\nEOFCOMPOSE"
        exit_code, output, error = ssh.execute_command(cmd, timeout=10)
        
        if exit_code == 0:
            return True, "保存成功"
        else:
            return False, error or "保存失败"
    
    def compose_action(self, path: str, action: str, services: List[str] = None) -> Tuple[bool, str]:
        """Compose 操作：up/down/restart/pull"""
        ssh = self._get_ssh()
        
        # 检测 compose 命令
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
            return True, output or "操作成功"
        else:
            return False, error or output
    
    def exec_container(self, container_id: str, command: str) -> Tuple[bool, str]:
        """在容器中执行命令"""
        ssh = self._get_ssh()
        cmd = f"docker exec {container_id} {command}"
        exit_code, output, error = ssh.execute_command(cmd, timeout=30)
        return exit_code == 0, output or error
    
    def get_ssh_client(self) -> SSHClient:
        """获取 SSH 客户端（用于 WebSocket）"""
        return self._get_ssh()
