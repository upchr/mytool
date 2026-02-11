from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Literal
# from app.core.safe import security_manager
# 节点相关
class NodeBase(BaseModel):
    name: str
    host: str
    port: int = 22
    username: str
    auth_type: str = "password"
    password: Optional[str] = None
    private_key: Optional[str] = None
    is_active: bool = True


    # def decrypt_sensitive_fields(self):
    #     """解密敏感字段（用于返回给前端）"""
    #     decrypted = self.model_copy()
    #     if decrypted.password:
    #         decrypted.password = security_manager.decrypt_field(decrypted.password)
    #     if decrypted.private_key:
    #         decrypted.private_key = security_manager.decrypt_field(decrypted.private_key)
    #     return decrypted



class NodeCreate(NodeBase):
    pass
    # @field_validator('password', mode='before')
    # @classmethod
    # def encrypt_password(cls, v):
    #     """输入时自动加密密码"""
    #     if v is not None and isinstance(v, str):
    #         # 如果已经是加密格式（包含 base64 编码特征），则不重复加密
    #         if v.startswith('@868@') or len(v) > 50:
    #             return v  # 假设已经是加密的
    #         return security_manager.encrypt_field(v)
    #     return v
    #
    # @field_validator('private_key', mode='before')
    # @classmethod
    # def encrypt_private_key(cls, v):
    #     """输入时自动加密私钥"""
    #     if v is not None and isinstance(v, str):
    #         if v.startswith('@868@') or len(v) > 50:
    #             return v  # 假设已经是加密的
    #         return security_manager.encrypt_field(v)
    #     return v

class NodeRead(NodeBase):
    id: int

    model_config = {"from_attributes": True}


class NodeRequest(BaseModel):
    node_ids: List[int]

class CredentialTemplateCreate(BaseModel):
    name: str
    username: str
    auth_type: Literal['password', 'ssh_key']
    password: Optional[str] = None
    private_key: Optional[str] = None

    # @model_validator(mode='after')
    # def check_auth_fields(self):
    #     if self.auth_type == 'password' and not self.password:
    #         raise ValueError('密码认证必须提供密码')
    #     if self.auth_type == 'ssh_key' and not self.private_key:
    #         raise ValueError('SSH密钥认证必须提供私钥')
    #     return self

class CredentialTemplateRead(CredentialTemplateCreate):
    id: int
    is_active: bool

    class Config:
        from_attributes = True
