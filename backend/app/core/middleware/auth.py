# backend/app/core/middleware/auth.py
from fastapi import Request, HTTPException
from sqlalchemy import select
from app.core.db.database import engine
from app.core.exception.exceptions import UnauthorizedException, ServerException, UnInitedException
from app.core.utils.jwt import verify_jwt_token
from app.modules.sys import system_config_table
import asyncio
from functools import wraps

def sync_to_async(func):
    """将同步函数转换为异步函数的装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 在线程池中执行同步函数
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper

# 将数据库查询包装为异步
@sync_to_async
def check_initialization_sync():
    with engine.connect() as conn:
        stmt = select(system_config_table.c.is_initialized)
        result = conn.execute(stmt).scalar()
        return result

async def check_initialization_middleware(request: Request, call_next):
    public_paths = [
        "/sys/init/check",
        "/sys/init/setup",
        "/version",
    ]
    if any(request.url.path.startswith(path) for path in public_paths):
        return await call_next(request)

    is_initialized = await check_initialization_sync()

    if not is_initialized:
        raise UnInitedException(detail=f"系统密码未初始化！")

    return await call_next(request)


async def jwt_auth_middleware(request: Request, call_next):
    public_paths = [
        "/sys/init/check",
        "/sys/init/setup",
        "/sys/login",
        "/version",
        "/example",
    ]

    if any(request.url.path.startswith(path) for path in public_paths):
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise UnauthorizedException(detail=f"缺少认证 token。请重新登录！")

    token = auth_header.split(" ")[1]

    try:
        payload = verify_jwt_token(token)
        request.state.user = payload
    except HTTPException as e:
        raise ServerException(detail=f"${e.detail}")
    except Exception:
        raise UnauthorizedException(detail=f"无效的 token。请重新登录！")

    return await call_next(request)
