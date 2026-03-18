from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select, update, delete, and_, or_, func
from app.core.db.database import database, engine
from .models import (
    task_templates_table,
    template_schemas_table,
    template_scripts_table,
    template_cron_suggestions_table,
    template_ratings_table
)
from .schemas import (
    TaskTemplateCreate,
    TaskTemplateUpdate,
    TemplateSchemaCreate,
    TemplateScriptCreate,
    TemplateCronSuggestionCreate,
    TemplateRatingCreate,
    TemplateQueryParams,
    TaskTemplateDetail,
    TemplateApplyRequest
)


class TaskTemplateService:
    """任务模板服务"""

    @staticmethod
    async def get_template(template_id: str) -> Optional[Dict]:
        """获取单个模板"""
        query = select(task_templates_table).where(task_templates_table.c.template_id == template_id)
        return await database.fetch_one(query)

    @staticmethod
    async def get_template_detail(template_id: str) -> Optional[TaskTemplateDetail]:
        """获取模板详情（包含schema、script、cron建议）"""
        # 获取模板基础信息
        template = await TaskTemplateService.get_template(template_id)
        if not template:
            return None

        # 获取schema
        schema_query = select(template_schemas_table).where(template_schemas_table.c.template_id == template_id)
        schema = await database.fetch_one(schema_query)

        # 获取script
        script_query = select(template_scripts_table).where(template_scripts_table.c.template_id == template_id)
        script = await database.fetch_one(script_query)

        # 获取cron建议
        cron_query = (
            select(template_cron_suggestions_table)
            .where(template_cron_suggestions_table.c.template_id == template_id)
            .order_by(template_cron_suggestions_table.c.sort_order)
        )
        cron_suggestions = await database.fetch_all(cron_query)

        return TaskTemplateDetail(
            **template,
            schema=schema,
            script=script,
            cron_suggestions=cron_suggestions
        )

    @staticmethod
    async def list_templates(params: TemplateQueryParams) -> tuple[List[Dict], int]:
        """列出模板（带分页和筛选）"""
        query = select(task_templates_table).where(task_templates_table.c.is_enabled == True)

        # 筛选条件
        if params.category:
            query = query.where(task_templates_table.c.category == params.category)
        if params.difficulty:
            query = query.where(task_templates_table.c.difficulty == params.difficulty)
        if params.is_official is not None:
            query = query.where(task_templates_table.c.is_official == params.is_official)
        if params.keyword:
            keyword = f"%{params.keyword}%"
            query = query.where(
                or_(
                    task_templates_table.c.name.like(keyword),
                    task_templates_table.c.description.like(keyword)
                )
            )
        if params.tag:
            # 简单的标签包含判断
            query = query.where(task_templates_table.c.tags.contains([params.tag]))

        # 总数
        count_query = select(func.count()).select_from(query.subquery())
        total = await database.fetch_val(count_query)

        # 分页
        offset = (params.page - 1) * params.page_size
        query = query.order_by(task_templates_table.c.download_count.desc()).offset(offset).limit(params.page_size)

        templates = await database.fetch_all(query)
        return templates, total

    @staticmethod
    async def create_template(data: TaskTemplateCreate) -> Dict:
        """创建模板"""
        now = datetime.utcnow()
        query = task_templates_table.insert().values(
            **data.model_dump(),
            created_at=now,
            updated_at=now
        )
        record_id = await database.execute(query)

        # 获取创建后的记录
        return await TaskTemplateService.get_template(data.template_id)

    @staticmethod
    async def update_template(template_id: str, data: TaskTemplateUpdate) -> Optional[Dict]:
        """更新模板"""
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return await TaskTemplateService.get_template(template_id)

        update_data["updated_at"] = datetime.utcnow()
        query = (
            update(task_templates_table)
            .where(task_templates_table.c.template_id == template_id)
            .values(**update_data)
        )
        await database.execute(query)
        return await TaskTemplateService.get_template(template_id)

    @staticmethod
    async def delete_template(template_id: str) -> bool:
        """删除模板（软删除，禁用）"""
        query = (
            update(task_templates_table)
            .where(task_templates_table.c.template_id == template_id)
            .values(is_enabled=False, updated_at=datetime.utcnow())
        )
        await database.execute(query)
        return True

    @staticmethod
    async def increment_download(template_id: str) -> None:
        """增加下载次数"""
        query = (
            update(task_templates_table)
            .where(task_templates_table.c.template_id == template_id)
            .values(
                download_count=task_templates_table.c.download_count + 1,
                updated_at=datetime.utcnow()
            )
        )
        await database.execute(query)

    # ========== Schema 相关 ==========

    @staticmethod
    async def create_template_schema(data: TemplateSchemaCreate) -> Dict:
        """创建模板Schema"""
        now = datetime.utcnow()
        query = template_schemas_table.insert().values(
            **data.model_dump(),
            created_at=now,
            updated_at=now
        )
        record_id = await database.execute(query)

        # 获取并返回
        get_query = select(template_schemas_table).where(template_schemas_table.c.id == record_id)
        return await database.fetch_one(get_query)

    @staticmethod
    async def get_template_schema(template_id: str) -> Optional[Dict]:
        """获取模板Schema"""
        query = select(template_schemas_table).where(template_schemas_table.c.template_id == template_id)
        return await database.fetch_one(query)

    # ========== Script 相关 ==========

    @staticmethod
    async def create_template_script(data: TemplateScriptCreate) -> Dict:
        """创建模板脚本"""
        now = datetime.utcnow()
        query = template_scripts_table.insert().values(
            **data.model_dump(),
            created_at=now,
            updated_at=now
        )
        record_id = await database.execute(query)

        get_query = select(template_scripts_table).where(template_scripts_table.c.id == record_id)
        return await database.fetch_one(get_query)

    @staticmethod
    async def get_template_script(template_id: str) -> Optional[Dict]:
        """获取模板脚本"""
        query = select(template_scripts_table).where(template_scripts_table.c.template_id == template_id)
        return await database.fetch_one(query)

    # ========== Cron建议 相关 ==========

    @staticmethod
    async def create_cron_suggestion(data: TemplateCronSuggestionCreate) -> Dict:
        """创建Cron建议"""
        query = template_cron_suggestions_table.insert().values(**data.model_dump())
        record_id = await database.execute(query)

        get_query = select(template_cron_suggestions_table).where(template_cron_suggestions_table.c.id == record_id)
        return await database.fetch_one(get_query)

    @staticmethod
    async def get_cron_suggestions(template_id: str) -> List[Dict]:
        """获取模板的Cron建议"""
        query = (
            select(template_cron_suggestions_table)
            .where(template_cron_suggestions_table.c.template_id == template_id)
            .order_by(template_cron_suggestions_table.c.sort_order)
        )
        return await database.fetch_all(query)

    # ========== 评分 相关 ==========

    @staticmethod
    async def create_rating(data: TemplateRatingCreate) -> Dict:
        """创建评分"""
        query = template_ratings_table.insert().values(**data.model_dump())
        record_id = await database.execute(query)

        # 更新模板的平均评分
        await TaskTemplateService._update_template_rating(data.template_id)

        get_query = select(template_ratings_table).where(template_ratings_table.c.id == record_id)
        return await database.fetch_one(get_query)

    @staticmethod
    async def _update_template_rating(template_id: str) -> None:
        """更新模板的平均评分"""
        # 计算平均评分和次数
        query = select(
            func.count(template_ratings_table.c.id).label("count"),
            func.avg(template_ratings_table.c.rating).label("avg")
        ).where(template_ratings_table.c.template_id == template_id)
        result = await database.fetch_one(query)

        if result and result["count"] > 0:
            update_query = (
                update(task_templates_table)
                .where(task_templates_table.c.template_id == template_id)
                .values(
                    rating_count=result["count"],
                    rating_avg=int(result["avg"]),
                    updated_at=datetime.utcnow()
                )
            )
            await database.execute(update_query)
    
    @staticmethod
    async def apply_template(template_id: str, request: TemplateApplyRequest) -> Dict[str, Any]:
        """一键应用模板 - 创建 cron 任务"""
        from app.modules.cron.services import create_cron_job
        from app.modules.cron.schemas import CronJobCreate
        
        # 获取模板详情
        template_detail = await TaskTemplateService.get_template_detail(template_id)
        if not template_detail:
            raise ValueError(f"模板不存在: {template_id}")
        
        # 增加下载次数
        await TaskTemplateService.increment_download(template_id)
        
        # 处理模板变量替换
        script = template_detail.script
        command = script.get("script_content", "") if script else ""
        
        # 替换变量: {{variable_name}}
        variables = request.variables or {}
        for var_name, var_value in variables.items():
            command = command.replace(f"{{{{{var_name}}}}}", str(var_value))
        
        # 使用请求提供的 schedule 或模板默认
        schedule = request.schedule
        if not schedule and template_detail.cron_suggestions:
            schedule = template_detail.cron_suggestions[0].get("cron_expression", "0 0 * * *")
        if not schedule:
            schedule = "0 0 * * *"
        
        # 创建 cron 任务
        cron_job_data = CronJobCreate(
            name=request.name or f"{template_detail.name} - 从模板创建",
            description=request.description or template_detail.description,
            node_id=request.node_id,
            command=command,
            schedule=schedule,
            is_active=request.is_active if request.is_active is not None else False,
            error_times=request.error_times or 3,
            consecutive_failures=0
        )
        
        import asyncio
        loop = asyncio.get_running_loop()
        
        result = await loop.run_in_executor(
            None,
            lambda: create_cron_job(engine, cron_job_data)
        )
        
        return {
            "message": "模板应用成功",
            "template_id": template_id,
            "cron_job": result
        }


# ========== 初始化内置模板 ==========

async def init_builtin_templates():
    """初始化内置模板（第一期）"""
    from .builtin_templates import get_builtin_templates

    for template_data in get_builtin_templates():
        # 检查是否已存在
        existing = await TaskTemplateService.get_template(template_data["template"].template_id)
        if existing:
            continue  # 已存在，跳过

        # 创建模板
        await TaskTemplateService.create_template(template_data["template"])

        # 创建Schema
        if "schema" in template_data:
            await TaskTemplateService.create_template_schema(template_data["schema"])

        # 创建Script
        if "script" in template_data:
            await TaskTemplateService.create_template_script(template_data["script"])

        # 创建Cron建议
        if "cron_suggestions" in template_data:
            for cron in template_data["cron_suggestions"]:
                await TaskTemplateService.create_cron_suggestion(cron)
