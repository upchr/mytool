from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class BaseResponse(BaseModel, Generic[T]):
    code: int
    message: str
    data: Optional[T] = None

    @classmethod
    def success(cls, data: T = None, message: str = "success") -> "BaseResponse[T]":
        return cls(code=200, message=message, data=data)

    @classmethod
    def error(cls, code: int, message: str, detail: Any = None) -> "BaseResponse[Any]":
        return cls(code=code, message=message, data=detail)
