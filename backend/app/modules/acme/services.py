# app/modules/acme/service.py
import json
import logging
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import select, insert, update, delete, desc, Engine, func, and_
from pathlib import Path

from app.core.db.database import engine
from app.core.db.utils.query import QueryBuilder
from app.modules.acme import schemas
from app.modules.acme.ssl_repository import (
    DNSAuthRepository, ApplicationRepository,
    ExecutionRepository, CertificateRepository,
    DownloadLogRepository
)

logger = logging.getLogger(__name__)


class DNSAuthService:
    """DNS授权服务类"""

    def __init__(self, engine: Engine):
        self.repo = DNSAuthRepository(engine)

    def create(self, data: schemas.DNSAuthCreate) -> Dict[str, Any]:
        """创建DNS授权"""
        # TODO: 加密secret_id和secret_key
        create_data = data.model_dump()
        create_data.update({
            "total_applications": 0,
            "total_success": 0,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        })

        id = self.repo.create(create_data)
        return self.get_by_id(id)

    def update(self, id: int, data: schemas.DNSAuthUpdate) -> Optional[Dict[str, Any]]:
        """更新DNS授权"""
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return self.get_by_id(id)

        # TODO: 如果有secret字段，需要加密
        update_data["updated_at"] = datetime.now()

        success = self.repo.update(id, update_data)
        return self.get_by_id(id) if success else None

    def delete(self, id: int) -> bool:
        """删除DNS授权"""
        # 检查是否被使用
        app_repo = ApplicationRepository(self.repo.engine)
        applications = app_repo.get_by_dns_auth(id)
        if applications:
            raise ValueError(f"DNS授权正在被 {len(applications)} 个证书申请使用，无法删除")

        return self.repo.delete(id)

    def batch_delete(self, ids: List[int]) -> int:
        """批量删除"""
        # 检查是否被使用
        app_repo = ApplicationRepository(self.repo.engine)
        for id in ids:
            applications = app_repo.get_by_dns_auth(id)
            if applications:
                raise ValueError(f"DNS授权 ID:{id} 正在被使用，无法删除")

        return self.repo.delete_many(ids)

    def get_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取"""
        return self.repo.get_by_id(id)

    def get_list(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        """获取列表（带分页）"""
        query = QueryBuilder(self.repo.table)

        # 应用过滤条件
        for key, value in filters.items():
            if value is not None:
                if key == 'search' and value:
                    query.where_like('name', f'%{value}%')
                elif hasattr(self.repo.table.c, key):
                    query.where_eq(key, value)

        # 总数
        total_query = select(func.count()).select_from(query.table)
        if query._conditions:
            total_query = total_query.where(and_(*query._conditions))

        with self.repo.engine.connect() as conn:
            total = conn.execute(total_query).scalar() or 0

            # 分页
            query = query.order_by(desc('created_at')) \
                .limit(page_size) \
                .offset((page - 1) * page_size)

            items = query.execute(self.repo.engine)

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size,
            "items": [schemas.DNSAuthReadSensitive.from_orm(item).model_dump() for item in items]
        }

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.repo.get_stats()

    def update_stats(self, id: int, success: bool):
        """更新使用统计"""
        self.repo.update_stats(id, success)


class ApplicationService:
    """证书申请服务类"""

    def __init__(self, engine: Engine):
        self.repo = ApplicationRepository(engine)
        self.dns_auth_repo = DNSAuthRepository(engine)
        self.execution_repo = ExecutionRepository(engine)
        self.cert_repo = CertificateRepository(engine)

    def create(self, data: schemas.ApplicationCreate) -> Dict[str, Any]:
        """创建证书申请"""
        # 检查DNS授权是否存在且有效
        dns_auth = self.dns_auth_repo.get_by_id(data.dns_auth_id)
        if not dns_auth:
            raise ValueError(f"DNS授权 ID:{data.dns_auth_id} 不存在")
        if not dns_auth['is_active']:
            raise ValueError(f"DNS授权 {dns_auth['name']} 已禁用")

        create_data = data.model_dump()
        create_data['domains'] = json.dumps(data.domains, ensure_ascii=False)
        create_data.update({
            "status": "pending",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        })

        id = self.repo.create(create_data)
        return self.get_by_id(id)

    def update(self, id: int, data: schemas.ApplicationUpdate) -> Optional[Dict[str, Any]]:
        """更新证书申请"""
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return self.get_by_id(id)

        # 处理JSON字段
        if 'domains' in update_data:
            update_data['domains'] = json.dumps(data.domains, ensure_ascii=False)

        # 如果修改了dns_auth_id，检查新授权
        if 'dns_auth_id' in update_data:
            dns_auth = self.dns_auth_repo.get_by_id(update_data['dns_auth_id'])
            if not dns_auth or not dns_auth['is_active']:
                raise ValueError("DNS授权无效或已禁用")

        update_data["updated_at"] = datetime.now()

        success = self.repo.update(id, update_data)
        return self.get_by_id(id) if success else None

    def batch_delete(self, ids: List[int]):
        """批量删除申请"""
        # return self.repo.delete_many(ids)
        for id in ids:
            # 检查是否有证书
            certificates = self.cert_repo.get_by_application(id)
            if certificates:
                raise ValueError(f"ID:{id}申请下有 {len(certificates)} 个证书，无法删除")
        return self.batch_delete_with_executions(ids)

    def batch_delete_with_executions(self, ids: List[int]) -> int:
        """批量删除申请及其关联的执行历史（同一个事务中）"""
        from sqlalchemy import delete

        with self.repo.engine.begin() as conn:
            # 1. 先删除关联的执行历史
            if ids:
                delete_executions_stmt = delete(self.execution_repo.table).where(
                    self.execution_repo.table.c.application_id.in_(ids)
                )
                conn.execute(delete_executions_stmt)

            # 2. 再删除申请
            delete_apps_stmt = delete(self.repo.table).where(
                self.repo.table.c.id.in_(ids)
            )
            result = conn.execute(delete_apps_stmt)

            return result.rowcount

    def delete(self, id: int) -> bool:
        """删除申请"""
        # 检查是否有证书
        certificates = self.cert_repo.get_by_application(id)
        if certificates:
            raise ValueError(f"申请下有 {len(certificates)} 个证书，无法删除")

        # 删除执行历史
        executions = self.execution_repo.get_by_application(id)
        for exec_ in executions:
            self.execution_repo.delete(exec_['id'])

        return self.repo.delete(id)

    def get_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取"""
        data = self.repo.get_by_id(id)
        if data and 'domains' in data:
            data['domains'] = json.loads(data['domains'])
        return data

    def get_list(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        """获取列表（带分页）"""
        # 构建查询
        query = QueryBuilder(self.repo.table)

        # 应用过滤条件
        for key, value in filters.items():
            if value is not None and hasattr(self.repo.table.c, key):
                if key =='domains':
                    query.where_like(key, f'%{value}%')
                    continue
                query.where_eq(key, value)

        # 总数
        total_query = select(func.count()).select_from(query.table)
        if query._conditions:
            total_query = total_query.where(and_(*query._conditions))

        with self.repo.engine.connect() as conn:
            total = conn.execute(total_query).scalar() or 0

            # 分页
            query = query.order_by(desc('created_at')) \
                .limit(page_size) \
                .offset((page - 1) * page_size)

            items = query.execute(self.repo.engine)

        # 处理JSON字段
        result_items = []
        for item in items:
            if 'domains' in item:
                item['domains'] = json.loads(item['domains'])
            result_items.append(item)

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size,
            "items": result_items
        }

    # def check_recent_processing(self,application_id: int) -> bool:
    #     """
    #     检查10分钟内是否有正在处理的申请
    #
    #     Returns:
    #         True: 有正在处理的申请（需要阻止）
    #         False: 没有正在处理的申请（可以继续）
    #     """
    #     # 获取最新的执行记录
    #     latest_exec = self.execution_repo.get_latest_by_application(application_id)
    #
    #     if not latest_exec:
    #         # 没有执行记录，可以执行
    #         return False
    #
    #     # 检查状态是否为 processing
    #     if latest_exec['status'] != 'processing':
    #         # 不是 processing 状态，可以执行
    #         return False
    #
    #     # 计算时间差
    #     time_diff = datetime.now() - latest_exec['created_at']
    #
    #     # 如果 processing 状态的记录在10分钟内
    #     if time_diff.total_seconds() < 600:  # 600秒 = 10分钟
    #         logger.info(f"⏳ 上一个申请正在执行中（{int(time_diff.total_seconds())}秒前），请稍后再试")
    #         return True
    #     else:
    #         # 超过10分钟，可能是卡住了，允许重新执行
    #         logger.info(f"⚠️ 上一个申请状态为 processing 但已超过10分钟（{int(time_diff.total_seconds())}秒前），允许重新执行")
    #         return False
    def check_and_clean_stuck_processing(self, application_id: int, stuck_minutes: int = 10) -> bool:
        """
        检查并清理卡住的 processing 状态

        Returns:
            True: 可以执行新任务
            False: 还有活跃任务，不能执行
        """
        latest_exec = self.execution_repo.get_latest_by_application(application_id)

        if not latest_exec:
            return True

        # 如果不是 processing 状态，可以直接执行
        if latest_exec['status'] != 'processing':
            return True

        # 计算时间差
        time_diff = datetime.now() - latest_exec['created_at']
        minutes_passed = time_diff.total_seconds() / 60

        if minutes_passed < stuck_minutes:
            # 10分钟内，还在正常执行中
            logger.info(f"⏳ 上一个申请正在执行中（{minutes_passed:.1f}分钟前），请稍后再试")
            return False
        else:
            # 超过10分钟，可能是卡住了，自动标记为失败并允许重新执行
            logger.warning(f"⚠️ 检测到卡住的 processing 任务（{minutes_passed:.1f}分钟前），自动标记为失败")

            # 更新卡住的任务为失败
            self.execution_repo.fail_execution(
                latest_exec['id'],
                "任务执行超时（超过10分钟）"
            )

            # 更新申请状态
            self.repo.update_status(application_id, "failed")

            return True

    def execute(self, application_id: int, triggered_by: str = "manual") -> Dict[str, Any]:
        """执行证书申请
        
        Args:
            application_id: 申请ID
            triggered_by: 触发方式（manual/schedule/workflow）
        
        Returns:
            工作流调用时返回执行结果，否则返回执行ID
        """
        # 检查10分钟内是否有正在处理的申请
        if not self.check_and_clean_stuck_processing(application_id):
            raise ValueError("上一个申请正在执行中，请稍后再试（10分钟内只能执行一次）")

        application = self.get_by_id(application_id)
        if not application:
            raise ValueError(f"申请 ID:{application_id} 不存在")

        # 检查DNS授权
        dns_auth = self.dns_auth_repo.get_by_id(application['dns_auth_id'])
        if not dns_auth or not dns_auth['is_active']:
            raise ValueError("关联的DNS授权无效或已禁用")

        # 工作流调用时，同步执行；否则后台执行
        if triggered_by == "workflow":
            # 同步执行模式：直接执行并等待完成
            return self._execute_sync(application_id, application, dns_auth, triggered_by)
        else:
            # 后台执行模式：在后台线程中执行
            return self._execute_async(application_id, application, dns_auth, triggered_by)

    def _execute_sync(self, application_id: int, application: dict, dns_auth: dict, triggered_by: str) -> Dict[str, Any]:
        """同步执行证书申请（用于工作流）"""
        # 创建执行记录
        execution_id = self.execution_repo.start_execution(application_id, triggered_by)
        
        cert_data = None
        error_msg = None
        cert = None
        key = None
        
        try:
            logger.info(f"开始申请证书: {application['domains']}")
            try:
                from app.modules.acme.client import issue_certificate
                cert, key = issue_certificate(
                    domains=application['domains'],
                    email=application['email'],
                    secret_id=dns_auth['secret_id'],
                    secret_key=dns_auth['secret_key'],
                    dns_provider=dns_auth['provider']
                )
                logger.info(f"申请证书成功: {cert}, {key}")
                success = True
            except Exception as e:
                success = False
                error_msg = str(e)
                logger.error(f"申请证书失败: {error_msg}")

            dns_auth_repo = DNSAuthRepository(self.repo.engine)
            if success:
                # 创建证书记录
                cert_data = {
                    "cert_path": cert,
                    "key_path": key,
                    "application_id": application_id,
                    "execution_id": execution_id,
                    "domains": json.dumps(application['domains']),
                    "algorithm": application['algorithm'],
                    "issuer": "Let's Encrypt",
                    "not_before": datetime.now(),
                    "not_after": datetime.now() + timedelta(days=90),
                    "is_active": True
                }
                cert_id = self.cert_repo.create(cert_data)

                # 完成执行
                self.execution_repo.complete_execution(
                    execution_id,
                    success=True,
                    cert_id=cert_id,
                    log="证书申请成功"
                )

                # 更新申请状态
                self.repo.update_status(application_id, "completed")

                # 更新DNS授权统计
                dns_auth_repo.update_stats(application['dns_auth_id'], True)

                # 停用旧证书
                self.cert_repo.deactivate_old_certificates(application_id, cert_id)

                # 上传证书到节点
                try:
                    from app.modules.node.services import get_node
                    node_dict = get_node(engine, application['node_id'])
                    from app.modules.node.schemas import NodeRead
                    from app.core.sh.ssh_client import SSHClient
                    ssh = SSHClient(NodeRead(**node_dict))
                    ssh.connect()
                    ssh.upload_file(cert, application['crt_path'])
                    ssh.upload_file(key, application['key_path'])
                    logger.info(f"证书上传成功: {application['crt_path']}")
                    ssh.close()
                except Exception as e:
                    logger.error(f"证书上传失败: {str(e)}")

                # 更新下次续期时间
                self.repo.update_next_renew(application_id, cert_data['not_after'])

            else:
                self.execution_repo.fail_execution(execution_id, f"申请证书失败: {error_msg}")
                self.repo.update_status(application_id, "failed")
                dns_auth_repo.update_stats(application['dns_auth_id'], False)

            # 发送通知
            self._send_notification(
                application=application,
                success=success,
                cert_data=cert_data,
                error_msg=error_msg
            )

            # 返回执行结果
            return {
                "status": "success" if success else "failed",
                "output": "证书申请成功" if success else "证书申请失败",
                "error": error_msg if not success else ""
            }

        except Exception as e:
            logger.error(f"证书申请失败: {str(e)}")
            self.execution_repo.fail_execution(execution_id, str(e))
            self.repo.update_status(application_id, "failed")
            return {
                "status": "failed",
                "output": "",
                "error": str(e)
            }

    def _execute_async(self, application_id: int, application: dict, dns_auth: dict, triggered_by: str) -> Dict[str, Any]:
        """异步执行证书申请（用于手动执行和调度）"""
        # 创建执行记录
        execution_id = self.execution_repo.start_execution(application_id, triggered_by)

        def run_task():
            cert_data = None
            error_msg = None
            cert = None
            key = None
            try:
                logger.info(f"开始申请证书: {application['domains']}")
                try:
                    from app.modules.acme.client import issue_certificate
                    cert, key = issue_certificate(
                        domains=application['domains'],
                        email=application['email'],
                        secret_id=dns_auth['secret_id'],
                        secret_key=dns_auth['secret_key'],
                        dns_provider=dns_auth['provider']
                    )
                    logger.info(f"申请证书成功: {cert}, {key}")
                    success = True
                except Exception as e:
                    success = False
                    error_msg = str(e)
                    logger.error(f"申请证书失败: {error_msg}")

                dns_auth_repo = DNSAuthRepository(self.repo.engine)
                if success:
                    # 创建证书记录
                    cert_data = {
                        "cert_path": cert,
                        "key_path": key,
                        "application_id": application_id,
                        "execution_id": execution_id,
                        "domains": json.dumps(application['domains']),
                        "algorithm": application['algorithm'],
                        "issuer": "Let's Encrypt",
                        "not_before": datetime.now(),
                        "not_after": datetime.now() + timedelta(days=90),
                        "is_active": True
                    }
                    cert_id = self.cert_repo.create(cert_data)

                    # 完成执行
                    self.execution_repo.complete_execution(
                        execution_id,
                        success=True,
                        cert_id=cert_id,
                        log="证书申请成功"
                    )

                    # 更新申请状态
                    self.repo.update_status(application_id, "completed")

                    # 更新DNS授权统计
                    dns_auth_repo.update_stats(application['dns_auth_id'], True)

                    # 停用旧证书
                    self.cert_repo.deactivate_old_certificates(application_id, cert_id)

                    def upload_task():
                        try:
                            from app.modules.node.services import get_node
                            node_dict = get_node(engine, application['node_id'])
                            from app.modules.node.schemas import NodeRead
                            from app.core.sh.ssh_client import SSHClient
                            ssh = SSHClient(NodeRead(**node_dict))
                            ssh.connect()
                            ssh.upload_file(cert, application['crt_path'])
                            ssh.upload_file(key, application['key_path'])
                            logger.info(f"证书上传成功: {application['crt_path']}")
                        except Exception as e:
                            logger.error(f"证书上传失败: {str(e)}")
                            # 上传失败不影响主流程，只记录日志
                    threading.Thread(target=upload_task, daemon=True).start()

                    # 更新下次续期时间
                    self.repo.update_next_renew(application_id, cert_data['not_after'])

                else:
                    self.execution_repo.fail_execution(execution_id, f"申请证书失败: {error_msg}")
                    self.repo.update_status(application_id, "failed")
                    dns_auth_repo.update_stats(application['dns_auth_id'], False)

                # 发送通知
                self._send_notification(
                    application=application,
                    success=success,
                    cert_data=cert_data,
                    error_msg=error_msg
                )

            except Exception as e:
                logger.error(f"证书申请失败: {str(e)}")
                self.execution_repo.fail_execution(execution_id, str(e))
                self.repo.update_status(application_id, "failed")
                raise
        
        threading.Thread(target=run_task, daemon=True).start()

        return {
            "execution_id": execution_id,
            "success": 'back'
        }

    def _send_notification(self, application: dict, success: bool,
                           cert_data: dict = None, error_msg: str = None):
        """
        发送证书续期通知

        Args:
            application: 申请信息
            success: 是否成功
            cert_data: 证书数据（成功时）
            error_msg: 错误信息（失败时）
        """
        # 检查是否需要发送通知
        if not application.get('auto_notice'):
            logger.debug(f"申请 {application.get('id')} 未开启通知，跳过")
            return

        # 确定通知时机
        when_notice = application.get('when_notice')

        # 构建通知内容
        content = None
        domains = application.get('domains', [])
        domains_str = ', '.join(domains) if isinstance(domains, list) else str(domains)

        if success and when_notice == 'completed' and cert_data:
            # 成功通知
            next_renew = cert_data.get('not_after')
            if next_renew:
                next_renew_str = next_renew.strftime('%Y-%m-%d %H:%M:%S')
            else:
                next_renew_str = "未知"

            content = (
                f"✅ 证书申请/续签成功\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"📌 申请ID：{application.get('id')}\n"
                f"🌐 域名：{domains_str}\n"
                f"📅 下次续签：{next_renew_str}\n"
                f"━━━━━━━━━━━━━━━━"
            )
            logger.info(f"准备发送成功通知: 申请ID={application.get('id')}")

        elif not success and when_notice == 'failed':
            # 失败通知
            content = (
                f"❌ 证书申请/续签失败\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"📌 申请ID：{application.get('id')}\n"
                f"🌐 域名：{domains_str}\n"
                f"💥 错误：{error_msg}\n"
                f"━━━━━━━━━━━━━━━━"
            )
            logger.info(f"准备发送失败通知: 申请ID={application.get('id')}")

        # 发送通知
        if content:
            try:
                # 异步发送通知
                from app.modules.notify.handler.manager import notification_manager
                import asyncio
                asyncio.run(notification_manager.send_broadcast(content=content))
                logger.info(f"✅ 通知发送成功: 申请ID={application.get('id')}")
            except Exception as e:
                logger.error(f"❌ 通知发送失败: {e}")
        else:
            logger.debug(f"无需发送通知: 成功={success}, 时机={when_notice}")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.repo.get_stats()


