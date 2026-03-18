from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from .schemas import (
    TaskTemplate,
    TaskTemplateCreate,
    TaskTemplateUpdate,
    TaskTemplateDetail,
    TemplateQueryParams,
    TemplateImportRequest,
    TemplateSchema,
    TemplateScript,
    TemplateCronSuggestion,
    TemplateRating,
    TemplateRatingCreate
)
from .services import TaskTemplateService

router = APIRouter(prefix="/task-templates", tags=["任务模板"])


@router.get("", response_model=List[TaskTemplate])
async def list_templates(
    category: Optional[str] = None,
    tag: Optional[str] = None,
    difficulty: Optional[str] = None,
    is_official: Optional[bool] = None,
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """获取模板列表"""
    params = TemplateQueryParams(
        category=category,
        tag=tag,
        difficulty=difficulty,
        is_official=is_official,
        keyword=keyword,
        page=page,
        page_size=page_size
    )
    templates, total = await TaskTemplateService.list_templates(params)
    return templates


@router.get("/{template_id}", response_model=TaskTemplateDetail)
async def get_template(template_id: str):
    """获取模板详情"""
    template = await TaskTemplateService.get_template_detail(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return template


@router.post("", response_model=TaskTemplate)
async def create_template(data: TaskTemplateCreate):
    """创建模板"""
    existing = await TaskTemplateService.get_template(data.template_id)
    if existing:
        raise HTTPException(status_code=400, detail="模板ID已存在")
    return await TaskTemplateService.create_template(data)


@router.put("/{template_id}", response_model=TaskTemplate)
async def update_template(template_id: str, data: TaskTemplateUpdate):
    """更新模板"""
    template = await TaskTemplateService.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return await TaskTemplateService.update_template(template_id, data)


@router.delete("/{template_id}")
async def delete_template(template_id: str):
    """删除模板"""
    template = await TaskTemplateService.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    await TaskTemplateService.delete_template(template_id)
    return {"message": "删除成功"}


@router.post("/{template_id}/import")
async def import_template(template_id: str, data: TemplateImportRequest):
    """一键导入模板为任务"""
    import json
    import os
    from app.modules.cron import services as cron_services
    from app.modules.cron.schemas import CronJobCreateSingle
    from app.core.db.database import engine
    from app.core.utils.path_utils import path_utils

    # 获取模板详情
    template = await TaskTemplateService.get_template_detail(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 增加下载次数
    await TaskTemplateService.increment_download(template_id)

    # 确定Cron表达式
    schedule = data.schedule
    if not schedule and template.cron_suggestions:
        # 找默认的，没有就用第一个
        default_cron = next((c for c in template.cron_suggestions if c.is_default), None)
        if default_cron:
            schedule = default_cron.cron_value
        elif template.cron_suggestions:
            schedule = template.cron_suggestions[0].cron_value

    if not schedule:
        raise HTTPException(status_code=400, detail="请提供Cron表达式或选择建议")

    if not template.script:
        raise HTTPException(status_code=400, detail="模板没有脚本内容")

    # 创建模板脚本目录
    scripts_dir = path_utils.get_data_dir() / "template-scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    # 保存脚本到文件
    script_content = template.script.script_content
    script_type = template.script.script_type
    ext = "py" if script_type == "python" else "sh"
    import time
    script_filename = f"{template_id}-{int(time.time())}.{ext}"
    script_path = scripts_dir / script_filename
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_content)
    os.chmod(script_path, 0o755)

    # 构建命令：执行脚本 + 传递配置参数
    config_json = json.dumps(data.config, ensure_ascii=False)
    # 转义单引号，避免shell问题
    config_json_escaped = config_json.replace("'", "\\'")
    if script_type == "python":
        command = f"python3 '{script_path}' '{config_json_escaped}'"
    else:
        command = f"bash '{script_path}' '{config_json_escaped}'"

    # 调用cron服务创建任务
    job_data = CronJobCreateSingle(
        node_id=data.node_id,
        name=data.name or template.name,
        schedule=schedule,
        command=command,
        description=f"从模板 {template_id} 导入",
        is_active=True,
        is_notice=False,
        error_times=3
    )

    result = cron_services.create_cron_job(engine, job_data)

    return {
        "message": "导入成功",
        "job": result,
        "script_path": str(script_path)
    }


@router.post("/{template_id}/ratings", response_model=TemplateRating)
async def rate_template(template_id: str, data: TemplateRatingCreate):
    """给模板评分"""
    template = await TaskTemplateService.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    data.template_id = template_id
    return await TaskTemplateService.create_rating(data)


@router.get("/{template_id}/schema", response_model=TemplateSchema)
async def get_template_schema(template_id: str):
    """获取模板参数配置Schema"""
    schema = await TaskTemplateService.get_template_schema(template_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema不存在")
    return schema


@router.get("/{template_id}/script", response_model=TemplateScript)
async def get_template_script(template_id: str):
    """获取模板脚本"""
    script = await TaskTemplateService.get_template_script(template_id)
    if not script:
        raise HTTPException(status_code=404, detail="脚本不存在")
    return script


@router.get("/{template_id}/cron-suggestions", response_model=List[TemplateCronSuggestion])
async def get_cron_suggestions(template_id: str):
    """获取模板Cron建议"""
    return await TaskTemplateService.get_cron_suggestions(template_id)
