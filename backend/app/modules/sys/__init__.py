from sqlalchemy import select,update

from app.core.db.database import engine, metadata
from . import  models
from fastapi import APIRouter
import logging

from .models import system_config_table
from .schemas import SysBase, ResetSysBase
from ...core.exception.exceptions import UnauthorizedException, ServerException, ValidationException
from ...core.pojo.response import BaseResponse
from ...core.utils.jwt import create_jwt_token
from ...core.utils.security import security_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sys", tags=["sys"])


@router.get("/init/check")
def check_initialization():
    with engine.connect() as conn:
        stmt = select(system_config_table.c.is_initialized)
        is_initialized = conn.execute(stmt).scalar()
        return BaseResponse.success({"is_initialized": bool(is_initialized)})

@router.post("/init/setup")
def setup_initialization(req: SysBase):
    if len(req.password) < 6:
        raise ValidationException(detail="密码至少6位")

    # 哈希密码
    password_hash = security_manager.hash_password(req.password)

    with engine.begin() as conn:
        # 检查是否已初始化
        check_stmt = select(system_config_table.c.is_initialized)
        if conn.execute(check_stmt).scalar():
            raise ServerException(detail="系统已初始化")

        # 插入初始化数据
        conn.execute(
            system_config_table.insert().values(
                id=1,
                is_initialized=True,
                admin_password_hash=password_hash
            )
        )

    return BaseResponse.success({"message": "初始化成功"})

@router.post("/login")
def login(req: SysBase):
    with engine.connect() as conn:
        stmt = select(system_config_table.c.admin_password_hash)
        password_hash = conn.execute(stmt).scalar()

        if not password_hash:
            raise UnauthorizedException(detail="系统未初始化")

        if security_manager.verify_password(req.password, password_hash):
            # 生成 JWT token
            token = create_jwt_token({"user_id": 1, "role": "admin"})
            return BaseResponse.success({"token": token})

        else:
            raise ValidationException(detail="密码错误！")

@router.post("/resetPassword")
def reset_password(req: ResetSysBase):
    if len(req.password) < 6:
        raise ValidationException(detail="密码至少6位")

    with engine.begin() as conn:
        stmt = select(system_config_table.c.admin_password_hash)
        password_hash = conn.execute(stmt).scalar()
        if not password_hash:
            raise UnauthorizedException(detail="系统未初始化")

        if not security_manager.verify_password(req.old_password, password_hash):
            raise ValidationException(detail="密码错误！")

        # 哈希密码
        password_hash = security_manager.hash_password(req.password)
        stmt = (
            update(system_config_table)
            .where(system_config_table.c.id == 1)
            .values(admin_password_hash=password_hash)
        )
        conn.execute(stmt)
        return BaseResponse.success(message="密码修改成功")


