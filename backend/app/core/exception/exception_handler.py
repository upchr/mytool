import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import traceback
from app.core.exception.exceptions import BusinessException

logger = logging.getLogger(__name__)

def setup_exception_handlers(app: FastAPI):
    """设置全局异常处理器"""

    @app.exception_handler(BusinessException)
    async def business_exception_handler(request: Request, exc: BusinessException):
        """业务异常处理器"""
        return JSONResponse(
            status_code=200,
            content={
                "code": exc.detail["code"],
                "message": exc.detail["message"],
                "detail": exc.detail["detail"]
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """参数验证异常处理器"""
        errors = []
        for error in exc.errors():
            errors.append({
                "loc": error["loc"],
                "msg": error["msg"],
                "type": error["type"]
            })

        return JSONResponse(
            status_code=200,
            content={
                "code": 422,
                "message": "参数验证失败",
                "detail": errors
            }
        )

    @app.exception_handler(404)
    async def not_found_exception_handler(request: Request, exc: Exception):
        logger.debug(f"路径 {request.url.path} 未找到")
        """404异常处理器"""
        return JSONResponse(
            status_code=200,
            content={
                "code": 404,
                "message": "接口不存在",
                "detail": f"路径 {request.url.path} 未找到"
            }
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """全局异常处理器"""
        # 记录错误日志
        logger.error(f"全局异常: {str(exc)}")
        logger.error(traceback.format_exc())

        # 如果是数据库错误
        if isinstance(exc, SQLAlchemyError):
            return JSONResponse(
                status_code=200,
                content={
                    "code": 500,
                    "message": "数据库操作失败",
                }
            )

        return JSONResponse(
            status_code=200,
            content={
                "code": 500,
                "message": "服务器内部错误",
            }
        )
