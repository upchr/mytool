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
    def add_cors_headers(response: JSONResponse) -> JSONResponse:
        """为响应添加 CORS header"""
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response

    @app.exception_handler(BusinessException)
    async def business_exception_handler(request: Request, exc: BusinessException):
        response = BaseResponse.error(
            code=exc.code,
            message=exc.message,
            detail=exc.detail
        )
        logger.error(f"业务异常: {exc.code} - {exc.message} - {exc.detail}")
        return add_cors_headers(JSONResponse(status_code=exc.code, content=response.dict()))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = [{"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in exc.errors()]
        response = BaseResponse.error(
            code=422,
            message="参数验证失败",
            detail=errors
        )
        return add_cors_headers(JSONResponse(status_code=422, content=response.dict()))

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: Exception):
        logger.error(f"路径 {request.url.path} 未找到")
        response = BaseResponse.error(
            code=404,
            message="接口不存在",
            detail=f"路径 {request.url.path} 未找到"
        )
        return add_cors_headers(JSONResponse(status_code=404, content=response.dict()))

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        out_flag = True

        if isinstance(exc, SQLAlchemyError):
            response = BaseResponse.error(500, "数据库操作失败")
        elif isinstance(exc, BusinessException):
            response = BaseResponse.error(
                code=exc.code,
                message=exc.message,
                detail=exc.detail
            )
            out_flag = False
        else:
            response = BaseResponse.error(500, "服务器内部错误")

        if out_flag:
            logger.error(f"全局异常: {str(exc)}\n{traceback.format_exc()}")

        # 这里必须使用响应体中的 code，而不是直接访问 exc.code（很多异常没有 code 属性）
        return add_cors_headers(JSONResponse(status_code=response.code, content=response.dict()))
