# app/modules/asset/models.py
from datetime import datetime

from sqlalchemy import Table, Column, Integer, String, Text, DateTime, Boolean, Float
from app.core.db.database import engine, metadata

# ========== 固定资产表 ==========
asset_table = Table(
    "asset",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),

    # 基本信息
    Column("name", String(200), nullable=False),  # 资产名称（如 iPhone 17）
    Column("category", String(50), nullable=False),  # 资产类别：electronics/home/office/vehicle/other
    Column("price", Float, nullable=False),  # 购买价格
    Column("purchase_date", DateTime, nullable=False),  # 购买日期
    Column("description", Text),  # 备注说明
    Column("image_url", String(500)),  # 资产图片URL

    # 状态信息
    Column("status", String(20), default="active"),  # 状态：active/scrapped
    Column("scrapped_date", DateTime),  # 报废日期

    # 质保信息
    Column("warranty_months", Integer),  # 质保期（月）
    Column("warranty_expire_date", DateTime),  # 质保到期日期

    # 时间戳
    Column("created_at", DateTime, default=datetime.now),
    Column("updated_at", DateTime, default=datetime.now, onupdate=datetime.now),

    sqlite_autoincrement=True,
)


__all__ = ["asset_table"]