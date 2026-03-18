from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select, update, delete, and_, or_, func
from app.core.db.database import database
from .models import (
    workflows_table,
    workflow_executions_table,
    workflow_node_executions_table
)
from .schemas import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowQueryParams,
    BUILTIN_WORKFLOWS
)
from .engine import workflow_engine
import logging

logger = logging.getLogger(__name__)


class WorkflowService:
    """工作流服务"""

    @staticmethod
    async def get_workflow(workflow_id: str) -> Optional[Dict]:
        """获取单个工作流"""
        query = select(workflows_table).where(workflows_table.c.workflow_id == workflow_id)
        return await database.fetch_one(query)

    @staticmethod
    async def list_workflows(params: WorkflowQueryParams) -> tuple[List[Dict], int]:
        """列出工作流（带分页和筛选）"""
        query = select(workflows_table).where(workflows_table.c.is_active == True)

        # 筛选条件
        if params.node_id:
            query = query.where(workflows_table.c.node_id == params.node_id)
        if params.is_active is not None:
            query = query.where(workflows_table.c.is_active == params.is_active)
        if params.keyword:
            keyword = f"%{params.keyword}%"
            query = query.where(
                or_(
                    workflows_table.c.name.like(keyword),
                    workflows_table.c.description.like(keyword)
                )
            )

        # 总数
        count_query = select(func.count()).select_from(query.subquery())
        total = await database.fetch_val(count_query)

        # 分页
        offset = (params.page - 1) * params.page_size
        query = query.order_by(workflows_table.c.created_at.desc()).offset(offset).limit(params.page_size)

        workflows = await database.fetch_all(query)
        return workflows, total

    @staticmethod
    async def create_workflow(data: WorkflowCreate) -> Dict:
        """创建工作流"""
        now = datetime.utcnow()
        query = workflows_table.insert().values(
            **data.model_dump(),
            created_at=now,
            updated_at=now
        )
        record_id = await database.execute(query)

        return await WorkflowService.get_workflow(data.workflow_id)

    @staticmethod
    async def update_workflow(workflow_id: str, data: WorkflowUpdate) -> Optional[Dict]:
        """更新工作流"""
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return await WorkflowService.get_workflow(workflow_id)

        update_data["updated_at"] = datetime.utcnow()
        query = (
            update(workflows_table)
            .where(workflows_table.c.workflow_id == workflow_id)
            .values(**update_data)
        )
        await database.execute(query)
        return await WorkflowService.get_workflow(workflow_id)

    @staticmethod
    async def delete_workflow(workflow_id: str) -> bool:
        """删除工作流"""
        query = (
            update(workflows_table)
            .where(workflows_table.c.workflow_id == workflow_id)
            .values(is_active=False, updated_at=datetime.utcnow())
        )
        await database.execute(query)
        return True

    @staticmethod
    async def trigger_workflow(workflow_id: str, triggered_by: str = "manual", inputs: Optional[Dict] = None) -> int:
        """触发工作流执行"""
        return await workflow_engine.start_workflow(workflow_id, triggered_by, inputs)

    @staticmethod
    async def get_execution(execution_id: int) -> Optional[Dict]:
        """获取执行记录"""
        query = select(workflow_executions_table).where(workflow_executions_table.c.id == execution_id)
        return await database.fetch_one(query)

    @staticmethod
    async def get_executions(workflow_id: str, limit: int = 20) -> List[Dict]:
        """获取工作流的执行记录"""
        query = (
            select(workflow_executions_table)
            .where(workflow_executions_table.c.workflow_id == workflow_id)
            .order_by(workflow_executions_table.c.created_at.desc())
            .limit(limit)
        )
        return await database.fetch_all(query)

    @staticmethod
    async def get_node_executions(execution_id: int) -> List[Dict]:
        """获取执行的节点记录"""
        query = (
            select(workflow_node_executions_table)
            .where(workflow_node_executions_table.c.execution_id == execution_id)
            .order_by(workflow_node_executions_table.c.created_at)
        )
        return await database.fetch_all(query)


# ========== 初始化内置工作流 ==========

async def init_builtin_workflows():
    """初始化内置工作流到数据库"""
    from .schemas import WorkflowCreate

    for wf_data in BUILTIN_WORKFLOWS:
        # 检查是否已存在
        existing = await WorkflowService.get_workflow(wf_data["workflow_id"])
        if existing:
            continue

        # 创建工作流（需要node_id，先默认1）
        workflow_data = WorkflowCreate(
            workflow_id=wf_data["workflow_id"],
            name=wf_data["name"],
            description=wf_data["description"],
            node_id=1,
            nodes=wf_data["nodes"],
            edges=wf_data["edges"],
            is_active=True
        )
        await WorkflowService.create_workflow(workflow_data)
        logger.info(f"内置工作流初始化完成: {wf_data['workflow_id']}")
