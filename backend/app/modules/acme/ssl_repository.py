# app/modules/acme/ssl_repository.py
import json
from typing import List, Dict, Any, Optional
from sqlalchemy import select, insert, update, delete, desc, Engine, func, and_
from datetime import datetime, timedelta

from app.core.db.utils.repository import BaseRepository
from app.core.db.utils.query import QueryBuilder
from app.modules.acme import models
from app.modules.acme.schemas import PendingRenewApplication


class DNSAuthRepository(BaseRepository):
    """DNS授权仓储类"""

    def __init__(self, engine: Engine):
        super().__init__(engine, models.ssl_dns_auth_table)

    def get_by_provider(self, provider: str) -> List[Dict[str, Any]]:
        """根据提供商查询"""
        query = QueryBuilder(self.table) \
            .where_eq('provider', provider) \
            .order_by(desc('created_at'))
        return query.execute(self.engine)

    def get_active_list(self) -> List[Dict[str, Any]]:
        """获取启用的授权列表"""
        query = QueryBuilder(self.table) \
            .where_eq('is_active', True) \
            .order_by(desc('created_at'))
        return query.execute(self.engine)

    def update_stats(self, id: int, success: bool):
        """更新使用统计"""
        with self.engine.begin() as conn:
            # 先查询当前值
            stmt = select(self.table.c.total_applications, self.table.c.total_success) \
                .where(self.table.c.id == id)
            current = conn.execute(stmt).first()

            if current:
                total_apps = current[0] + 1
                total_success = current[1] + (1 if success else 0)

                # 更新
                update_stmt = update(self.table) \
                    .where(self.table.c.id == id) \
                    .values(
                    total_applications=total_apps,
                    total_success=total_success,
                    last_used_at=datetime.now()
                )
                conn.execute(update_stmt)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.engine.connect() as conn:
            # 总数
            total = conn.execute(select(func.count()).select_from(self.table)).scalar()

            # 活跃数
            active = conn.execute(
                select(func.count()).select_from(self.table).where(self.table.c.is_active == True)
            ).scalar()

            # 总申请次数
            total_apps = conn.execute(
                select(func.sum(self.table.c.total_applications))
            ).scalar() or 0

            # 总成功次数
            total_success = conn.execute(
                select(func.sum(self.table.c.total_success))
            ).scalar() or 0

            return {
                "total": total,
                "active": active,
                "total_applications_sum": total_apps,
                "total_success_sum": total_success,
                "success_rate": round((total_success / total_apps * 100) if total_apps > 0 else 0, 2)
            }


class ApplicationRepository(BaseRepository):
    """证书申请仓储类"""

    def __init__(self, engine: Engine):
        super().__init__(engine, models.ssl_applications_table)

    def get_by_dns_auth(self, dns_auth_id: int) -> List[Dict[str, Any]]:
        """根据DNS授权ID查询"""
        query = QueryBuilder(self.table) \
            .where_eq('dns_auth_id', dns_auth_id) \
            .order_by(desc('created_at'))
        return query.execute(self.engine)

    def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """根据状态查询"""
        query = QueryBuilder(self.table) \
            .where_eq('status', status) \
            .order_by(desc('created_at'))
        return query.execute(self.engine)

    def get_pending_renew(self) -> list[PendingRenewApplication]:
        """获取需要续期的申请"""
        now = datetime.now()
        query = QueryBuilder(self.table) \
            .where_eq('auto_renew', True) \
            .where_eq('status', 'completed') \
            .where(self.table.c.next_renew_at <= now) \
            .order_by('next_renew_at')

        with self.engine.connect() as conn:
            result = conn.execute(query.build(), {"now": now})
            from app.modules.acme.schemas import PendingRenewApplication
            return [PendingRenewApplication.model_validate(row) for row in result.mappings()]

    def update_status(self, id: int, status: str, **kwargs):
        """更新状态"""
        data = {"status": status, "updated_at": datetime.now()}
        data.update(kwargs)
        return self.update(id, data)

    def update_next_renew(self, id: int, not_after: datetime):
        """更新下次续期时间"""
        renew_before = self.get_by_id(id).get('renew_before', 30)
        next_renew = not_after - timedelta(days=renew_before)
        return self.update(id, {"next_renew_at": next_renew})

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.engine.connect() as conn:
            # 总数
            total = conn.execute(select(func.count()).select_from(self.table)).scalar()

            # 各状态数量
            status_counts = {}
            for status in ['pending', 'processing', 'completed', 'failed']:
                count = conn.execute(
                    select(func.count()).select_from(self.table).where(self.table.c.status == status)
                ).scalar()
                status_counts[status] = count

            # 自动续期数量
            auto_renew = conn.execute(
                select(func.count()).select_from(self.table).where(self.table.c.auto_renew == True)
            ).scalar()

            return {
                "total": total,
                **status_counts,
                "auto_renew_enabled": auto_renew
            }


