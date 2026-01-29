from fastapi import APIRouter, HTTPException, Depends
from fastapi.params import Body
from sqlalchemy import select, update, insert, func
import json

from app.core.db.database import engine, metadata
from app.modules.notify.models import notification_services_table, notification_settings_table
from app.modules.notify.service import send_test_notification

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/services/{service_id}")
def get_service(service_id: int):
    stmt = select(notification_services_table).where(notification_services_table.c.id == service_id)
    with engine.connect() as conn:
        result = conn.execute(stmt).mappings().first()
        if not result:
            raise HTTPException(status_code=400, detail="渠道不存在")
        return dict(result) if result else None
@router.get("/services")
def get_notification_services():
    """获取所有通知服务配置"""
    with engine.connect() as conn:
        stmt = select(notification_services_table)
        services = conn.execute(stmt).mappings().all()

        # 获取默认服务ID
        settings_stmt = select(notification_settings_table).where(notification_settings_table.c.id == 1)
        settings = conn.execute(settings_stmt).mappings().first()

        return {
            "services": [
                {
                    **dict(service),
                    "config": json.loads(service["config"]) if service["config"] else {}
                }
                for service in services
            ],
            "default_service_id": settings["default_service_id"] if settings else None
        }

@router.put("/services/{service_id}")
def update_notification_service(service_id: int, service_data: dict):
    """更新通知服务配置"""
    # 验证 service_type
    # valid_types = ["wecom", "bark", "dingtalk", "email"]
    # if service_data.get("service_type") not in valid_types:
    #     raise HTTPException(status_code=400, detail="无效的服务类型")

    # 验证配置
    config = service_data.get("config", {})
    with engine.begin() as conn:
        # 检查服务是否存在
        check_stmt = select(notification_services_table).where(notification_services_table.c.id == service_id)
        if not conn.execute(check_stmt).first():
            raise HTTPException(status_code=404, detail="服务不存在")

        # 更新服务
        config_json = json.dumps(config) if config else None
        stmt = (
            update(notification_services_table)
            .where(notification_services_table.c.id == service_id)
            .values(
                service_name=service_data["service_name"],
                is_enabled=service_data["is_enabled"],
                config=config_json
            )
        )
        result = conn.execute(stmt)
        return {"message": "配置更新成功"}

@router.put("/services/status/{service_id}")
def update_notification_service(service_id: int,is_enabled: bool = Body(..., embed=True)):
    with engine.begin() as conn:
        # 检查服务是否存在
        check_stmt = select(notification_services_table).where(notification_services_table.c.id == service_id)
        if not conn.execute(check_stmt).first():
            raise HTTPException(status_code=404, detail="服务不存在")

        stmt = (
            update(notification_services_table)
            .where(notification_services_table.c.id == service_id)
            .values(
                is_enabled=is_enabled,
            )
        )
        result = conn.execute(stmt)
        return {"message": "配置状态成功"}

@router.put("/default-service")
def set_default_service(default_service_id: int):
    """设置默认通知服务"""
    with engine.begin() as conn:
        # 检查服务是否存在且已启用
        service_stmt = select(notification_services_table).where(
            notification_services_table.c.id == default_service_id,
            notification_services_table.c.is_enabled == True
        )
        service = conn.execute(service_stmt).mappings().first()

        if not service:
            raise HTTPException(status_code=400, detail="请选择一个已启用的服务作为默认")

        # 更新默认设置
        stmt = (
            update(notification_settings_table)
            .where(notification_settings_table.c.id == 1)
            .values(default_service_id=default_service_id)
        )
        conn.execute(stmt)
        return {"message": "默认服务设置成功"}

@router.post("/test/{service_id}")
async def test_notification_service(service_id: int):
    """测试通知服务"""
    with engine.connect() as conn:
        stmt = select(notification_services_table).where(
            notification_services_table.c.id == service_id
        )
        service = conn.execute(stmt).mappings().first()

        if not service:
            raise HTTPException(status_code=404, detail="服务不存在")

        if not service["is_enabled"]:
            raise HTTPException(status_code=400, detail="服务未启用")

        config = json.loads(service["config"]) if service["config"] else {}
        try:
            success = await send_test_notification(service["service_type"], config)
            if success:
                return {"message": "测试通知发送成功"}
            else:
                raise HTTPException(status_code=500, detail="测试通知发送失败")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"测试失败: {str(e)}")

@router.post("/init-default")
def init_default_services():
    """初始化默认通知服务（可选）"""
    default_services = [
        {"service_type": "wecom", "service_name": "企业微信", "is_enabled": False},
        {"service_type": "bark", "service_name": "Bark", "is_enabled": False},
        {"service_type": "dingtalk", "service_name": "钉钉", "is_enabled": False},
        {"service_type": "email", "service_name": "邮件", "is_enabled": False}
    ]

    with engine.begin() as conn:
        # 检查是否已初始化
        count = conn.execute(select(func.count()).select_from(notification_services_table)).scalar()
        if count > 0:
            raise HTTPException(status_code=400, detail="服务已初始化")

        # 插入默认服务
        for service in default_services:
            conn.execute(notification_services_table.insert().values(**service))

        # 初始化全局设置
        conn.execute(notification_settings_table.insert().values(id=1))

        return {"message": "默认服务初始化成功"}
