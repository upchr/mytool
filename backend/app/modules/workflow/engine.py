# app/modules/workflow/engine.py
"""
工作流执行引擎

负责解析和执行工作流节点
"""
import logging
import asyncio
import re
import json
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy import select, update, func

from app.modules.workflow.models import (
    workflows_table,
    workflow_executions_table,
    workflow_node_executions_table
)

logger = logging.getLogger(__name__)


class AttrDict(dict):
    """支持属性访问的字典类（支持嵌套访问）"""
    def __getattr__(self, key):
        try:
            value = self[key]
            # 如果值是字典，自动包装成 AttrDict 以支持嵌套访问
            if isinstance(value, dict) and not isinstance(value, AttrDict):
                return AttrDict(value)
            return value
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{key}'")


class WorkflowVariableResolver:
    """工作流变量解析器"""

    @staticmethod
    def resolve(value: str, state: Dict[str, Any]) -> Any:
        """
        解析变量 {{inputs.xxx}} 或 {{outputs.node1.xxx}}

        Args:
            value: 包含变量的字符串
            state: 当前状态（inputs、outputs）

        Returns:
            解析后的值
        """
        if not isinstance(value, str):
            return value

        pattern = r'\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}'

        def replace_var(match):
            var_path = match.group(1)
            parts = var_path.split('.')

            current = state
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return match.group(0)  # 找不到则保留原样

            return str(current) if current is not None else ''

        result = re.sub(pattern, replace_var, value)

        # 如果没有变化，直接返回
        if result == value:
            return value

        # 尝试解析为 JSON
        try:
            return json.loads(result)
        except (json.JSONDecodeError, TypeError):
            return result

    @staticmethod
    def evaluate_condition(expression: str, state: Dict[str, Any]) -> bool:
        """
        评估条件表达式

        Args:
            expression: 条件表达式（如 {{inputs.count}} > 5）
            state: 当前状态

        Returns:
            条件结果
        """
        try:
            resolved_expr = WorkflowVariableResolver.resolve(expression, state)

            # 安全的全局变量
            safe_globals = {
                '__builtins__': {},
                'True': True,
                'False': False,
                'None': None,
                'inputs': AttrDict(state.get('inputs', {})),
                'outputs': AttrDict(state.get('outputs', {}))
            }

            result = eval(str(resolved_expr), safe_globals, {})
            return bool(result)
        except Exception as e:
            logger.error(f"条件表达式评估失败: {expression}, error: {e}")
            return False


