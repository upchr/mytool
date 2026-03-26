from app.core.sh.ssh_client import SSHClient
from app.modules.node.schemas import NodeRead
from app.modules.node import services as node_services
from app.core.db.database import engine
import json
import re
from typing import List, Optional, Tuple


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
        """获取容器列表"""
        ssh = self._get_ssh()
        flag = "-a" if all else ""
        cmd = f"docker ps {flag} --format '{{{{json .}}}}'"
        _, output, _ = ssh.execute_command(cmd)
        
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
        
        exit_code, output, error = ssh.execute_command(cmd)
        
        if exit_code == 0:
            return True, f"容器 {container_id} 已{action}"
        else:
            return False, error or output
    
    def get_container_logs(self, container_id: str, tail: int = 100) -> str:
        """获取容器日志"""
        ssh = self._get_ssh()
        cmd = f"docker logs --tail {tail} {container_id} 2>&1"
        _, output, _ = ssh.execute_command(cmd)
        return output
    
    def list_compose_projects(self) -> List[dict]:
        """列出 compose 项目"""
        ssh = self._get_ssh()
        
        # 方法1: 使用 docker compose ls (新版本)
        cmd = "docker compose ls --format json 2>/dev/null || docker-compose ls 2>/dev/null"
        exit_code, output, _ = ssh.execute_command(cmd)
        
        projects = []
        if output.strip():
            try:
                data = json.loads(output)
                if isinstance(data, list):
                    for p in data:
                        projects.append({
                            "name": p.get("Name", ""),
                            "status": p.get("Status", ""),
                            "path": ""
                        })
            except:
                pass
        
        # 方法2: 查找常见目录下的 docker-compose.yml
        search_paths = [
            "/opt/docker-compose",
            "/opt/compose",
            "/root/compose",
            "/home/*/compose",
            "/home/*/docker-compose"
        ]
        
        for search_path in search_paths:
            cmd = f"find {search_path} -name 'docker-compose.yml' -o -name 'docker-compose.yaml' 2>/dev/null"
            _, output, _ = ssh.execute_command(cmd)
            
            for filepath in output.strip().split('\n'):
                if filepath:
                    import os
                    path = os.path.dirname(filepath)
                    name = os.path.basename(path)
                    
                    # 检查是否已存在
                    if not any(p["path"] == path for p in projects):
                        # 获取服务数量
                        cmd = f"grep -c '^  [a-z]' {filepath} 2>/dev/null || echo 0"
                        _, count_output, _ = ssh.execute_command(cmd)
                        try:
                            services = int(count_output.strip())
                        except:
                            services = 0
                        
                        projects.append({
                            "name": name,
                            "path": path,
                            "status": "未知",
                            "services": services
                        })
        
        return projects
    
    def get_compose_file(self, path: str) -> str:
        """读取 compose 文件内容"""
        ssh = self._get_ssh()
        
        # 尝试 .yml 和 .yaml
        for filename in ["docker-compose.yml", "docker-compose.yaml"]:
            filepath = f"{path}/{filename}"
            cmd = f"cat {filepath} 2>/dev/null"
            _, output, _ = ssh.execute_command(cmd)
            if output.strip():
                return output
        
        raise FileNotFoundError(f"未找到 compose 文件: {path}")
    
    def save_compose_file(self, path: str, content: str) -> Tuple[bool, str]:
        """保存 compose 文件"""
        ssh = self._get_ssh()
        
        # 确保目录存在
        ssh.execute_command(f"mkdir -p {path}")
        
        # 写入文件
        import io
        fileobj = io.BytesIO(content.encode('utf-8'))
        
        # 使用 heredoc 方式写入（避免转义问题）
        cmd = f"cat > {path}/docker-compose.yml << 'EOFCOMPOSE'\n{content}\nEOFCOMPOSE"
        exit_code, output, error = ssh.execute_command(cmd)
        
        if exit_code == 0:
            return True, "保存成功"
        else:
            return False, error or "保存失败"
    
    def compose_action(self, path: str, action: str, services: List[str] = None) -> Tuple[bool, str]:
        """Compose 操作：up/down/restart/pull"""
        ssh = self._get_ssh()
        
        # 检测 compose 命令
        cmd_check = "docker compose version &>/dev/null && echo 'docker compose' || echo 'docker-compose'"
        _, compose_cmd, _ = ssh.execute_command(cmd_check)
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
        
        exit_code, output, error = ssh.execute_command(cmd, timeout=60)
        
        if exit_code == 0:
            return True, output or "操作成功"
        else:
            return False, error or output
    
    def exec_container(self, container_id: str, command: str) -> Tuple[bool, str]:
        """在容器中执行命令"""
        ssh = self._get_ssh()
        cmd = f"docker exec {container_id} {command}"
        exit_code, output, error = ssh.execute_command(cmd)
        return exit_code == 0, output or error
