# app/modules/notify/manager.py
# 导入 asyncio
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import select, update, func

from app.core.db.database import engine, metadata
from . import NotificationStrategyFactory
from ..models import notification_services_table

logger = logging.getLogger(__name__)

class NotificationManager:
    """通知管理器（基于现有框架）"""

    def __init__(self):
        self.strategy_cache = {}
        # 确保表存在
        metadata.create_all(bind=engine)

    def _get_strategy_instance(self, service_type: str, config: Dict) -> Any:
        """获取策略实例（带缓存）"""
        cache_key = f"{service_type}:{json.dumps(config, sort_keys=True)}"
        if cache_key not in self.strategy_cache:
            try:
                strategy = NotificationStrategyFactory.get_strategy(service_type, config)
                self.strategy_cache[cache_key] = strategy
                logger.debug(f"创建策略实例: {service_type}")
            except Exception as e:
                logger.error(f"创建策略实例失败 {service_type}: {e}")
                raise
        return self.strategy_cache[cache_key]

    async def send_notification(self,
                                title: str = "ToolsPlus",
                                content: str = '',
                                service_id: Optional[int] = None,
                                service_name: Optional[str] = None,
                                **kwargs) -> List[Dict[str, Any]]:
        """
        发送通知

        Args:
            title: 通知标题
            content: 通知内容
            service_id: 服务ID
            service_name: 服务名称
            **kwargs: 额外参数

        Returns:
            发送结果列表
        """
        # 获取服务配置
        service = self.get_service(service_id, service_name)
        if not service:
            raise ValueError("指定的通知服务不存在或未启用")

        return [await self._send_via_service(service, title, content, **kwargs)]

    async def send_broadcast(self,
                             title: str = "ToolsPlus",
                             content: str = '',
                             service_types: Optional[List[str]] = None,
                             **kwargs) -> List[Dict[str, Any]]:
        """
        广播通知到多个服务

        Args:
            title: 通知标题
            content: 通知内容
            service_types: 指定服务类型列表，为None时发送到所有启用的服务
            **kwargs: 额外参数

        Returns:
            发送结果列表
        """
        # 获取所有启用的服务
        services = self.get_all_services(enabled_only=True)

        # 过滤服务类型
        if service_types:
            services = [s for s in services if s['service_type'] in service_types]

        # 并发发送通知
        tasks = []
        for service in services:
            task = self._send_via_service(service, title, content, **kwargs)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"发送通知到服务 {services[i]['service_name']} 失败: {result}")
                final_results.append({
                    'service_id': services[i]['id'],
                    'service_name': services[i]['service_name'],
                    'service_type': services[i]['service_type'],
                    'success': False,
                    'message': str(result),
                    'raw_result': None
                })
            else:
                final_results.append(result)

        return final_results

    async def _send_via_service(self,
                                service: Dict,
                                title: str,
                                content: str,
                                **kwargs) -> Dict[str, Any]:
        """通过指定服务发送通知"""
        try:
            # 获取策略实例
            strategy = self._get_strategy_instance(service['service_type'], service['config'])

            # 发送通知
            result = await strategy.send(title, content, **kwargs)

            # 记录日志
            if result.get('success'):
                logger.info(f"通知发送成功: {service['service_name']} - {title}")
            else:
                logger.warning(f"通知发送失败: {service['service_name']} - {title}: {result.get('message')}")

            return {
                'service_id': service['id'],
                'service_name': service['service_name'],
                'service_type': service['service_type'],
                'success': result.get('success', False),
                'message': result.get('message', ''),
                'raw_result': result
            }

        except Exception as e:
            logger.error(f"通知发送异常: {service['service_name']} - {title}: {e}")
            return {
                'service_id': service['id'],
                'service_name': service['service_name'],
                'service_type': service['service_type'],
                'success': False,
                'message': str(e),
                'raw_result': None
            }

    def get_service(self, service_id: Optional[int] = None,
                    service_name: Optional[str] = None) -> Optional[Dict]:
        """
        获取服务配置

        Args:
            service_id: 服务ID
            service_name: 服务名称

        Returns:
            服务配置字典，如果不存在或未启用则返回None
        """

        with engine.begin() as conn:
            try:
                query = select(notification_services_table)

                if service_id:
                    query = query.where(notification_services_table.c.id == service_id)
                elif service_name:
                    query = query.where(notification_services_table.c.service_name == service_name)
                else:
                    return None

                result = conn.execute(query).fetchone()

                if result and result.is_enabled:
                    return {
                        'id': result.id,
                        'service_type': result.service_type,
                        'service_name': result.service_name,
                        'is_enabled': result.is_enabled,
                        'config': json.loads(result.config) if result.config else {},
                        'created_at': result.created_at,
                        'updated_at': result.updated_at
                    }
                return None

            except Exception as e:
                logger.error(f"获取服务配置失败: {e}")
                return None

    def get_all_services(self, enabled_only: bool = True) -> List[Dict]:
        """
        获取所有服务配置

        Args:
            enabled_only: 是否只获取启用的服务

        Returns:
            服务配置列表
        """

        with engine.begin() as conn:
            try:
                query = select(notification_services_table)

                if enabled_only:
                    query = query.where(notification_services_table.c.is_enabled == True)

                query = query.order_by(notification_services_table.c.id)
                results = conn.execute(query).fetchall()

                services = []
                for result in results:
                    services.append({
                        'id': result.id,
                        'service_type': result.service_type,
                        'service_name': result.service_name,
                        'is_enabled': result.is_enabled,
                        'config': json.loads(result.config) if result.config else {},
                        'created_at': result.created_at,
                        'updated_at': result.updated_at
                    })

                return services

            except Exception as e:
                logger.error(f"获取所有服务配置失败: {e}")
                return []

    def add_service(self, service_type: str, service_name: str, config: Dict,
                    is_enabled: bool = False) -> Optional[int]:
        """
        添加通知服务

        Args:
            service_type: 服务类型 (wecom, bark, dingtalk, email等)
            service_name: 服务名称
            config: 服务配置（字典）
            is_enabled: 是否启用

        Returns:
            创建的服务ID，失败返回None
        """

        with engine.begin() as conn:
            try:
                # 检查名称是否重复
                check_query = select(notification_services_table).where(
                    notification_services_table.c.service_name == service_name
                )
                existing = conn.execute(check_query).fetchone()
                if existing:
                    logger.warning(f"服务名称已存在: {service_name}")
                    return None

                # 插入新服务
                insert_stmt = notification_services_table.insert().values(
                    service_type=service_type,
                    service_name=service_name,
                    is_enabled=is_enabled,
                    config=json.dumps(config)
                )

                result = conn.execute(insert_stmt)

                logger.info(f"添加通知服务成功: {service_name} (ID: {result.lastrowid})")
                return result.lastrowid

            except Exception as e:
                logger.error(f"添加通知服务失败: {e}")
                return None

    def update_service(self, service_id: int, **kwargs) -> bool:
        """
        更新服务配置

        Args:
            service_id: 服务ID
            **kwargs: 更新字段，支持：service_name, is_enabled, config

        Returns:
            是否更新成功
        """

        allowed_fields = ['service_name', 'is_enabled', 'config']
        updates = {}

        for key, value in kwargs.items():
            if key in allowed_fields:
                if key == 'config' and isinstance(value, dict):
                    updates[key] = json.dumps(value)
                else:
                    updates[key] = value

        if not updates:
            return False

        with engine.begin() as conn:
            try:
                update_stmt = update(notification_services_table).where(
                    notification_services_table.c.id == service_id
                ).values(**updates)

                result = conn.execute(update_stmt)

                success = result.rowcount > 0
                if success:
                    logger.info(f"更新服务配置成功: ID={service_id}")
                else:
                    logger.warning(f"更新服务配置失败: 服务不存在 ID={service_id}")

                return success

            except Exception as e:
                logger.error(f"更新服务配置失败: {e}")
                return False

    def delete_service(self, service_id: int) -> bool:
        """
        删除服务

        Args:
            service_id: 服务ID

        Returns:
            是否删除成功
        """

        with engine.begin() as conn:
            try:
                delete_stmt = notification_services_table.delete().where(
                    notification_services_table.c.id == service_id
                )

                result = conn.execute(delete_stmt)

                success = result.rowcount > 0
                if success:
                    logger.info(f"删除服务成功: ID={service_id}")
                else:
                    logger.warning(f"删除服务失败: 服务不存在 ID={service_id}")

                return success

            except Exception as e:
                logger.error(f"删除服务失败: {e}")
                return False

    def test_service(self, service_id: int) -> Dict[str, Any]:
        """
        测试服务连通性

        Args:
            service_id: 服务ID

        Returns:
            测试结果
        """
        service = self.get_service(service_id=service_id)
        if not service:
            return {
                'success': False,
                'message': '服务不存在',
                'service': None
            }

        try:
            strategy = self._get_strategy_instance(service['service_type'], service['config'])
            success = strategy.test_connection()
            return {
                'success': success,
                'message': '测试成功' if success else '测试失败',
                'service': {
                    'id': service['id'],
                    'name': service['service_name'],
                    'type': service['service_type']
                }
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
                'service': {
                    'id': service['id'],
                    'name': service['service_name'],
                    'type': service['service_type']
                }
            }

    def list_available_strategies(self) -> Dict[str, str]:
        """
        列出所有可用策略

        Returns:
            策略名称到类名的映射
        """
        strategies = NotificationStrategyFactory.get_available_strategies()
        return {
            name: strategy_class.__name__
            for name, strategy_class in strategies.items()
        }

    def get_strategy_info(self, strategy_type: str) -> Optional[Dict[str, Any]]:
        """
        获取策略信息

        Args:
            strategy_type: 策略类型

        Returns:
            策略信息字典
        """
        strategies = NotificationStrategyFactory.get_available_strategies()
        strategy_class = strategies.get(strategy_type)

        if not strategy_class:
            return None

        return {
            'name': strategy_type,
            'class_name': strategy_class.__name__,
            'description': strategy_class.__doc__ or '',
            'required_config': self._get_required_config_fields(strategy_class)
        }

    def _get_required_config_fields(self, strategy_class) -> List[str]:
        """获取策略需要的配置字段"""
        try:
            # 创建临时实例以获取验证信息
            temp_config = {'test': 'test'}
            strategy = strategy_class(temp_config)

            # 尝试调用验证方法（可能会抛出异常显示缺少的字段）
            try:
                strategy._validate_config()
            except ValueError as e:
                # 从错误信息中提取字段名
                error_msg = str(e)
                if '缺少必要字段' in error_msg:
                    # 解析错误信息，提取字段名
                    import re
                    fields = re.findall(r'缺少必要字段: (\w+)', error_msg)
                    if fields:
                        return fields

            return []

        except Exception:
            return []

    def get_service_statistics(self) -> Dict[str, Any]:
        """
        获取服务统计信息

        Returns:
            统计信息字典
        """

        with engine.begin() as conn:
            try:
                # 统计总数
                total_query = select(func.count()).select_from(notification_services_table)
                total = conn.execute(total_query).scalar()

                # 统计启用数量
                enabled_query = select(func.count()).select_from(notification_services_table).where(
                    notification_services_table.c.is_enabled == True
                )
                enabled = conn.execute(enabled_query).scalar()

                # 按类型统计
                type_query = select(
                    notification_services_table.c.service_type,
                    func.count()
                ).group_by(notification_services_table.c.service_type)

                type_stats = {}
                for row in conn.execute(type_query):
                    type_stats[row[0]] = row[1]

                return {
                    'total': total or 0,
                    'enabled': enabled or 0,
                    'disabled': (total or 0) - (enabled or 0),
                    'by_type': type_stats
                }

            except Exception as e:
                logger.error(f"获取服务统计信息失败: {e}")
                return {
                    'total': 0,
                    'enabled': 0,
                    'disabled': 0,
                    'by_type': {}
                }

    def get_service_by_type(self, service_type: str, enabled_only: bool = True) -> List[Dict]:
        """
        根据类型获取服务

        Args:
            service_type: 服务类型
            enabled_only: 是否只获取启用的服务

        Returns:
            服务列表
        """

        with engine.begin() as conn:
            try:
                query = select(notification_services_table).where(
                    notification_services_table.c.service_type == service_type
                )

                if enabled_only:
                    query = query.where(notification_services_table.c.is_enabled == True)

                query = query.order_by(notification_services_table.c.id)
                results = conn.execute(query).fetchall()

                services = []
                for result in results:
                    services.append({
                        'id': result.id,
                        'service_type': result.service_type,
                        'service_name': result.service_name,
                        'is_enabled': result.is_enabled,
                        'config': json.loads(result.config) if result.config else {},
                        'created_at': result.created_at,
                        'updated_at': result.updated_at
                    })

                return services

            except Exception as e:
                logger.error(f"根据类型获取服务失败: {e}")
                return []

    def enable_service(self, service_id: int) -> bool:
        """启用服务"""
        return self.update_service(service_id, is_enabled=True)

    def disable_service(self, service_id: int) -> bool:
        """禁用服务"""
        return self.update_service(service_id, is_enabled=False)

    def update_service_config(self, service_id: int, config: Dict) -> bool:
        """更新服务配置"""
        return self.update_service(service_id, config=config)

# 全局实例
notification_manager = NotificationManager()

# 快捷函数
async def send_notification(title: str, content: str, service_name: str, **kwargs):
    """发送通知的快捷函数"""
    return await notification_manager.send_notification(
        title=title,
        content=content,
        service_name=service_name,
        **kwargs
    )

async def broadcast_notification(title: str, content: str, service_types: List[str] = None, **kwargs):
    """广播通知的快捷函数"""
    return await notification_manager.send_broadcast(
        title=title,
        content=content,
        service_types=service_types,
        **kwargs
    )

def get_enabled_services():
    """获取所有启用的服务"""
    return notification_manager.get_all_services(enabled_only=True)

def add_notification_service(service_type: str, service_name: str, config: Dict, is_enabled: bool = False):
    """添加通知服务的快捷函数"""
    return notification_manager.add_service(service_type, service_name, config, is_enabled)


