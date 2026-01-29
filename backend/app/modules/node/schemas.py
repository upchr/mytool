from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Literal
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

class NodeCreate(NodeBase):
    pass

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
