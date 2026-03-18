# app/modules/workflow/services.py
"""
工作流模块 - 业务逻辑层

包含：
- WorkflowService: 工作流管理服务
- WorkflowVersionService: 版本管理服务
- WorkflowExecutionService: 执行管理服务
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select, func, update, delete, and_, or_

from app.core.db.utils.query import QueryBuilder
from app.modules.workflow.models import (
    workflows_table,
    workflow_executions_table,
    workflow_node_executions_table,
    workflow_versions_table
)
from app.modules.workflow import schemas

logger = logging.getLogger(__name__)


class WorkflowRepository:
    """工作流数据访问层"""
    
    def __init__(self, engine):
        self.engine = engine
        self.table = workflows_table
    
    def create(self, data: Dict[str, Any]) -> int:
        """创建工作流"""
        query = self.table.insert().values(**data)
        with self.engine.connect() as conn:
            result = conn.execute(query)
            conn.commit()
            return result.inserted_primary_key[0]
    
    def update(self, workflow_id: str, data: Dict[str, Any]) -> bool:
        """更新工作流"""
        query = (
            self.table.update()
            .where(self.table.c.workflow_id == workflow_id)
            .values(**data)
        )
        with self.engine.connect() as conn:
            result = conn.execute(query)
            conn.commit()
            return result.rowcount > 0
    
    def delete(self, workflow_id: str) -> bool:
        """删除工作流（软删除）"""
        query = (
            self.table.update()
            .where(self.table.c.workflow_id == workflow_id)
            .values(is_active=False, updated_at=datetime.now())
        )
        with self.engine.connect() as conn:
            result = conn.execute(query)
            conn.commit()
            return result.rowcount > 0
    
    def get_by_id(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """根据 workflow_id 获取工作流"""
        query = select(self.table).where(self.table.c.workflow_id == workflow_id)
        with self.engine.connect() as conn:
            result = conn.execute(query)
            row = result.first()
            return dict(row._mapping) if row else None
    
    def get_by_pk(self, id: int) -> Optional[Dict[str, Any]]:
        """根据主键获取工作流"""
        query = select(self.table).where(self.table.c.id == id)
        with self.engine.connect() as conn:
            result = conn.execute(query)
            row = result.first()
            return dict(row._mapping) if row else None
    
    def get_list(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        """获取工作流列表（分页）"""
        query = QueryBuilder(self.table)
        
        # 默认只查询启用的
        query.where_eq('is_active', True)
        
        # 过滤条件
        for key, value in filters.items():
            if value is not None:
                if key == 'keyword':
                    query.where_like('name', f'%{value}%')
                elif hasattr(self.table.c, key):
                    query.where_eq(key, value)
        
        return query.paginate(self.engine, page, page_size)


class WorkflowService:
    """工作流管理服务"""
    
    def __init__(self, engine):
        self.repo = WorkflowRepository(engine)
        self.engine = engine
    
    def create(self, data: schemas.WorkflowCreate) -> Dict[str, Any]:
        """
        创建工作流
        
        Args:
            data: 创建数据
        
        Returns:
            创建后的工作流数据
        """
        create_data = data.model_dump()
        now = datetime.now()
        create_data.update({
            "created_at": now,
            "updated_at": now
        })
        
        workflow_id = self.repo.create(create_data)
        return self.repo.get_by_pk(workflow_id)
    
    def update(self, workflow_id: str, data: schemas.WorkflowUpdate) -> Optional[Dict[str, Any]]:
        """
        更新工作流
        
        Args:
            workflow_id: 工作流ID
            data: 更新数据
        
        Returns:
            更新后的工作流数据
        """
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return self.repo.get_by_id(workflow_id)
        
        update_data["updated_at"] = datetime.now()
        self.repo.update(workflow_id, update_data)
        return self.repo.get_by_id(workflow_id)
    
    def delete(self, workflow_id: str) -> bool:
        """
        删除工作流（软删除）
        
        Args:
            workflow_id: 工作流ID
        
        Returns:
            是否删除成功
        """
        return self.repo.delete(workflow_id)
    
    def get_by_id(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        获取工作流详情
        
        Args:
            workflow_id: 工作流ID
        
        Returns:
            工作流数据
        """
        return self.repo.get_by_id(workflow_id)
    
    def get_list(self, params: schemas.WorkflowQueryParams) -> Dict[str, Any]:
        """
        获取工作流列表
        
        Args:
            params: 查询参数
        
        Returns:
            分页结果
        """
        return self.repo.get_list(
            page=params.page,
            page_size=params.page_size,
            node_id=params.node_id,
            is_active=params.is_active,
            keyword=params.keyword
        )
    
    def trigger(self, workflow_id: str, triggered_by: str = "manual", inputs: Optional[Dict] = None) -> int:
        """
        触发工作流执行
        
        Args:
            workflow_id: 工作流ID
            triggered_by: 触发方式
            inputs: 输入参数
        
        Returns:
            执行记录ID
        """
        # 创建执行记录
        now = datetime.now()
        query = workflow_executions_table.insert().values(
            workflow_id=workflow_id,
            status="pending",
            triggered_by=triggered_by,
            start_time=now,
            created_at=now
        )
        with self.engine.connect() as conn:
            result = conn.execute(query)
            conn.commit()
            execution_id = result.inserted_primary_key[0]
        
        # TODO: 异步执行工作流
        logger.info(f"工作流触发: {workflow_id}, execution_id={execution_id}")
        
        return execution_id
    
    def get_executions(self, workflow_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取工作流执行记录
        
        Args:
            workflow_id: 工作流ID
            limit: 返回条数
        
        Returns:
            执行记录列表
        """
        query = (
            select(workflow_executions_table)
            .where(workflow_executions_table.c.workflow_id == workflow_id)
            .order_by(workflow_executions_table.c.created_at.desc())
            .limit(limit)
        )
        with self.engine.connect() as conn:
            result = conn.execute(query)
            return [dict(row._mapping) for row in result]
    
    def get_execution(self, execution_id: int) -> Optional[Dict[str, Any]]:
        """
        获取执行记录详情
        
        Args:
            execution_id: 执行记录ID
        
        Returns:
            执行记录
        """
        query = select(workflow_executions_table).where(
            workflow_executions_table.c.id == execution_id
        )
        with self.engine.connect() as conn:
            result = conn.execute(query)
            row = result.first()
            return dict(row._mapping) if row else None
    
    def get_node_executions(self, execution_id: int) -> List[Dict[str, Any]]:
        """
        获取节点执行记录
        
        Args:
            execution_id: 执行记录ID
        
        Returns:
            节点执行记录列表
        """
        query = (
            select(workflow_node_executions_table)
            .where(workflow_node_executions_table.c.execution_id == execution_id)
            .order_by(workflow_node_executions_table.c.created_at)
        )
        with self.engine.connect() as conn:
            result = conn.execute(query)
            return [dict(row._mapping) for row in result]


class WorkflowVersionService:
    """工作流版本管理服务"""
    
    def __init__(self, engine):
        self.engine = engine
    
    def create_version(self, workflow_id: str, change_note: str = None, created_by: str = None) -> Dict[str, Any]:
        """
        创建工作流版本
        
        Args:
            workflow_id: 工作流ID
            change_note: 变更说明
            created_by: 创建者
        
        Returns:
            版本数据
        """
        # 获取当前工作流
        workflow = WorkflowService(self.engine).get_by_id(workflow_id)
        if not workflow:
            raise ValueError(f"工作流不存在: {workflow_id}")
        
        # 获取最大版本号
        max_version_query = select(func.max(workflow_versions_table.c.version)).where(
            workflow_versions_table.c.workflow_id == workflow_id
        )
        with self.engine.connect() as conn:
            max_version = conn.execute(max_version_query).scalar() or 0
        new_version = max_version + 1
        
        # 创建版本
        now = datetime.now()
        query = workflow_versions_table.insert().values(
            workflow_id=workflow_id,
            version=new_version,
            name=workflow["name"],
            description=workflow["description"],
            nodes=workflow["nodes"],
            edges=workflow["edges"],
            change_note=change_note,
            created_by=created_by,
            created_at=now
        )
        with self.engine.connect() as conn:
            result = conn.execute(query)
            conn.commit()
            version_id = result.inserted_primary_key[0]
        
        # 返回版本数据
        return self.get_version(version_id)
    
    def get_version(self, version_id: int) -> Optional[Dict[str, Any]]:
        """
        获取版本详情
        
        Args:
            version_id: 版本ID
        
        Returns:
            版本数据
        """
        query = select(workflow_versions_table).where(
            workflow_versions_table.c.id == version_id
        )
        with self.engine.connect() as conn:
            result = conn.execute(query)
            row = result.first()
            return dict(row._mapping) if row else None
    
    def list_versions(self, workflow_id: str) -> List[Dict[str, Any]]:
        """
        获取版本列表
        
        Args:
            workflow_id: 工作流ID
        
        Returns:
            版本列表
        """
        query = (
            select(workflow_versions_table)
            .where(workflow_versions_table.c.workflow_id == workflow_id)
            .order_by(workflow_versions_table.c.version.desc())
        )
        with self.engine.connect() as conn:
            result = conn.execute(query)
            return [dict(row._mapping) for row in result]
    
    def restore_version(self, version_id: int, change_note: str = None) -> Dict[str, Any]:
        """
        恢复到指定版本
        
        Args:
            version_id: 版本ID
            change_note: 恢复说明
        
        Returns:
            恢复后的工作流数据
        """
        version = self.get_version(version_id)
        if not version:
            raise ValueError(f"版本不存在: {version_id}")
        
        workflow_id = version["workflow_id"]
        
        # 先创建当前版本的快照
        self.create_version(
            workflow_id,
            change_note=f"恢复前自动备份 (恢复版本 v{version['version']})",
            created_by="system"
        )
        
        # 更新工作流
        now = datetime.now()
        update_query = (
            update(workflows_table)
            .where(workflows_table.c.workflow_id == workflow_id)
            .values(
                name=version["name"],
                description=version["description"],
                nodes=version["nodes"],
                edges=version["edges"],
                updated_at=now
            )
        )
        with self.engine.connect() as conn:
            conn.execute(update_query)
            conn.commit()
        
        # 创建恢复版本
        self.create_version(
            workflow_id,
            change_note=change_note or f"恢复到版本 v{version['version']}",
            created_by="user"
        )
        
        return WorkflowService(self.engine).get_by_id(workflow_id)


__all__ = ["WorkflowService", "WorkflowVersionService"]
