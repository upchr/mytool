from sqlalchemy import select, update, delete, and_
from datetime import datetime, timedelta
import random
import string

from app.core.db.database import engine, metadata
from fastapi import APIRouter, Request
import logging

from .models import (
    system_config_table,
    login_failed_records_table,
    password_reset_codes_table
)
from .schemas import (
    SysBase,
    ResetSysBase,
    LoginRequest,
    LoginResponse,
    SendResetCodeRequest,
    VerifyResetCodeRequest,
    ResetPasswordResponse
)
from ...core.exception.exceptions import UnauthorizedException, ServerException, ValidationException
from ...core.pojo.response import BaseResponse
from ...core.utils.jwt import create_jwt_token
from ...core.utils.security import security_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sys", tags=["sys"])

# 登录失败次数限制
MAX_LOGIN_ATTEMPTS = 5
LOGIN_ATTEMPT_WINDOW = timedelta(minutes=15)  # 15分钟内
RESET_CODE_EXPIRE_MINUTES = 10  # 验证码10分钟过期

# 密码重置验证码速率限制
RESET_CODE_RATE_LIMIT = 5  # 最大请求次数
RESET_CODE_RATE_WINDOW = timedelta(minutes=3)  # 3分钟内

# 内存存储验证码：{ip_address: {"code": "xxx", "expires_at": datetime}}
reset_codes_cache = {}

# 内存存储请求记录：{ip_address: [datetime1, datetime2, ...]}
reset_code_request_cache = {}


def get_client_ip(request: Request) -> str:
    """获取客户端IP地址"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host if request.client else "unknown"


def check_reset_code_rate_limit(ip_address: str) -> tuple[bool, int, int | None]:
    """
    检查密码重置验证码请求速率限制（滑动窗口算法）
    
    Args:
        ip_address: IP地址
    
    Returns:
        (是否允许请求, 剩余次数, 等待秒数(拒绝时))
    """
    now = datetime.now()
    
    # 获取该IP的请求记录
    request_times = reset_code_request_cache.get(ip_address, [])
    
    # 移除窗口外的旧记录
    window_start = now - RESET_CODE_RATE_WINDOW
    request_times = [t for t in request_times if t > window_start]
    
    # 检查是否超过限制
    if len(request_times) >= RESET_CODE_RATE_LIMIT:
        # 计算最早请求的剩余时间
        oldest_request = request_times[0]
        remaining_seconds = int((oldest_request + RESET_CODE_RATE_WINDOW - now).total_seconds())
        logger.warning(f"密码重置验证码请求超过速率限制: IP={ip_address}, 请等待{remaining_seconds}秒")
        return False, 0, remaining_seconds
    
    # 添加当前请求时间
    request_times.append(now)
    reset_code_request_cache[ip_address] = request_times
    
    # 计算剩余次数
    remaining_attempts = RESET_CODE_RATE_LIMIT - len(request_times)
    
    logger.info(f"密码重置验证码请求速率检查通过: IP={ip_address}, 剩余次数={remaining_attempts}")
    return True, remaining_attempts, None


def check_login_attempts(ip_address: str) -> tuple[int, bool]:
    """
    检查登录尝试次数
    
    Args:
        ip_address: IP地址
    
    Returns:
        (失败次数, 是否被锁定)
    """
    try:
        with engine.connect() as conn:
            # 计算时间窗口
            window_start = datetime.now() - LOGIN_ATTEMPT_WINDOW
            
            # 查询时间窗口内的失败次数
            stmt = (
                select(login_failed_records_table)
                .where(
                    and_(
                        login_failed_records_table.c.ip_address == ip_address,
                        login_failed_records_table.c.failed_time >= window_start
                    )
                )
            )
            result = conn.execute(stmt).fetchall()
            
            failed_count = len(result)
            is_locked = failed_count >= MAX_LOGIN_ATTEMPTS
            
            return failed_count, is_locked
    except Exception as e:
        logger.error(f"检查登录尝试次数失败: {e}")
        return 0, False


def record_login_failure(ip_address: str, user_agent: str = None):
    """
    记录登录失败
    
    Args:
        ip_address: IP地址
        user_agent: 用户代理
    """
    try:
        with engine.begin() as conn:
            conn.execute(
                login_failed_records_table.insert().values(
                    ip_address=ip_address,
                    user_agent=user_agent,
                    failed_time=datetime.now()
                )
            )
            logger.warning(f"记录登录失败: IP={ip_address}")
    except Exception as e:
        logger.error(f"记录登录失败失败: {e}")


def clear_login_attempts(ip_address: str):
    """
    清除登录失败记录
    
    Args:
        ip_address: IP地址
    """
    try:
        with engine.begin() as conn:
            stmt = (
                delete(login_failed_records_table)
                .where(login_failed_records_table.c.ip_address == ip_address)
            )
            conn.execute(stmt)
            logger.info(f"清除登录失败记录: IP={ip_address}")
    except Exception as e:
        logger.error(f"清除登录失败记录失败: {e}")


def generate_reset_code() -> str:
    """生成6位数字验证码"""
    return ''.join(random.choices(string.digits, k=6))


async def send_reset_notification(code: str, ip_address: str) -> bool:
    """
    发送密码重置验证码通知
    
    Args:
        code: 验证码
        ip_address: IP地址
    
    Returns:
        是否发送成功
    """
    try:
        from app.modules.notify.handler.manager import notification_manager
        
        # 检查是否有可用的通知服务
        services = notification_manager.get_all_services(enabled_only=True)
        
        if not services:
            logger.warning("没有可用的通知服务，无法发送重置验证码")
            return False
        
        # 发送通知到所有启用的服务
        title = "🔐 密码重置验证码"
        content = f"""您的密码重置验证码是：{code}

