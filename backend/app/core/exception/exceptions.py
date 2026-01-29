from fastapi import HTTPException
from typing import Any, Optional

class BusinessException(HTTPException):
    """业务异常基类"""
    def __init__(
            self,
            code: int = 400,
            message: str = "业务异常",
            detail: Any = None
    ):
        super().__init__(status_code=200, detail={
            "code": code,
            "message": message,
            "detail": detail
        })

class NotFoundException(BusinessException):
    """资源不存在异常"""
    def __init__(self, message: str = "资源不存在", detail: Any = None):
        super().__init__(code=404, message=message, detail=detail)

class UnauthorizedException(BusinessException):
    """未授权异常"""
    def __init__(self, message: str = "未授权访问", detail: Any = None):
        super().__init__(code=401, message=message, detail=detail)

class ValidationException(BusinessException):
    """验证异常"""
    def __init__(self, message: str = "参数验证失败", detail: Any = None):
        super().__init__(code=422, message=message, detail=detail)

class ServerException(BusinessException):
    """服务器异常"""
    def __init__(self, message: str = "服务器内部错误", detail: Any = None):
        super().__init__(code=500, message=message, detail=detail)
