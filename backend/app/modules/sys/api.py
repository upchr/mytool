from sqlalchemy import select,update

from app.core.db.database import engine, metadata
from fastapi import APIRouter
import logging
from datetime import datetime

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


@router.get("/runtime")
def get_runtime():
    """
    获取应用运行时长
    返回应用启动时间、当前时间和运行时长（秒）
    """
    with engine.connect() as conn:
        stmt = select(system_config_table.c.app_start_time)
        start_time = conn.execute(stmt).scalar()

        if not start_time:
            return BaseResponse.success({
                "start_time": None,
                "current_time": datetime.now().isoformat(),
                "runtime_seconds": 0,
                "runtime_str": "未启动"
            })

        start_time = datetime.fromisoformat(start_time) if isinstance(start_time, str) else start_time
        current_time = datetime.now()
        runtime_seconds = int((current_time - start_time).total_seconds())

        # 格式化运行时长
        days = runtime_seconds // 86400
        hours = (runtime_seconds % 86400) // 3600
        minutes = (runtime_seconds % 3600) // 60
        seconds = runtime_seconds % 60

        runtime_str = []
        if days > 0:
            runtime_str.append(f"{days}天")
        if hours > 0:
            runtime_str.append(f"{hours}小时")
        if minutes > 0:
            runtime_str.append(f"{minutes}分钟")
        if seconds > 0 or len(runtime_str) == 0:
            runtime_str.append(f"{seconds}秒")

        return BaseResponse.success({
            "start_time": start_time.isoformat(),
            "current_time": current_time.isoformat(),
            "runtime_seconds": runtime_seconds,
            "runtime_str": "".join(runtime_str)
        })

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
            token = create_jwt_token({"user_id": 1, "username": "admin", "role": "admin"})
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


