import paramiko
import io

from app.modules.node.schemas import NodeRead


class SSHClient:
    def __init__(self, node: NodeRead):
        self.node = node
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self):
        try:
            if self.node.auth_type == "ssh_key" and self.node.private_key:
                pkey = paramiko.RSAKey.from_private_key(
                    io.StringIO(self.node.private_key)
                )
                self.client.connect(
                    hostname=self.node.host,
                    port=self.node.port,
                    username=self.node.username,
                    pkey=pkey,
                    timeout=10
                )
            else:
                self.client.connect(
                    hostname=self.node.host,
                    port=self.node.port,
                    username=self.node.username,
                    password=self.node.password,
                    timeout=10
                )
            return True
        except Exception as e:
            raise ConnectionError(f"SSH连接失败: {str(e)}")

    def execute_command(self, command: str, timeout=30):
        try:
            _, stdout, stderr = self.client.exec_command(command, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            output = stdout.read().decode('utf-8', errors='replace')
            error = stderr.read().decode('utf-8', errors='replace')
            return exit_code, output, error
        finally:
            self.client.close()

    def close(self):
        self.client.close()
