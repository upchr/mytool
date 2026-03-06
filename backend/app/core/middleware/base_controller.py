from fastapi import Request
from typing import Dict, Any, Optional

class BaseController:
    """基础控制器，提供获取当前用户的方法"""

    def __init__(self, request: Request):
        self.request = request

    def get_current_user(self) -> Dict[str, Any]:
        """获取当前用户"""
        if not hasattr(self.request.state, "user"):
            raise ValueError("用户未认证")
        return self.request.state.user

    def get_current_user_id(self) -> Optional[int]:
        """获取当前用户ID"""
        user = self.get_current_user()
        return user.get("user_id")

    def get_current_username(self) -> Optional[str]:
        """获取当前用户名"""
        user = self.get_current_user()
        return user.get("username")

    def has_role(self, role: str) -> bool:
        """检查是否有指定角色"""
        user = self.get_current_user()
        return user.get("role") == role