验证码有效期为10分钟，请尽快使用。

如果这不是您本人的操作，请忽略此消息。

IP地址：{ip_address}
时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        
        results = await notification_manager.send_broadcast(
            title=title,
            content=content
        )
        
        # 检查是否有至少一个发送成功
        success_count = sum(1 for r in results if r.get('success'))
        
        if success_count > 0:
            logger.info(f"密码重置验证码已发送: IP={ip_address}, 成功={success_count}/{len(results)}")
            return True
        else:
            logger.error(f"密码重置验证码发送失败: IP={ip_address}")
            return False
            
    except Exception as e:
        logger.error(f"发送密码重置验证码异常: {e}")
        return False


@router.get("/init/check")
def check_initialization():
    """检查系统是否已初始化"""
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
def setup_initialization(req: SysBase, request: Request):
    """
    系统初始化
    
    Args:
        req: 初始化请求（密码）
        request: HTTP请求对象
    
    Returns:
        初始化结果
    """
    if len(req.password) < 6:
        raise ValidationException(detail="密码至少6位")

    # 哈希密码
    password_hash = security_manager.hash_password(req.password)

    with engine.begin() as conn:
        # 检查是否已初始化
        check_stmt = select(system_config_table.c.is_initialized)
        result = conn.execute(check_stmt).scalar()
        if result:
            raise ServerException(detail="系统已初始化")

        # 更新初始化数据
        conn.execute(
            system_config_table.update()
            .where(system_config_table.c.id == 1)
            .values(
                is_initialized=True,
                admin_password_hash=password_hash
            )
        )

    logger.info(f"系统初始化成功: IP={get_client_ip(request)}")
    return BaseResponse.success({"message": "初始化成功"})


@router.post("/login")
def login(req: LoginRequest, request: Request):
    """
    用户登录
    
    Args:
        req: 登录请求（密码）
        request: HTTP请求对象
    
    Returns:
        登录结果（包含token和剩余尝试次数）
    """
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "")
    
    # 检查登录尝试次数
    failed_count, is_locked = check_login_attempts(ip_address)
    
    if is_locked:
        remaining_time = LOGIN_ATTEMPT_WINDOW - (datetime.now() - datetime.now())
        raise ValidationException(
            detail=f"登录失败次数过多，账户已锁定。请15分钟后再试或使用密码重置功能。"
        )
    
    with engine.connect() as conn:
        stmt = select(system_config_table.c.admin_password_hash)
        password_hash = conn.execute(stmt).scalar()

        if not password_hash:
            raise UnauthorizedException(detail="系统未初始化")

        if security_manager.verify_password(req.password, password_hash):
            # 登录成功，清除失败记录
            clear_login_attempts(ip_address)
            
            # 生成 JWT token
            token = create_jwt_token({"user_id": 1, "username": "admin", "role": "admin"})
            
            logger.info(f"用户登录成功: IP={ip_address}")
            return BaseResponse.success(data=LoginResponse(token=token, remaining_attempts=None), message="登录成功")
        else:
            # 登录失败，记录失败
            record_login_failure(ip_address, user_agent)
            
            # 重新计算失败次数
            failed_count += 1
            remaining_attempts = MAX_LOGIN_ATTEMPTS - failed_count
            
            # 检查是否达到5次
            if failed_count >= MAX_LOGIN_ATTEMPTS:
                # 发送通知提醒
                try:
                    from app.modules.notify.handler.manager import notification_manager
                    title = "⚠️ 登录安全提醒"
                    content = f"""检测到多次登录失败！

IP地址：{ip_address}
失败次数：{failed_count}
时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

请检查是否为本人操作，如非本人操作请及时修改密码。"""
                    
                    import asyncio
                    asyncio.create_task(notification_manager.send_broadcast(title=title, content=content))
                    logger.warning(f"登录失败达到5次，已发送通知: IP={ip_address}")
                except Exception as e:
                    logger.error(f"发送登录失败通知失败: {e}")
                
                raise ValidationException(
                    detail=f"登录失败次数过多，账户已锁定。请15分钟后再试或使用密码重置功能。",
                    message="登录失败次数过多"
                )
            
            logger.warning(f"用户登录失败: IP={ip_address}, 失败次数={failed_count}")
            raise ValidationException(
                detail=f"密码错误！剩余尝试次数：{remaining_attempts}",
                message="密码错误"
            )