class WorkflowEngine:
    """工作流执行引擎"""

    def __init__(self, engine):
        self.engine = engine

    async def execute_workflow(self, execution_id: int):
        """
        执行工作流

        Args:
            execution_id: 执行记录ID
        """
        # 获取执行记录
        execution = await self._get_execution(execution_id)
        if not execution:
            logger.error(f"执行记录不存在: {execution_id}")
            return

        workflow_id = execution["workflow_id"]

        # 获取工作流定义
        workflow = await self._get_workflow(workflow_id)
        if not workflow:
            logger.error(f"工作流不存在: {workflow_id}")
            await self._update_execution(execution_id, "failed", error="工作流不存在")
            return

        # 初始化状态，从执行记录中获取输入参数
        state = {
            "inputs": execution.get("inputs", {}),
            "outputs": {},
            "executed_nodes": set(),  # 跟踪已执行的节点
            "workflow": workflow
        }

        logger.info(f"工作流执行开始: {workflow_id}, execution_id={execution_id}, inputs={state['inputs']}")

        # 更新执行状态为运行中
        await self._update_execution(execution_id, "running")

        try:
            # 获取起始节点（没有入边的节点）
            nodes = workflow.get("nodes", [])
            edges = workflow.get("edges", [])

            start_nodes = self._find_start_nodes(nodes, edges)

            # 执行起始节点
            for node in start_nodes:
                await self._execute_node(execution_id, node, state, nodes, edges)

            # 更新执行状态为成功
            await self._update_execution(execution_id, "success")
            logger.info(f"工作流执行成功: {workflow_id}, execution_id={execution_id}")

        except Exception as e:
            logger.error(f"工作流执行失败: {workflow_id}, error: {e}")
            await self._update_execution(execution_id, "failed", error=str(e))

    async def _execute_node(self, execution_id: int, node: Dict, state: Dict,
                            all_nodes: list, all_edges: list):
        """
        执行单个节点

        Args:
            execution_id: 执行记录ID
            node: 节点定义
            state: 当前状态
            all_nodes: 所有节点
            all_edges: 所有边
        """
        node_id = node.get("id")
        node_type = node.get("type", "task")
        config = node.get("config", {})
        node_name = node.get("name", node_id)

        # 检查节点是否已经执行过
        if node_id in state["executed_nodes"]:
            logger.info(f"节点 {node_id} 已经执行过，跳过")
            return

        # 标记节点为已执行
        state["executed_nodes"].add(node_id)

        # 开始节点
        if node_type == "start":
            logger.info(f"开始节点: {node_name}")

            # 创建节点执行记录
            node_execution_id = await self._create_node_execution(
                execution_id, node_id, node_name, node_type
            )

            # 获取后置节点
            next_nodes = []
            for edge in all_edges:
                if edge.get("source") == node_id:
                    next_nodes.append(edge.get("target"))

            # 记录节点开始执行
            await self._add_node_log(node_execution_id, f"节点开始执行: {node_name} ({node_type})", "info")
            await self._add_node_log(node_execution_id, f"前置节点: 无", "info")
            await self._add_node_log(node_execution_id, f"后置节点: {', '.join(next_nodes) if next_nodes else '无'}", "info")

            # 更新节点状态为成功
            await self._update_node_execution(node_execution_id, "success", output="开始节点")

            # 执行后续节点
            await self._execute_next_nodes(execution_id, node_id, "success", state, all_nodes, all_edges, node_execution_id)
            return

        # 结束节点
        if node_type == "end":
            logger.info(f"结束节点: {node_name}")

            # 创建节点执行记录
            node_execution_id = await self._create_node_execution(
                execution_id, node_id, node_name, node_type
            )

            # 获取前置节点
            prev_nodes = []
            for edge in all_edges:
                if edge.get("target") == node_id:
                    prev_nodes.append(edge.get("source"))

            # 记录节点开始执行
            await self._add_node_log(node_execution_id, f"节点开始执行: {node_name} ({node_type})", "info")
            await self._add_node_log(node_execution_id, f"前置节点: {', '.join(prev_nodes) if prev_nodes else '无'}", "info")
            await self._add_node_log(node_execution_id, f"后置节点: 无", "info")

            # 更新节点状态为成功
            await self._update_node_execution(node_execution_id, "success", output="结束节点")
            return

        # AND 和 OR 节点需要创建执行记录来记录日志
        if node_type in ["and", "or"]:
            # 创建节点执行记录
            node_execution_id = await self._create_node_execution(
                execution_id, node_id, node_name, node_type
            )

            # 获取前置节点和后置节点
            prev_nodes = []
            next_nodes = []
            for edge in all_edges:
                if edge.get("target") == node_id:
                    prev_nodes.append(edge.get("source"))
                elif edge.get("source") == node_id:
                    next_nodes.append(edge.get("target"))

            # 记录节点开始执行
            await self._add_node_log(node_execution_id, f"节点开始执行: {node_name} ({node_type})", "info")
            await self._add_node_log(node_execution_id, f"前置节点: {', '.join(prev_nodes) if prev_nodes else '无'}", "info")
            await self._add_node_log(node_execution_id, f"后置节点: {', '.join(next_nodes) if next_nodes else '无'}", "info")

            # 更新节点状态为运行中
            await self._update_node_execution(node_execution_id, "running")

            # 根据节点类型执行
            if node_type == "and":
                result = await self._execute_and_node(node, config, state, node_execution_id, all_edges)
            elif node_type == "or":
                result = await self._execute_or_node(node, config, state, node_execution_id, all_edges)

            # 更新节点状态
            await self._update_node_execution(
                node_execution_id,
                result.get("status", "success"),
                output=result.get("output")
            )

            # 记录节点完成
            await self._add_node_log(node_execution_id, f"节点执行成功: {result.get('output', '')}", "success")

            # 更新状态
            state["outputs"][node_id] = result
            logger.info(f"节点执行完成: {node_id}, 状态: {result.get('status')}, 结果: {result}")

            # 执行后续节点
            await self._execute_next_nodes(execution_id, node_id, result.get("status", "success"),
                                           state, all_nodes, all_edges, node_execution_id)
            return

        # 创建节点执行记录
        node_execution_id = await self._create_node_execution(
            execution_id, node_id, node_name, node_type
        )

        # 获取前置节点和后置节点
        prev_nodes = []
        next_nodes = []
        for edge in all_edges:
            if edge.get("target") == node_id:
                prev_nodes.append(edge.get("source"))
            elif edge.get("source") == node_id:
                next_nodes.append(edge.get("target"))

        # 记录节点开始执行
        await self._add_node_log(node_execution_id, f"节点开始执行: {node_name} ({node_type})", "info")
        await self._add_node_log(node_execution_id, f"前置节点: {', '.join(prev_nodes) if prev_nodes else '无'}", "info")
        await self._add_node_log(node_execution_id, f"后置节点: {', '.join(next_nodes) if next_nodes else '无'}", "info")

        # 更新节点状态为运行中
        await self._update_node_execution(node_execution_id, "running")

        try:
            # 根据节点类型执行
            if node_type == "task":
                result = await self._execute_task_node(node, config, state)
            elif node_type == "condition":
                result = await self._execute_condition_node(node, config, state)
            elif node_type == "wait":
                result = await self._execute_wait_node(node, config, state)
            elif node_type == "notification":
                result = await self._execute_notification_node(node, config, state)
            else:
                result = {"status": "success", "output": f"未知节点类型: {node_type}"}

            # 更新节点状态
            await self._update_node_execution(
                node_execution_id,
                result.get("status", "success"),
                output=result.get("output"),
                error=result.get("error")
            )

            # 记录节点完成
            if result.get("status") == "success":
                await self._add_node_log(node_execution_id, f"节点执行成功: {result.get('output', '')}", "success")
            else:
                await self._add_node_log(node_execution_id, f"节点执行失败: {result.get('error', '')}", "failed")

            # 更新状态
            state["outputs"][node_id] = result
            logger.info(f"节点执行完成: {node_id}, 状态: {result.get('status')}, 结果: {result}")

            # 执行后续节点
            await self._execute_next_nodes(execution_id, node_id, result.get("status", "success"),
                                           state, all_nodes, all_edges)

        except Exception as e:
            logger.error(f"节点执行失败: {node_name}, error: {e}")
            await self._update_node_execution(node_execution_id, "failed", error=str(e))
            await self._add_node_log(node_execution_id, f"节点执行异常: {str(e)}", "error")
            state["outputs"][node_id] = {"status": "failed", "error": str(e)}
            logger.info(f"节点执行异常: {node_id}, 状态: failed, 错误: {str(e)}")

    async def _execute_task_node(self, node: Dict, config: Dict, state: Dict) -> Dict:
        """执行任务节点"""
        job_id = config.get("job_id")
        job_type = config.get("job_type", "cron")  # 默认为 cron 任务
        node_id = node.get("id")
        if not job_id:
            return {"status": "failed", "error": "未配置任务ID"}

        try:
            # 获取输入参数和输出参数
            inputs = state.get("inputs", {})
            outputs = state.get("outputs", {})

            logger.info(f"执行任务节点: {node_id}, job_id: {job_id}, job_type: {job_type}")
            logger.info(f"任务节点输入参数: {inputs}")
            logger.info(f"任务节点输出参数: {outputs}")

            if job_type == "cron":
                # 执行 cron 任务
                from app.modules.cron.services import execute_job
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: execute_job(self.engine, int(job_id), "workflow", inputs, outputs)
                )
            elif job_type == "acme":
                # 执行 acme 证书申请任务
                from app.modules.acme.services import ApplicationService
                acme_service = ApplicationService(self.engine)
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: acme_service.execute(int(job_id), "workflow")
                )
            else:
                return {"status": "failed", "error": f"不支持的任务类型: {job_type}"}

            logger.info(f"任务节点执行结果: {node_id}, 结果: {result}")

            return {
                "status": "success" if result.get("status") == "success" else "failed",
                "output": result.get("output", ""),
                "error": result.get("error", "")
            }
        except Exception as e:
            logger.error(f"任务节点执行异常: {node_id}, 错误: {e}")
            return {"status": "failed", "error": str(e)}

    async def _execute_condition_node(self, node: Dict, config: Dict, state: Dict) -> Dict:
        """执行条件节点"""
        expression = config.get("expression", "True")

        result = WorkflowVariableResolver.evaluate_condition(expression, state)

        logger.info(f"条件节点执行: node_id={node.get('id')}, expression={expression}, result={result}, result_type={type(result)}")

        return {
            "status": "success",
            "output": json.dumps({"result": result, "expression": expression}),
            "condition_result": result
        }

    async def _execute_and_node(self, node: Dict, config: Dict, state: Dict, node_execution_id: int = None, all_edges: list = None) -> Dict:
        """执行 AND 节点"""
        node_id = node.get("id")

        # AND 节点只是一个控制节点，不执行任何操作
        # 它的作用是等待所有前置节点完成
        logger.info(f"AND 节点执行: node_id={node_id}")

        if node_execution_id:
            # 记录 AND 节点的执行逻辑
            await self._add_node_log(node_execution_id, f"AND 节点等待所有前置节点完成", "info")

        return {
            "status": "success",
            "output": "AND 节点执行完成"
        }

    async def _execute_or_node(self, node: Dict, config: Dict, state: Dict, node_execution_id: int = None, all_edges: list = None) -> Dict:
        """执行 OR 节点"""
        node_id = node.get("id")

        # OR 节点只是一个控制节点，不执行任何操作
        # 它的作用是任一前置节点完成即执行
        logger.info(f"OR 节点执行: node_id={node_id}")

        if node_execution_id:
            # 记录 OR 节点的执行逻辑
            await self._add_node_log(node_execution_id, f"OR 节点任一前置节点完成即执行", "info")

        return {
            "status": "success",
            "output": "OR 节点执行完成"
        }

    async def _execute_wait_node(self, node: Dict, config: Dict, state: Dict) -> Dict:
        """执行等待节点"""
        seconds = config.get("seconds", 5)

        # 解析变量
        if isinstance(seconds, str):
            seconds = WorkflowVariableResolver.resolve(seconds, state)
            try:
                seconds = int(seconds)
            except (ValueError, TypeError):
                seconds = 5

        await asyncio.sleep(seconds)

        return {"status": "success", "output": f"等待 {seconds} 秒完成"}

    async def _execute_notification_node(self, node: Dict, config: Dict, state: Dict) -> Dict:
        """执行通知节点"""
        title = config.get("title", "工作流通知")
        content = config.get("content", "")

        # 解析变量
        resolved_title = WorkflowVariableResolver.resolve(title, state)
        resolved_content = WorkflowVariableResolver.resolve(content, state)

        try:
            # 调用通知模块
            from app.modules.notify.handler.manager import notification_manager
            await notification_manager.send_broadcast(
                content=f"【{resolved_title}】\n{resolved_content}"
            )

            return {"status": "success", "output": "通知发送成功"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def _execute_next_nodes(self, execution_id: int, current_node_id: str,
                                   status: str, state: Dict,
                                   all_nodes: list, all_edges: list,
                                   current_node_execution_id: int = None):
        """执行后续节点

        Args:
            execution_id: 执行记录ID
            current_node_id: 当前节点ID
            status: 当前节点状态
            state: 当前状态
            all_nodes: 所有节点
            all_edges: 所有边
            current_node_execution_id: 当前节点执行记录ID（用于记录日志）
        """
        # 找到匹配条件的出边
        next_node_ids = []
        for edge in all_edges:
            if edge.get("source") == current_node_id:
                edge_condition = edge.get("condition", "always")

                # 获取当前节点的输出
                current_output = state["outputs"].get(current_node_id, {})

                # 判断是否匹配
                match = False
                if edge_condition == "always":
                    # 总是执行（适用于非条件节点）
                    match = True
                    logger.info(f"连线条件: {current_node_id} -> {edge.get('target')}, condition=always, match={match}")
                elif edge_condition == "true":
                    # 条件为真时执行
                    condition_result = current_output.get("condition_result") if isinstance(current_output, dict) else None
                    match = condition_result is True
                    logger.info(f"连线条件: {current_node_id} -> {edge.get('target')}, condition=true, condition_result={condition_result}, match={match}")
                elif edge_condition == "false":
                    # 条件为假时执行
                    condition_result = current_output.get("condition_result") if isinstance(current_output, dict) else None
                    match = condition_result is False
                    logger.info(f"连线条件: {current_node_id} -> {edge.get('target')}, condition=false, condition_result={condition_result}, match={match}")
                elif edge_condition == "success":
                    # 节点成功时执行（适用于任务节点）
                    match = status == "success"
                    logger.info(f"连线条件: {current_node_id} -> {edge.get('target')}, condition=success, status={status}, match={match}")
                elif edge_condition == "failed":
                    # 节点失败时执行
                    match = status == "failed"
                    logger.info(f"连线条件: {current_node_id} -> {edge.get('target')}, condition=failed, status={status}, match={match}")

                if match:
                    target = edge.get("target")
                    if target and target not in next_node_ids:
                        next_node_ids.append(target)
                        logger.info(f"执行后续节点: {target}")

                        # 记录路由日志
                        if current_node_execution_id:
                            # 获取目标节点的后置节点
                            target_next_nodes = []
                            for e in all_edges:
                                if e.get("source") == target:
                                    target_next_nodes.append(e.get("target"))

                            await self._add_node_log(
                                current_node_execution_id,
                                f"路由到节点: {target} (条件: {edge_condition})",
                                "route"
                            )
                            await self._add_node_log(
                                current_node_execution_id,
                                f"目标节点后置节点: {', '.join(target_next_nodes) if target_next_nodes else '无'}",
                                "route"
                            )

        # 检查所有前置节点是否都已完成
        node_map = {n.get("id"): n for n in all_nodes}
        for next_node_id in next_node_ids[:]:
            next_node = node_map.get(next_node_id)
            if next_node:
                node_type = next_node.get("type", "task")

                # AND 节点：等待所有前置节点完成
                if node_type == "and":
                    if not await self._check_prerequisites_completed(next_node_id, state, all_edges):
                        logger.info(f"AND 节点 {next_node_id} 的前置节点未完成，跳过执行")
                        next_node_ids.remove(next_node_id)
                # OR 节点：任一前置节点完成即执行
                elif node_type == "or":
                    logger.info(f"OR 节点 {next_node_id} 任一前置节点完成即执行")
                # 其他节点：任一前置节点完成即执行（默认行为）
                else:
                    logger.info(f"节点 {next_node_id} 任一前置节点完成即执行")

        # 执行后续节点（并行执行）
        tasks = []
        for next_node_id in next_node_ids:
            next_node = node_map.get(next_node_id)
            if next_node:
                # 创建异步任务，不立即 await
                task = asyncio.create_task(
                    self._execute_node(execution_id, next_node, state, all_nodes, all_edges)
                )
                tasks.append(task)

        # 等待所有任务完成
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _check_prerequisites_completed(self, node_id: str, state: Dict, all_edges: list) -> bool:
        """检查节点的前置节点是否都已完成"""
        # 找到所有入边（前置节点）
        prerequisite_ids = []
        for edge in all_edges:
            if edge.get("target") == node_id:
                prerequisite_ids.append(edge.get("source"))

        # 检查所有前置节点是否都已完成
        for prereq_id in prerequisite_ids:
            if prereq_id not in state["outputs"]:
                logger.info(f"前置节点 {prereq_id} 还未完成")
                return False

            # 检查前置节点的执行状态是否为 success
            prereq_output = state["outputs"].get(prereq_id, {})
            prereq_status = prereq_output.get("status") if isinstance(prereq_output, dict) else None
            if prereq_status != "success":
                logger.info(f"前置节点 {prereq_id} 状态为 {prereq_status}，不是 success，等待完成")
                return False

        logger.info(f"节点 {node_id} 的所有前置节点都已完成: {prerequisite_ids}")
        return True

    def _find_start_nodes(self, nodes: list, edges: list) -> list:
        """找到起始节点（没有入边的节点）"""
        target_ids = {e.get("target") for e in edges}
        start_nodes = [n for n in nodes if n.get("id") not in target_ids]
        return start_nodes if start_nodes else (nodes[:1] if nodes else [])

    # ========== 数据库操作 ==========

    async def _get_workflow(self, workflow_id: str) -> Optional[Dict]:
        """获取工作流"""
        query = select(workflows_table).where(workflows_table.c.workflow_id == workflow_id)
        with self.engine.connect() as conn:
            result = conn.execute(query)
            row = result.first()
            return dict(row._mapping) if row else None

    async def _get_execution(self, execution_id: int) -> Optional[Dict]:
        """获取执行记录"""
        query = select(workflow_executions_table).where(
            workflow_executions_table.c.id == execution_id
        )
        with self.engine.connect() as conn:
            result = conn.execute(query)
            row = result.first()
            return dict(row._mapping) if row else None

    async def _update_execution(self, execution_id: int, status: str, error: str = None):
        """更新执行记录"""
        now = datetime.now()
        query = (
            update(workflow_executions_table)
            .where(workflow_executions_table.c.id == execution_id)
            .values(
                status=status,
                end_time=now if status in ["success", "failed", "cancelled"] else None,
                error=error
            )
        )
        with self.engine.connect() as conn:
            conn.execute(query)
            conn.commit()

    async def _create_node_execution(self, execution_id: int, node_id: str,
                                      node_name: str, node_type: str) -> int:
        """创建节点执行记录"""
        now = datetime.now()
        query = workflow_node_executions_table.insert().values(
            execution_id=execution_id,
            node_id=node_id,
            node_name=node_name,
            node_type=node_type,
            status="pending",
            start_time=now,
            created_at=now
        )
        with self.engine.connect() as conn:
            result = conn.execute(query)
            conn.commit()
            return result.inserted_primary_key[0]

    async def _update_node_execution(self, node_execution_id: int, status: str,
                                      output: str = None, error: str = None):
        """更新节点执行记录"""
        now = datetime.now()
        query = (
            update(workflow_node_executions_table)
            .where(workflow_node_executions_table.c.id == node_execution_id)
            .values(
                status=status,
                end_time=now if status in ["success", "failed"] else None,
                output=output,
                error=error
            )
        )
        with self.engine.connect() as conn:
            conn.execute(query)
            conn.commit()

    async def _add_node_log(self, node_execution_id: int, message: str, log_type: str = "info"):
        """添加节点执行日志

        Args:
            node_execution_id: 节点执行记录ID
            message: 日志消息
            log_type: 日志类型（info/warning/error/success/failed/condition/route）
        """
        now = datetime.now()
        log_entry = {
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "message": message,
            "type": log_type
        }

        # 先获取现有的日志
        query = select(workflow_node_executions_table.c.logs).where(
            workflow_node_executions_table.c.id == node_execution_id
        )

        try:
            with self.engine.connect() as conn:
                result = conn.execute(query)
                row = result.first()
                existing_logs = list(row._mapping.get("logs", [])) if row else []

                # 添加新日志
                existing_logs.append(log_entry)

                # 更新日志
                update_query = (
                    update(workflow_node_executions_table)
                    .where(workflow_node_executions_table.c.id == node_execution_id)
                    .values(logs=existing_logs)
                )
                conn.execute(update_query)
                conn.commit()
        except Exception as e:
            logger.error(f"添加节点日志失败: {e}")



# ========== 同步执行入口 ==========

def execute_workflow_sync(engine, execution_id: int):
    """
    同步执行工作流（用于后台任务）

    Args:
        engine: 数据库引擎
        execution_id: 执行记录ID
    """
    import asyncio

    engine_obj = WorkflowEngine(engine)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(engine_obj.execute_workflow(execution_id))
    finally:
        loop.close()


__all__ = ["WorkflowEngine", "WorkflowVariableResolver", "execute_workflow_sync"]
