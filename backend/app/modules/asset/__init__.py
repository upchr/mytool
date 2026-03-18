# app/modules/asset/__init__.py
"""
固定资产管理模块

功能：
- 资产登记：登记购买的物品，记录价格、购买日期等信息
- 自动计算：自动计算使用天数、日均成本
- 资产管理：编辑、删除、报废资产
- 数据统计：按类别、年份统计，图表展示
- 质保管理：记录质保期，提醒即将过保资产
"""

from app.modules.asset import models, schemas, services, api

__all__ = ["models", "schemas", "services", "api"]