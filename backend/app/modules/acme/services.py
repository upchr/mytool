# app/modules/acme/service.py
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import select, insert, update, delete, desc, Engine, func, and_
from pathlib import Path

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

    def execute(self, application_id: int, triggered_by: str = "manual") -> Dict[str, Any]:
        """手动执行证书申请"""
        global cert, key
        application = self.get_by_id(application_id)
        if not application:
            raise ValueError(f"申请 ID:{application_id} 不存在")

        # 检查DNS授权
        dns_auth = self.dns_auth_repo.get_by_id(application['dns_auth_id'])
        if not dns_auth or not dns_auth['is_active']:
            raise ValueError("关联的DNS授权无效或已禁用")

        # 创建执行记录
        execution_id = self.execution_repo.start_execution(application_id, triggered_by)

        try:
            # TODO: 实际调用acme.sh或certbot申请证书
            # 这里模拟申请过程
            logger.info(f"开始申请证书: {application['domains']}")
            try:
                from app.modules.acme.core import ACMEService
                acme = ACMEService(
                    email="1017719268@qq.com",
                    staging=True  # 生产环境
                )
                # 申请证书
                cert, key = acme.issue_certificate(
                    domains=application['domains'],
                    dns_provider=dns_auth['provider'],
                    wait_time=30
                )
                logger.info(f"申请证书成功: {cert}, {key}")
                success = True
            except Exception as e:
                success = False
                logger.error(f"申请证书失败: {str(e)}")



            cert_id = None
            dns_auth_repo = DNSAuthRepository(self.repo.engine)
            if success:
                # 创建证书记录
                cert_data = {
                    "cert_path":cert,
                    "key_path":key,
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

                # 更新下次续期时间
                self.repo.update_next_renew(application_id, cert_data['not_after'])

            else:
                self.execution_repo.fail_execution(execution_id, "申请失败")
                self.repo.update_status(application_id, "failed")
                dns_auth_repo.update_stats(application['dns_auth_id'], False)

            return {
                "execution_id": execution_id,
                "cert_id": cert_id,
                "success": success
            }

        except Exception as e:
            logger.error(f"证书申请失败: {str(e)}")
            self.execution_repo.fail_execution(execution_id, str(e))
            self.repo.update_status(application_id, "failed")
            raise

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

    def get_list(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        """获取列表（带分页）"""
        query = QueryBuilder(self.repo.table)

        for key, value in filters.items():
            if value is not None and hasattr(self.repo.table.c, key):
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

    def get_by_application(self, application_id: int) -> List[Dict[str, Any]]:
        """根据申请ID获取执行历史"""
        return self.repo.get_by_application(application_id)

    def get_latest_by_application(self, application_id: int) -> Optional[Dict[str, Any]]:
        """获取申请的最新执行记录"""
        return self.repo.get_latest_by_application(application_id)
