import logging
import traceback
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.exception.exceptions import BusinessException
from app.core.pojo.response import BaseResponse

logger = logging.getLogger(__name__)

def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(BusinessException)
    async def business_exception_handler(request: Request, exc: BusinessException):
        response = BaseResponse.error(
            code=exc.code,
            message=exc.message,
            detail=exc.detail
        )
        return JSONResponse(status_code=200, content=response.dict())

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = [{"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in exc.errors()]
        response = BaseResponse.error(
            code=422,
            message="参数验证失败",
            detail=errors
        )
        return JSONResponse(status_code=200, content=response.dict())

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: Exception):
        logger.debug(f"路径 {request.url.path} 未找到")
        response = BaseResponse.error(
            code=404,
            message="接口不存在",
            detail=f"路径 {request.url.path} 未找到"
        )
        return JSONResponse(status_code=200, content=response.dict())

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"全局异常: {str(exc)}\n{traceback.format_exc()}")

        if isinstance(exc, SQLAlchemyError):
            response = BaseResponse.error(500, "数据库操作失败")
        else:
            response = BaseResponse.error(500, "服务器内部错误")

        return JSONResponse(status_code=200, content=response.dict())
