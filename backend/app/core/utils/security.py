import logging
import sys
from pathlib import Path

import bcrypt
import os
import base64
from typing import Optional
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

"""安全工具类 - 密码用 bcrypt，敏感数据用 AES"""
class SecurityManager:

    def __init__(self):
        self.cipher = Fernet(self.get_encryption_key().encode())

    def get_encryption_key(self):
        # 1. 优先从环境变量读取
        key = os.getenv("ENCRYPTION_SECRET_KEY")
        if key:
            return key

        # 2. 否则从 data 目录读取
        if sys.platform.startswith("win"):
            key_path = Path.cwd().parent.parent / "data"
        else:
            # Linux / Docker 挂载卷
            key_path=Path("/toolsplus/data")
        key_path.mkdir(exist_ok=True)
        key_path = f"{key_path}/encryption.key"

        if os.path.exists(key_path):
            with open(key_path) as f:
                return f.read().strip()

        # 3. 都没有则生成并保存
        key = Fernet.generate_key().decode()
        with open(key_path, "w") as f:
            f.write(key)
        logger.info(f"🔑 自动生成加解密密钥: {key_path}")
        return key

    # ========== 密码哈希（bcrypt）==========
    def hash_password(self, password: str) -> str:
        """哈希密码（使用 bcrypt）"""
        if isinstance(password, str):
            password = password.encode('utf-8')
        hashed = bcrypt.hashpw(password, bcrypt.gensalt())
        return hashed.decode('utf-8')

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """验证密码"""
        if isinstance(password, str):
            password = password.encode('utf-8')
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password, hashed_password)

    # ========== 敏感数据加密（AES）==========
    def encrypt_field(self, plaintext: str) -> Optional[str]:
        """加密敏感字段（手机号、邮箱等）"""
        if not plaintext:
            return None
        try:
            encrypted = self.cipher.encrypt(plaintext.encode('utf-8'))
            return '@868@'+base64.urlsafe_b64encode(encrypted).decode('utf-8')
        except Exception as e:
            logger.error(f"加密失败: {e}")
            return None

    def decrypt_field(self, encrypted_text: str) -> Optional[str]:
        """解密敏感字段"""
        if not encrypted_text:
            return None
        try:
            encrypted = base64.urlsafe_b64decode(encrypted_text[5:].encode('utf-8'))
            decrypted = self.cipher.decrypt(encrypted)
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"解密失败: {e}")
            return None

security_manager = SecurityManager()