class CertificateService:
    """证书服务类"""

    def __init__(self, engine: Engine):
        self.repo = CertificateRepository(engine)
        self.download_repo = DownloadLogRepository(engine)

    def get_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取"""
        data = self.repo.get_by_id(id)
        if data and 'domains' in data:
            data['domains'] = json.loads(data['domains'])
        if data and Path(data['cert_path']).exists():
            with open(data['cert_path'], "r") as f:
                data['cert'] = f.read().strip()
        if data and Path(data['key_path']).exists():
            with open(data['key_path'], "r") as f:
                data['key'] = f.read().strip()

        return data

    def delete(self, id: int) -> bool:
        return self.repo.delete(id)>0

    def get_list(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        """获取列表（带分页）"""
        query = QueryBuilder(self.repo.table)

        for key, value in filters.items():
            if value is not None:
                if key == 'search' and value:
                    query.where_like('domains', f'%{value}%')
                elif hasattr(self.repo.table.c, key):
                    query.where_eq(key, value)

        total_query = select(func.count()).select_from(query.table)
        if query._conditions:
            total_query = total_query.where(and_(*query._conditions))

        with self.repo.engine.connect() as conn:
            total = conn.execute(total_query).scalar() or 0

            query = query.order_by(desc('created_at')) \
                .limit(page_size) \
                .offset((page - 1) * page_size)

            items = query.execute(self.repo.engine)

        result_items = []
        for item in items:
            if 'domains' in item:
                item['domains'] = json.loads(item['domains'])
            result_items.append(item)

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size,
            "items": result_items
        }

    def download(self, id: int, downloaded_by: str = None) -> Dict[str, Any]:
        """下载证书"""
        cert = self.get_by_id(id)
        if not cert:
            raise ValueError(f"证书 ID:{id} 不存在")

        # 记录下载日志
        self.download_repo.create({
            "cert_id": id,
            "downloaded_by": downloaded_by or "unknown"
        })

        # TODO: 读取证书文件内容
        return {
            "cert": cert,
            "content": {
                "cert": "证书内容...",
                "key": "私钥内容...",
                "fullchain": "完整链内容..."
            }
        }

    def download_as_zip(self, id: int, downloaded_by: str = None) -> Dict[str, Any]:
        """将证书文件打包成zip下载"""
        cert = self.get_by_id(id)
        if not cert:
            raise ValueError(f"证书 ID:{id} 不存在")

        # 记录下载日志
        self.download_repo.create({
            "cert_id": id,
            "downloaded_by": downloaded_by or "unknown"
        })
        import io
        # 创建内存中的zip文件
        zip_buffer = io.BytesIO()
        import base64

        import zipfile

        # 匹配域名和日期时间
        pattern = r'^(.+?)_(\d{8}_\d{6})\.'
        import re
        match = re.match(pattern, Path(cert['cert_path']).name)

        zip_base64=None
        filename=None
        if match:
            domain = match.group(1)
            datetime_str = match.group(2)

            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # 添加证书文件
                if cert.get('cert_path') and Path(cert['cert_path']).exists():
                    cert_content = Path(cert['cert_path']).read_text(encoding='utf-8')
                    zip_file.writestr(f"{domain}.crt", cert_content)

                # 添加私钥文件
                if cert.get('key_path') and Path(cert['key_path']).exists():
                    key_content = Path(cert['key_path']).read_text(encoding='utf-8')
                    zip_file.writestr(f"{domain}.key", key_content)

                # 添加完整链文件（如果有）
                if cert.get('fullchain_path') and Path(cert['fullchain_path']).exists():
                    fullchain_content = Path(cert['fullchain_path']).read_text(encoding='utf-8')
                    zip_file.writestr(f"{domain}_fullchain.crt", fullchain_content)

                # 添加说明文件
                readme_content = self._generate_readme(cert,domain)
                zip_file.writestr("README.txt", readme_content)

            # 获取zip文件的二进制内容
            zip_buffer.seek(0)
            zip_content = zip_buffer.getvalue()

            # 转换为base64
            zip_base64 = base64.b64encode(zip_content).decode('utf-8')

            # 生成文件名
            filename = f"{domain}_{datetime_str}.zip"

        return {
            "content": zip_base64,
            "filename": filename,
            "encoding": "base64",
            "mime_type": "application/zip"
        }

    def _generate_readme(self, cert: Dict,domain:str) -> str:
        """生成说明文件"""
        domains = ', '.join(cert.get('domains', []))
        not_after = cert.get('not_after')
        if not_after:
            expiry = not_after.strftime('%Y-%m-%d %H:%M:%S')
        else:
            expiry = '未知'

        readme = f"""证书信息