class ExecutionRepository(BaseRepository):
    """执行历史仓储类"""

    def __init__(self, engine: Engine):
        super().__init__(engine, models.ssl_application_executions_table)

    def get_by_application(self, application_id: int) -> List[Dict[str, Any]]:
        """根据申请ID查询"""
        query = QueryBuilder(self.table) \
            .where_eq('application_id', application_id) \
            .order_by(desc('created_at'))
        return query.execute(self.engine)

    def get_latest_by_application(self, application_id: int) -> Optional[Dict[str, Any]]:
        """获取申请的最新执行记录"""
        query = QueryBuilder(self.table) \
            .where_eq('application_id', application_id) \
            .order_by(desc('created_at')) \
            .limit(1)
        result = query.execute(self.engine)
        return result[0] if result else None

    def start_execution(self, application_id: int, triggered_by: str = "system") -> int:
        """开始执行"""
        data = {
            "application_id": application_id,
            "triggered_by": triggered_by,
            "status": "processing",
            "started_at": datetime.now()
        }
        return self.create(data)

    def complete_execution(self, id: int, success: bool, cert_id: int = None, log: str = None):
        """完成执行"""
        data = {
            "status": "success" if success else "failed",
            "completed_at": datetime.now()
        }
        if cert_id:
            data["cert_id"] = cert_id
        if log:
            data["log"] = log
        return self.update(id, data)

    def fail_execution(self, id: int, error: str):
        """执行失败"""
        return self.update(id, {
            "status": "failed",
            "error": error,
            "log": error,
            "completed_at": datetime.now()
        })


class CertificateRepository(BaseRepository):
    """证书仓储类"""

    def __init__(self, engine: Engine):
        super().__init__(engine, models.ssl_certificates_table)

    def get_by_application(self, application_id: int) -> List[Dict[str, Any]]:
        """根据申请ID查询"""
        query = QueryBuilder(self.table) \
            .where_eq('application_id', application_id) \
            .order_by(desc('created_at'))
        return query.execute(self.engine)

    def get_valid_by_domain(self, domain: str) -> List[Dict[str, Any]]:
        """获取域名的有效证书"""
        now = datetime.now()
        query = QueryBuilder(self.table) \
            .where_eq('is_active', True) \
            .where('not_before <= :now') \
            .where('not_after >= :now') \
            .order_by(desc('not_after'))

        with self.engine.connect() as conn:
            result = conn.execute(query.build(), {"now": now})
            # 需要过滤包含该域名的证书
            certificates = []
            for row in result.mappings():
                domains = json.loads(row['domains'])
                if domain in domains:
                    certificates.append(dict(row))
            return certificates

    def get_expiring_soon(self, days: int = 30) -> List[Dict[str, Any]]:
        """获取即将过期的证书"""
        now = datetime.now()
        threshold = now + timedelta(days=days)
        query = QueryBuilder(self.table) \
            .where_eq('is_active', True) \
            .where('not_after <= :threshold') \
            .order_by('not_after')

        with self.engine.connect() as conn:
            result = conn.execute(query.build(), {"threshold": threshold})
            return [dict(row) for row in result.mappings()]

    def deactivate_old_certificates(self, application_id: int, new_cert_id: int):
        """停用旧证书"""
        stmt = update(self.table) \
            .where(self.table.c.application_id == application_id) \
            .where(self.table.c.is_active == True) \
            .where(self.table.c.id != new_cert_id) \
            .values(is_active=False, renewed_by=new_cert_id)

        with self.engine.begin() as conn:
            conn.execute(stmt)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        now = datetime.now()
        expiring_soon = now + timedelta(days=30)

        with self.engine.connect() as conn:
            # 总数
            total = conn.execute(select(func.count()).select_from(self.table)).scalar()

            # 活跃数
            active = conn.execute(
                select(func.count()).select_from(self.table).where(self.table.c.is_active == True)
            ).scalar()

            # 过期数
            expired = conn.execute(
                select(func.count()).select_from(self.table) \
                    .where(self.table.c.is_active == True) \
                    .where(self.table.c.not_after < now)
            ).scalar()

            # 即将过期
            expiring = conn.execute(
                select(func.count()).select_from(self.table) \
                    .where(self.table.c.is_active == True) \
                    .where(self.table.c.not_after >= now) \
                    .where(self.table.c.not_after <= expiring_soon)
            ).scalar()

            # 按算法分布
            algorithms = {}
            for algo in ['RSA', 'ECC']:
                count = conn.execute(
                    select(func.count()).select_from(self.table).where(self.table.c.algorithm == algo)
                ).scalar()
                algorithms[algo] = count

            return {
                "total": total,
                "active": active,
                "expired": expired,
                "expiring_soon": expiring,
                "by_algorithm": algorithms
            }


class DownloadLogRepository(BaseRepository):
    """下载日志仓储类"""

    def __init__(self, engine: Engine):
        super().__init__(engine, models.ssl_download_logs_table)

    def get_by_certificate(self, cert_id: int) -> List[Dict[str, Any]]:
        """根据证书ID查询"""
        query = QueryBuilder(self.table) \
            .where_eq('cert_id', cert_id) \
            .order_by(desc('downloaded_at'))
        return query.execute(self.engine)

    def get_download_count(self, cert_id: int) -> int:
        """获取证书下载次数"""
        stmt = select(func.count()).select_from(self.table).where(self.table.c.cert_id == cert_id)
        with self.engine.connect() as conn:
            return conn.execute(stmt).scalar() or 0
