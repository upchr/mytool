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
        workflow = self.repo.get_by_pk(workflow_id)
        
        # 自动创建v1版本
        version_service = WorkflowVersionService(self.engine)
        version_data = schemas.WorkflowVersionCreate(
            workflow_id=workflow["workflow_id"],
            version=1,
            name=f"{workflow['name']} - v1",
            description=workflow.get("description", ""),
            nodes=workflow.get("nodes", []),
            edges=workflow.get("edges", []),
            change_note="初始版本"
        )
        version_service.create_version_from_data(version_data)
        
        return workflow
    
    def update(self, workflow_id: str, data: schemas.WorkflowUpdate, version_number: int = None) -> Optional[Dict[str, Any]]:
        """
        更新工作流
        
        Args:
            workflow_id: 工作流ID
            data: 更新数据
            version_number: 版本号（如果指定，则更新该版本；否则更新默认版本）
        
        Returns:
            更新后的工作流数据
        """
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return self.repo.get_by_id(workflow_id)
        
        # 如果更新了 nodes 或 edges，更新指定版本
        if "nodes" in update_data or "edges" in update_data:
            # 获取当前工作流信息
            workflow = self.repo.get_by_id(workflow_id)
            if not workflow:
                return None
            
            # 确定要更新的版本号
            version_service = WorkflowVersionService(self.engine)
            if version_number:
                # 更新指定版本
                target_version = version_number
            else:
                # 更新默认版本
                target_version = workflow.get("default_version")
            
            if target_version:
                # 更新指定版本
                version_service.update_version(workflow_id, target_version, update_data)
            else:
                # 如果没有默认版本，创建v1版本
                version_data = schemas.WorkflowVersionCreate(
                    workflow_id=workflow_id,
                    version=1,
                    name=f"{workflow['name']} - v1",
                    description=workflow.get("description", ""),
                    nodes=update_data.get("nodes", workflow.get("nodes", [])),
                    edges=update_data.get("edges", workflow.get("edges", [])),
                    change_note="初始版本"
                )
                version_service.create_version_from_data(version_data)
                update_data["default_version"] = 1
            
            update_data["updated_at"] = datetime.now()
            self.repo.update(workflow_id, update_data)
            
            return self.repo.get_by_id(workflow_id)
        
        # 如果只是更新名称或描述，直接更新工作流
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
            inputs=inputs or {},
            start_time=now,
            created_at=now
        )
        with self.engine.connect() as conn:
            result = conn.execute(query)
            conn.commit()
            execution_id = result.inserted_primary_key[0]
        
        # 异步执行工作流
        from .engine import execute_workflow_sync
        import threading
        
        thread = threading.Thread(
            target=execute_workflow_sync,
            args=(self.engine, execution_id)
        )
        thread.start()
        
        logger.info(f"工作流触发: {workflow_id}, execution_id={execution_id}, inputs={inputs}")
        
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
    
    def validate_workflow_format(self, nodes: List[Dict], edges: List[Dict]) -> Dict[str, Any]:
        """
        验证工作流格式
        
        Args:
            nodes: 节点列表
            edges: 边列表
        
        Returns:
            验证结果 {valid: bool, errors: List[str], warnings: List[str]}
        """
        errors = []
        warnings = []
        
        # 1. 检查节点ID是否唯一
        node_ids = [node.get("id") for node in nodes]
        duplicate_ids = [nid for nid in node_ids if node_ids.count(nid) > 1]
        if duplicate_ids:
            errors.append(f"节点ID重复: {', '.join(set(duplicate_ids))}")
        
        # 2. 检查是否有开始节点
        start_nodes = [node for node in nodes if node.get("type") == "start"]
        if not start_nodes:
            errors.append("缺少开始节点")
        elif len(start_nodes) > 1:
            warnings.append("存在多个开始节点，只会使用第一个")
        
        # 3. 检查是否有结束节点
        end_nodes = [node for node in nodes if node.get("type") == "end"]
        if not end_nodes:
            warnings.append("缺少结束节点，建议添加结束节点以明确工作流终点")
        
        # 4. 检查边是否连接到有效的节点
        node_id_set = set(node_ids)
        invalid_edges = []
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            if source not in node_id_set:
                invalid_edges.append(f"边 {source} -> {target} 的源节点不存在")
            if target not in node_id_set:
                invalid_edges.append(f"边 {source} -> {target} 的目标节点不存在")
        if invalid_edges:
            errors.extend(invalid_edges)
        
        # 5. 检查条件节点是否有表达式
        condition_nodes = [node for node in nodes if node.get("type") == "condition"]
        for node in condition_nodes:
            config = node.get("config", {})
            expression = config.get("expression")
            if not expression:
                errors.append(f"条件节点 {node.get('id')} 缺少表达式")
            elif not isinstance(expression, str):
                errors.append(f"条件节点 {node.get('id')} 的表达式必须是字符串")
        
        # 6. 检查任务节点是否有关联的任务ID
        task_nodes = [node for node in nodes if node.get("type") == "task"]
        for node in task_nodes:
            config = node.get("config", {})
            job_id = config.get("job_id")
            if not job_id:
                warnings.append(f"任务节点 {node.get('id')} 未关联任务ID")
        
        # 7. 检查是否有孤立的节点（没有入边和出边）
        connected_sources = {edge.get("source") for edge in edges}
        connected_targets = {edge.get("target") for edge in edges}
        isolated_nodes = []
        for node in nodes:
            node_id = node.get("id")
            if node_id not in connected_sources and node_id not in connected_targets:
                if node.get("type") not in ["start", "end"]:
                    isolated_nodes.append(node_id)
        if isolated_nodes:
            warnings.append(f"存在孤立节点: {', '.join(isolated_nodes)}")
        
        # 8. 检查循环依赖
        def has_cycle(edges, start, visited=None, path=None):
            if visited is None:
                visited = set()
            if path is None:
                path = []
            
            if start in visited:
                return True, path
            
            visited.add(start)
            path.append(start)
            
            for edge in edges:
                if edge.get("source") == start:
                    next_node = edge.get("target")
                    if has_cycle(edges, next_node, visited.copy(), path.copy())[0]:
                        return True, path
            
            return False, path
        
        for edge in edges:
            source = edge.get("source")
            has_cycle_result, cycle_path = has_cycle(edges, source)
            if has_cycle_result:
                errors.append(f"存在循环依赖: {' -> '.join(cycle_path)}")
                break
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "node_count": len(nodes),
            "edge_count": len(edges)
        }


