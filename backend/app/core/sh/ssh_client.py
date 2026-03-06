# app/core/sh/ssh_client.py
from app.modules.node.schemas import NodeRead

import paramiko
import io
import os

class SSHClient:
    def __init__(self, node: NodeRead):
        self.node = node
        self.client = paramiko.SSHClient()
        self.sftp = None  # SFTP 客户端
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
        except Exception as e:
            raise Exception(f"命令执行失败: {str(e)}")

    def close(self):
        if self.sftp:
            self.sftp.close()
        self.client.close()

    # ========== 文件传输方法 ==========

    def _get_sftp(self):
        """获取 SFTP 客户端（懒加载）"""
        if not self.sftp:
            self.sftp = self.client.open_sftp()
        return self.sftp

    def upload_file(self, local_path: str, remote_path: str, callback=None):
        """
        上传文件到远程服务器

        Args:
            local_path: 本地文件路径
            remote_path: 远程文件路径
            callback: 进度回调函数 (bytes_sent, total_bytes)
        """
        try:
            sftp = self._get_sftp()
            # 确保远程目录存在
            remote_dir = os.path.dirname(remote_path)
            try:
                sftp.stat(remote_dir)
            except FileNotFoundError:
                self.execute_command(f"mkdir -p {remote_dir}")

            # 上传文件
            sftp.put(local_path, remote_path, callback=callback)
            return True
        except Exception as e:
            raise Exception(f"上传文件失败: {str(e)}")

    def download_file(self, remote_path: str, local_path: str, callback=None):
        """
        从远程服务器下载文件

        Args:
            remote_path: 远程文件路径
            local_path: 本地保存路径
            callback: 进度回调函数 (bytes_received, total_bytes)
        """
        try:
            sftp = self._get_sftp()
            # 确保本地目录存在
            local_dir = os.path.dirname(local_path)
            os.makedirs(local_dir, exist_ok=True)

            # 下载文件
            sftp.get(remote_path, local_path, callback=callback)
            return True
        except Exception as e:
            raise Exception(f"下载文件失败: {str(e)}")

    def upload_fileobj(self, fileobj, remote_path: str):
        """
        上传文件对象（适用于内存中的文件）

        Args:
            fileobj: 文件类对象（如 BytesIO）
            remote_path: 远程文件路径
        """
        try:
            sftp = self._get_sftp()
            with sftp.open(remote_path, 'wb') as f:
                f.write(fileobj.read())
            return True
        except Exception as e:
            raise Exception(f"上传文件对象失败: {str(e)}")

    def download_fileobj(self, remote_path: str):
        """
        下载文件到内存

        Returns:
            BytesIO 对象
        """
        try:
            sftp = self._get_sftp()
            fileobj = io.BytesIO()
            with sftp.open(remote_path, 'rb') as f:
                fileobj.write(f.read())
            fileobj.seek(0)
            return fileobj
        except Exception as e:
            raise Exception(f"下载文件到内存失败: {str(e)}")

    def list_files(self, remote_path: str = '.'):
        """列出远程目录下的文件"""
        try:
            sftp = self._get_sftp()
            return sftp.listdir(remote_path)
        except Exception as e:
            raise Exception(f"列出文件失败: {str(e)}")

    def list_files_attr(self, remote_path: str = '.'):
        """列出远程目录下的文件详细信息"""
        try:
            sftp = self._get_sftp()
            return sftp.listdir_attr(remote_path)
        except Exception as e:
            raise Exception(f"列出文件详情失败: {str(e)}")

    def stat(self, remote_path: str):
        """获取远程文件状态"""
        try:
            sftp = self._get_sftp()
            return sftp.stat(remote_path)
        except Exception as e:
            raise Exception(f"获取文件状态失败: {str(e)}")

    def remove_file(self, remote_path: str):
        """删除远程文件"""
        try:
            sftp = self._get_sftp()
            sftp.remove(remote_path)
            return True
        except Exception as e:
            raise Exception(f"删除文件失败: {str(e)}")

    def rename_file(self, old_path: str, new_path: str):
        """重命名远程文件"""
        try:
            sftp = self._get_sftp()
            sftp.rename(old_path, new_path)
            return True
        except Exception as e:
            raise Exception(f"重命名文件失败: {str(e)}")

    def mkdir(self, remote_path: str):
        """创建远程目录"""
        try:
            sftp = self._get_sftp()
            sftp.mkdir(remote_path)
            return True
        except Exception as e:
            raise Exception(f"创建目录失败: {str(e)}")

    def rmdir(self, remote_path: str):
        """删除远程目录"""
        try:
            sftp = self._get_sftp()
            sftp.rmdir(remote_path)
            return True
        except Exception as e:
            raise Exception(f"删除目录失败: {str(e)}")

    def exists(self, remote_path: str) -> bool:
        """检查远程文件/目录是否存在"""
        try:
            sftp = self._get_sftp()
            sftp.stat(remote_path)
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            raise Exception(f"检查文件存在失败: {str(e)}")

if __name__ == "__main__":
    # 使用示例
    node = NodeRead(
        id='1',
        name='1',
        host="192.168.1.180",
        port=34567,
        username="root",
        auth_type="password",
        password="password"
    )

    ssh = SSHClient(node)


    try:
        # 重要：必须先连接！
        if ssh.connect():
            print("SSH连接成功")

        # 1. 上传本地文件
        ssh.upload_file("P:\workspace\project\mytool\data\\a.py", "/remote/file.txt")

        # 2. 上传内存中的文件
        file_data = io.BytesIO(b"Hello, World!")
        ssh.upload_fileobj(file_data, "/remote/hello.txt")

        # 3. 下载文件
        ssh.download_file("/remote/file.txt", "/local/downloaded.txt")

        # 4. 下载到内存
        fileobj = ssh.download_fileobj("/remote/hello.txt")
        content = fileobj.read().decode()
        print(f"文件内容: {content}")

        # 5. 列出文件
        files = ssh.list_files("/remote")
        print(f"远程文件: {files}")

        # 6. 检查文件是否存在
        if ssh.exists("/remote/file.txt"):
            print("文件存在")

        # 7. 删除文件
        ssh.remove_file("/remote/hello.txt")

        # 8. 创建目录
        ssh.mkdir("/remote/newdir")

    finally:
        ssh.close()
