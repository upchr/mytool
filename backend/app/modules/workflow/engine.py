from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import json
import asyncio
from sqlalchemy import select, insert, update
from app.core.db.database import database
from .models import (
    workflows_table,
    workflow_executions_table,
    workflow_node_executions_table
)
from .schemas import NodeTypes

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """工作流执行引擎"""

    def __init__(self):
        self.running_executions: Dict[int, Dict] = {}

    async def start_workflow(self, workflow_id: str, triggered_by: str = "system", inputs: Optional[Dict] = None) -> int:
        """启动工作流"""
        # 获取工作流定义
        query = select(workflows_table).where(workflows_table.c.workflow_id == workflow_id)
        workflow = await database.fetch_one(query)
        if not workflow:
            raise ValueError(f"工作流不存在: {workflow_id}")

        # 创建执行记录
        exec_query = workflow_executions_table.insert().values(
            workflow_id=workflow_id,
            status="running",
            start_time=datetime.utcnow(),
            triggered_by=triggered_by
        )
        exec_result = await database.execute(exec_query)
        execution_id = exec_result.inserted_primary_key[0]

        # 初始化节点执行记录
        nodes = workflow["nodes"] or []
        for node in nodes:
            await self._create_node_execution(execution_id, node)

        # 保存运行状态
        self.running_executions[execution_id] = {
            "workflow": workflow,
            "inputs": inputs or {},
            "outputs": {},
            "current_node": None,
            "status": "running"
        }

        logger.info(f"工作流启动: {workflow_id}, execution_id={execution_id}")

        # 异步执行工作流
        asyncio.create_task(self._execute_workflow(execution_id))

        return execution_id

    async def _execute_workflow(self, execution_id: int):
        """异步执行工作流"""
        try:
            state = self.running_executions.get(execution_id)
            if not state:
                return

            workflow = state["workflow"]
            nodes = workflow["nodes"] or []
            edges = workflow["edges"] or []

            # 构建入边索引
            in_edges: Dict[str, List[Dict]] = {}
            for edge in edges:
                target = edge.get("target")
                if target not in in_edges:
                    in_edges[target] = []
                in_edges[target].append(edge)

            # 找到起始节点（没有入边的节点）
            start_nodes = []
            for node in nodes:
                node_id = node.get("id")
                if node_id not in in_edges or len(in_edges[node_id]) == 0:
                    start_nodes.append(node)

            if not start_nodes:
                raise ValueError("工作流没有起始节点")

            # 执行起始节点
            for node in start_nodes:
                await self._execute_node(execution_id, node, state)

            # 检查工作流是否完成
            await self._check_workflow_complete(execution_id)

        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            await self._fail_workflow(execution_id, str(e))

    async def _execute_node(self, execution_id: int, node: Dict, state: Dict):
        """执行单个节点"""
        node_id = node.get("id")
        node_name = node.get("name", node_id)
        node_type = node.get("type", NodeTypes.TASK)
        config = node.get("config", {})

        logger.info(f"执行节点: {node_name} ({node_id})")

        # 更新节点状态
        await self._update_node_status(execution_id, node_id, "running")

        try:
            # 根据节点类型执行
            if node_type == NodeTypes.TASK:
                result = await self._execute_task_node(node, config, state)
            elif node_type == NodeTypes.CONDITION:
                result = await self._execute_condition_node(node, config, state)
            elif node_type == NodeTypes.WAIT:
                result = await self._execute_wait_node(node, config, state)
            elif node_type == NodeTypes.NOTIFICATION:
                result = await self._execute_notification_node(node, config, state)
            else:
                result = {"status": "success", "output": f"未知节点类型: {node_type}"}

            # 成功处理
            if result.get("status") == "success":
                await self._update_node_status(
                    execution_id, node_id, "success",
                    output=result.get("output")
                )
                # 保存输出
                state["outputs"][node_id] = result.get("output")
                # 执行后续节点
                await self._execute_next_nodes(execution_id, node_id, "success", state)
            else:
                await self._update_node_status(
                    execution_id, node_id, "failed",
                    error=result.get("error", "执行失败")
                )
                # 执行失败分支
                await self._execute_next_nodes(execution_id, node_id, "failure", state)

        except Exception as e:
            logger.error(f"节点执行失败: {node_name}, error: {e}")
            await self._update_node_status(
                execution_id, node_id, "failed",
                error=str(e)
            )
            await self._execute_next_nodes(execution_id, node_id, "failure", state)

    async def _execute_task_node(self, node: Dict, config: Dict, state: Dict) -> Dict:
        """执行任务节点（简化版：直接返回成功）"""
        # TODO: 实际执行命令或调用cron任务
        node_name = node.get("name")
        logger.info(f"执行任务: {node_name}, config={config}")
        return {
            "status": "success",
            "output": f"任务执行完成: {node_name}"
        }

    async def _execute_condition_node(self, node: Dict, config: Dict, state: Dict) -> Dict:
        """执行条件节点"""
        # TODO: 实际条件判断
        return {"status": "success", "output": "条件判断完成"}

    async def _execute_wait_node(self, node: Dict, config: Dict, state: Dict) -> Dict:
        """执行等待节点"""
        wait_seconds = config.get("seconds", 5)
        await asyncio.sleep(wait_seconds)
        return {"status": "success", "output": f"等待 {wait_seconds} 秒完成"}

    async def _execute_notification_node(self, node: Dict, config: Dict, state: Dict) -> Dict:
        """执行通知节点"""
        # TODO: 调用通知插件
        return {"status": "success", "output": "通知发送完成"}

    async def _execute_next_nodes(self, execution_id: int, current_node_id: str, condition: str, state: Dict):
        """执行后续节点"""
        workflow = state["workflow"]
        edges = workflow["edges"] or []
        nodes = workflow["nodes"] or []
        node_map = {n.get("id"): n for n in nodes}

        # 找到匹配条件的出边
        next_node_ids = []
        for edge in edges:
            if edge.get("source") == current_node_id:
                edge_condition = edge.get("condition", "success")
                if edge_condition == "always" or edge_condition == condition:
                    target = edge.get("target")
                    if target and target not in next_node_ids:
                        next_node_ids.append(target)

        # 执行后续节点
        for next_node_id in next_node_ids:
            # 检查前置条件是否都满足
            if await self._check_dependencies_met(execution_id, next_node_id, edges):
                next_node = node_map.get(next_node_id)
                if next_node:
                    await self._execute_node(execution_id, next_node, state)

    async def _check_dependencies_met(self, execution_id: int, node_id: str, edges: List[Dict]) -> bool:
        """检查节点的所有依赖是否都已完成"""
        # 获取该节点的所有入边
        in_edges = [e for e in edges if e.get("target") == node_id]
        if not in_edges:
            return True

        # 检查所有源节点
        for edge in in_edges:
            source_id = edge.get("source")
            source_status = await self._get_node_status(execution_id, source_id)
            edge_condition = edge.get("condition", "success")

            # 如果有任何一个依赖不满足，返回False
            if edge_condition == "success" and source_status != "success":
                return False
            if edge_condition == "failure" and source_status != "failed":
                return False

        return True

    async def _create_node_execution(self, execution_id: int, node: Dict):
        """创建节点执行记录"""
        query = workflow_node_executions_table.insert().values(
            execution_id=execution_id,
            node_id=node.get("id"),
            node_name=node.get("name"),
            status="pending"
        )
        await database.execute(query)

    async def _update_node_status(
        self,
        execution_id: int,
        node_id: str,
        status: str,
        output: Optional[str] = None,
        error: Optional[str] = None
    ):
        """更新节点状态"""
        now = datetime.utcnow()
        values = {"status": status}

        if status == "running":
            values["start_time"] = now
        if status in ["success", "failed", "skipped"]:
            values["end_time"] = now
        if output:
            values["output"] = output
        if error:
            values["error"] = error

        query = (
            update(workflow_node_executions_table)
            .where(
                workflow_node_executions_table.c.execution_id == execution_id,
                workflow_node_executions_table.c.node_id == node_id
            )
            .values(**values)
        )
        await database.execute(query)

    async def _get_node_status(self, execution_id: int, node_id: str) -> Optional[str]:
        """获取节点状态"""
        query = (
            select(workflow_node_executions_table.c.status)
            .where(
                workflow_node_executions_table.c.execution_id == execution_id,
                workflow_node_executions_table.c.node_id == node_id
            )
        )
        result = await database.fetch_one(query)
        return result["status"] if result else None

    async def _check_workflow_complete(self, execution_id: int):
        """检查工作流是否完成"""
        # 获取所有节点状态
        query = (
            select(workflow_node_executions_table.c.status)
            .where(workflow_node_executions_table.c.execution_id == execution_id)
        )
        node_statuses = await database.fetch_all(query)
        statuses = [s["status"] for s in node_statuses]

        # 如果所有节点都是终态
        if all(s in ["success", "failed", "skipped"] for s in statuses):
            if any(s == "failed" for s in statuses):
                await self._fail_workflow(execution_id, "部分节点执行失败")
            else:
                await self._complete_workflow(execution_id)

    async def _complete_workflow(self, execution_id: int):
        """完成工作流"""
        query = (
            update(workflow_executions_table)
            .where(workflow_executions_table.c.id == execution_id)
            .values(
                status="success",
                end_time=datetime.utcnow()
            )
        )
        await database.execute(query)

        if execution_id in self.running_executions:
            del self.running_executions[execution_id]

        logger.info(f"工作流执行成功: execution_id={execution_id}")

    async def _fail_workflow(self, execution_id: int, error: str):
        """工作流失败"""
        query = (
            update(workflow_executions_table)
            .where(workflow_executions_table.c.id == execution_id)
            .values(
                status="failed",
                end_time=datetime.utcnow(),
                error=error
            )
        )
        await database.execute(query)

        if execution_id in self.running_executions:
            del self.running_executions[execution_id]

        logger.error(f"工作流执行失败: execution_id={execution_id}, error={error}")


# 全局引擎实例
workflow_engine = WorkflowEngine()