class WorkflowVersionService:
    """工作流版本管理服务"""
    
    def __init__(self, engine):
        self.engine = engine
    
    def create_version_from_data(self, data: schemas.WorkflowVersionCreate) -> Dict[str, Any]:
        """
        从数据创建工作流版本
        
        Args:
            data: 版本创建数据
        
        Returns:
            版本数据
        """
        create_data = data.model_dump()
        now = datetime.now()
        create_data.update({
            "created_at": now
        })
        
        query = workflow_versions_table.insert().values(**create_data)
        with self.engine.connect() as conn:
            result = conn.execute(query)
            conn.commit()
            version_id = result.inserted_primary_key[0]
        
        return self.get_version(version_id)
    
    def update_version(self, workflow_id: str, version_number: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新指定版本
        
        Args:
            workflow_id: 工作流ID
            version_number: 版本号
            update_data: 更新数据
        
        Returns:
            更新后的版本数据
        """
        # 只允许更新 nodes 和 edges
        allowed_fields = {"nodes", "edges"}
        filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}
        
        if not filtered_data:
            return self.get_version_by_workflow_and_version(workflow_id, version_number)
        
        query = (
            update(workflow_versions_table)
            .where(
                (workflow_versions_table.c.workflow_id == workflow_id) &
                (workflow_versions_table.c.version == version_number)
            )
            .values(**filtered_data)
        )
        with self.engine.connect() as conn:
            conn.execute(query)
            conn.commit()
        
        # 获取更新后的版本数据
        return self.get_version_by_workflow_and_version(workflow_id, version_number)
    
    def create_version(self, workflow_id: str, change_note: str = None, created_by: str = None) -> Dict[str, Any]:
        """
        创建工作流版本（从默认版本复制）
        
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
        
        # 获取默认版本
        default_version = workflow.get("default_version")
        if default_version:
            # 从默认版本复制数据
            default_version_data = self.get_version_by_workflow_and_version(workflow_id, default_version)
            if default_version_data:
                nodes = default_version_data.get("nodes", [])
                edges = default_version_data.get("edges", [])
            else:
                nodes = workflow.get("nodes", [])
                edges = workflow.get("edges", [])
        else:
            # 没有默认版本，从工作流表复制
            nodes = workflow.get("nodes", [])
            edges = workflow.get("edges", [])
        
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
            nodes=nodes,
            edges=edges,
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
    
    def get_version_by_workflow_and_version(self, workflow_id: str, version_number: int) -> Optional[Dict[str, Any]]:
        """
        根据工作流ID和版本号获取版本详情
        
        Args:
            workflow_id: 工作流ID
            version_number: 版本号
        
        Returns:
            版本数据
        """
        query = select(workflow_versions_table).where(
            (workflow_versions_table.c.workflow_id == workflow_id) &
            (workflow_versions_table.c.version == version_number)
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
        # 获取工作流信息
        workflow = WorkflowService(self.engine).get_by_id(workflow_id)
        default_version = workflow.get("default_version") if workflow else None
        
        query = (
            select(workflow_versions_table)
            .where(workflow_versions_table.c.workflow_id == workflow_id)
            .order_by(workflow_versions_table.c.version.desc())
        )
        with self.engine.connect() as conn:
            result = conn.execute(query)
            versions = [dict(row._mapping) for row in result]
        
        # 添加 is_default 字段
        for version in versions:
            version["is_default"] = (version["version"] == default_version)
        
        return versions
    
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
    
    def set_default_version(self, workflow_id: str, version_id: int) -> Dict[str, Any]:
        """
        设置默认版本
        
        Args:
            workflow_id: 工作流ID
            version_id: 版本ID
        
        Returns:
            更新后的工作流数据
        """
        # 验证版本是否存在
        version = self.get_version(version_id)
        if not version:
            raise ValueError(f"版本不存在: {version_id}")
        
        if version["workflow_id"] != workflow_id:
            raise ValueError(f"版本 {version_id} 不属于工作流 {workflow_id}")
        
        # 更新工作流的默认版本
        now = datetime.now()
        update_query = (
            update(workflows_table)
            .where(workflows_table.c.workflow_id == workflow_id)
            .values(default_version=version["version"], updated_at=now)
        )
        with self.engine.connect() as conn:
            conn.execute(update_query)
            conn.commit()
        
        return WorkflowService(self.engine).get_by_id(workflow_id)


__all__ = ["WorkflowService", "WorkflowVersionService"]
