from typing import Any

class BusinessException(Exception):
    """业务异常基类"""
    def __init__(self, code: int, message: str, detail: Any = None):
        self.code = code
        self.message = message
        self.detail = detail

class NotFoundException(BusinessException):
    def __init__(self, message: str = "资源不存在", detail: Any = None):
        super().__init__(404, message, detail)

class UnauthorizedException(BusinessException):
    def __init__(self, message: str = "未授权访问", detail: Any = None):
        super().__init__(401, message, detail)

class UnInitedException(BusinessException):
    def __init__(self, message: str = "未授权访问", detail: Any = None):
        super().__init__(403, message, detail)

class ValidationException(BusinessException):
    def __init__(self, message: str = "参数验证失败", detail: Any = None):
        super().__init__(422, message, detail)

class ServerException(BusinessException):
    def __init__(self, message: str = "服务器内部错误", detail: Any = None):
        super().__init__(500, message, detail)