@router.post("/resetPassword")
def reset_password(req: ResetSysBase, request: Request):
    """
    修改密码（需要旧密码）
    
    Args:
        req: 重置密码请求（旧密码和新密码）
        request: HTTP请求对象
    
    Returns:
        修改结果
    """
    ip_address = get_client_ip(request)
    
    if len(req.password) < 6:
        raise ValidationException(detail="密码至少6位")

    with engine.begin() as conn:
        stmt = select(system_config_table.c.admin_password_hash)
        password_hash = conn.execute(stmt).scalar()
        if not password_hash:
            raise UnauthorizedException(detail="系统未初始化")

        if not security_manager.verify_password(req.old_password, password_hash):
            raise ValidationException(detail="旧密码错误！")

        # 哈希新密码
        password_hash = security_manager.hash_password(req.password)
        stmt = (
            update(system_config_table)
            .where(system_config_table.c.id == 1)
            .values(admin_password_hash=password_hash)
        )
        conn.execute(stmt)
        
        logger.info(f"用户修改密码成功: IP={ip_address}")
        return BaseResponse.success(message="密码修改成功")


@router.post("/password-reset/send-code")
async def send_reset_code(request: Request):
    """
    发送密码重置验证码
    
    Args:
        request: HTTP请求对象
    
    Returns:
        发送结果
    """
    ip_address = get_client_ip(request)
    logger.info(f"收到发送验证码请求: IP={ip_address}")
    
    # 检查速率限制（防止恶意触发）
    is_allowed, remaining_attempts, wait_seconds = check_reset_code_rate_limit(ip_address)
    if not is_allowed:
        # 格式化等待时间
        remaining_minutes = wait_seconds // 60
        remaining_seconds = wait_seconds % 60
        time_str = f"{remaining_minutes}分{remaining_seconds}秒" if remaining_minutes > 0 else f"{remaining_seconds}秒"
        
        raise ValidationException(
            detail=f"请求过于频繁，请在 {time_str} 后再试。3分钟内最多可请求5次。"
        )
    
    # 生成验证码
    code = generate_reset_code()
    expires_at = datetime.now() + timedelta(minutes=RESET_CODE_EXPIRE_MINUTES)
    
    # 保存验证码到内存
    reset_codes_cache[ip_address] = {
        "code": code,
        "expires_at": expires_at
    }
    logger.info(f"验证码已保存到内存: IP={ip_address}, Code={code}")
    
    # 发送通知
    try:
        success = await send_reset_notification(code, ip_address)
        
        if not success:
            logger.warning(f"没有可用的通知服务: IP={ip_address}")
            raise ValidationException(
                detail="没有配置通知服务，无法发送验证码。请先配置通知渠道。"
            )
    except ValidationException:
        raise
    except Exception as e:
        logger.error(f"发送通知失败: {e}", exc_info=True)
        raise ValidationException(detail="发送验证码失败，请稍后重试")
    
    logger.info(f"密码重置验证码已发送: IP={ip_address}, Code={code}")
    
    return BaseResponse.success(
        message="验证码已发送到通知渠道，请查收"
    )


@router.post("/password-reset/verify")
async def verify_reset_code(req: VerifyResetCodeRequest, request: Request):
    """
    验证重置验证码并更新密码
    
    Args:
        req: 验证码和新密码
        request: HTTP请求对象
    
    Returns:
        重置结果
    """
    ip_address = get_client_ip(request)
    
    if len(req.new_password) < 6:
        raise ValidationException(detail="密码至少6位")
    
    # 从内存中验证验证码
    cached_data = reset_codes_cache.get(ip_address)
    
    if not cached_data:
        raise ValidationException(detail="验证码无效或已过期")
    
    # 检查验证码是否匹配
    if cached_data["code"] != req.code:
        raise ValidationException(detail="验证码无效或已过期")
    
    # 检查验证码是否过期
    if cached_data["expires_at"] < datetime.now():
        # 清除过期的验证码
        del reset_codes_cache[ip_address]
        raise ValidationException(detail="验证码无效或已过期")
    
    # 验证码有效，更新密码
    try:
        with engine.begin() as conn:
            # 更新密码
            password_hash = security_manager.hash_password(req.new_password)
            stmt = (
                update(system_config_table)
                .where(system_config_table.c.id == 1)
                .values(admin_password_hash=password_hash)
            )
            conn.execute(stmt)
            
            # 清除该IP的登录失败记录
            delete_stmt = (
                delete(login_failed_records_table)
                .where(login_failed_records_table.c.ip_address == ip_address)
            )
            conn.execute(delete_stmt)
        
        # 清除已使用的验证码
        del reset_codes_cache[ip_address]
        
        logger.info(f"用户密码重置成功: IP={ip_address}")
        return BaseResponse.success(message="密码重置成功，请使用新密码登录")
        
    except ValidationException:
        raise
    except Exception as e:
        logger.error(f"密码重置失败: {e}", exc_info=True)
        raise ServerException(detail="密码重置失败，请稍后重试")


# ====== 健康检查端点（Railway 部署用）======
@router.get("/health")
def health_check():
    """简单健康检查，供 Railway 使用"""
    return {"status": "ok"}