================================
域名: {domains}
颁发者: {cert.get('issuer', "Let's Encrypt")}
算法: {cert.get('algorithm', 'RSA')}
创建时间: {cert.get('created_at', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')}
过期时间: {expiry}

文件说明:
- *.crt: 证书文件
- *.key: 私钥文件
- *_fullchain.crt: 完整证书链

使用示例 (Nginx):
ssl_certificate     /your_path/{domain}.crt;
ssl_certificate_key /your_path/{domain}.key;

================================
下载时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
By ToolsPlus.ChrPlus（开源：https://github.com/upchr/mytool）
"""
        return readme

    def get_download_count(self, id: int) -> int:
        """获取下载次数"""
        return self.download_repo.get_download_count(id)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.repo.get_stats()


class ExecutionService:
    """执行历史服务类"""

    def __init__(self, engine: Engine):
        self.repo = ExecutionRepository(engine)

    def get_by_application(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        """根据申请ID获取执行历史"""
        """获取列表（带分页）"""
        query = QueryBuilder(self.repo.table)

        # 应用过滤条件
        for key, value in filters.items():
            if value is not None:
                if key == 'search' and value:
                    query.where_like('name', f'%{value}%')
                elif hasattr(self.repo.table.c, key):
                    query.where_eq(key, value)

        # 总数
        total_query = select(func.count()).select_from(query.table)
        if query._conditions:
            total_query = total_query.where(and_(*query._conditions))

        with self.repo.engine.connect() as conn:
            total = conn.execute(total_query).scalar() or 0

            # 分页
            query = query.order_by(desc('created_at')) \
                .limit(page_size) \
                .offset((page - 1) * page_size)

            items = query.execute(self.repo.engine)

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size,
            "items": [schemas.ExecutionRead.model_validate(item).model_dump() for item in items]
        }


        return self.repo.get_by_application(application_id)

    def get_latest_by_application(self, application_id: int) -> Optional[Dict[str, Any]]:
        """获取申请的最新执行记录"""
        return self.repo.get_latest_by_application(application_id)
