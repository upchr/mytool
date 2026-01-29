from fastapi import HTTPException
from sqlalchemy import select, insert, update, delete, desc
from sqlalchemy.engine import Engine

from sqlalchemy.exc import IntegrityError

from . import models, schemas
from .models import nodes_table, credential_templates_table
from .schemas import NodeCreate, CredentialTemplateCreate

from ..cron.models import cron_jobs_table
from ..cron.scheduler import scheduler


def create_node(engine: Engine, node: schemas.NodeCreate) -> dict:
    data = node.model_dump()
    stmt = insert(models.nodes_table).values(**data)
    with engine.begin() as conn:
        result = conn.execute(stmt)
        node_id = result.inserted_primary_key[0]
        return {"id": node_id, **data}  # ✅ 返回完整对象

def get_nodes(engine: Engine, active_only: bool) -> list[dict]:
    stmt = select(models.nodes_table).order_by(models.nodes_table.c.name )
    if active_only:
        stmt = stmt.where(models.nodes_table.c.is_active == True)
    with engine.connect() as conn:
        result = conn.execute(stmt)
        return [dict(row) for row in result.mappings()]

def get_node(engine: Engine, node_id: int) -> dict:
    stmt = select(models.nodes_table).where(models.nodes_table.c.id == node_id)
    with engine.connect() as conn:
        result = conn.execute(stmt).mappings().first()
        return dict(result) if result else None

def delete_node(engine: Engine, node_id: int) -> bool:
    stmt = delete(models.nodes_table).where(models.nodes_table.c.id == node_id)
    with engine.begin() as conn:
        result = conn.execute(stmt)
        return result.rowcount > 0

def toggle_node_status(engine: Engine, node_id: int, is_active: bool) -> bool:
    with engine.begin() as conn:
        # 1️⃣ 更新节点状态
        result = conn.execute(
            update(models.nodes_table)
            .where(models.nodes_table.c.id == node_id)
            .values(is_active=is_active)
        )
        if result.rowcount == 0:
            return False

        # 2️⃣ 查询该节点下所有任务
        jobs = conn.execute(
            select(cron_jobs_table)
            .where(cron_jobs_table.c.node_id == node_id)
        ).mappings().all()

    # 3️⃣ 同步调度器（事务外）
    for job in jobs:
        if is_active:
            # 节点恢复：只恢复原本启用的任务
            if job["is_active"]:
                scheduler.add_job(job)
        else:
            # 节点停用：全部从调度器移除
            scheduler.remove_job(job["id"], job["name"])

    return True

def update_node(engine: Engine, node_id: int, node: NodeCreate) -> dict:
    stmt = (
        update(nodes_table)
        .where(nodes_table.c.id == node_id)
        .values(**node.__dict__)  # 将NodeCreate对象转为字典
    )
    with engine.begin() as conn:
        result = conn.execute(stmt)
        if result.rowcount == 0:
            return None
        # 返回更新后的数据
        select_stmt = select(nodes_table).where(nodes_table.c.id == node_id)
        row = conn.execute(select_stmt).mappings().first()
        return dict(row)

def batch_delete_nodes(engine: Engine, node_ids: list[int]) -> int:
    """批量删除节点，返回成功删除的数量"""
    deleted_count = 0

    with engine.begin() as conn:
        for node_id in node_ids:
            try:
                # 1. 删除关联的定时任务
                conn.execute(
                    delete(cron_jobs_table)
                    .where(cron_jobs_table.c.node_id == node_id)
                )

                # 2. 删除节点
                result = conn.execute(
                    delete(models.nodes_table)
                    .where(models.nodes_table.c.id == node_id)
                )

                if result.rowcount > 0:
                    deleted_count += 1

            except Exception as e:
                print(f"删除节点 {node_id} 失败: {e}")
                # 继续处理其他节点

    return deleted_count

def create_credential_template(engine, template_data):
    table = models.credential_templates_table

    # 转为字典（兼容 Pydantic 模型）
    data = template_data if isinstance(template_data, dict) else template_data.model_dump()

    with engine.connect() as conn:
        try:
            # 插入
            stmt = insert(table).values(**data)
            result = conn.execute(stmt)
            conn.commit()

            # 获取刚插入的记录
            new_id = result.inserted_primary_key[0]
            query = select(table).where(table.c.id == new_id)
            row = conn.execute(query).fetchone()
            return row._asdict() if row else None
        except IntegrityError as e:
            conn.rollback()  # 回滚事务
            # 检查是否是名称重复
            if "UNIQUE constraint failed: credential_templates.name" in str(e) or "Duplicate entry" in str(e):
                raise HTTPException(
                    status_code=400,
                    detail="凭据模板名称已存在，请使用其他名称"
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="数据校验失败"
                )
        except Exception as e:
            conn.rollback()
            raise HTTPException(
                status_code=500,
                detail="服务器内部错误"
)

def get_credential_templates(engine):
    """
    获取所有凭据模板列表
    :param engine: SQLAlchemy 引擎
    :return: list[dict]
    """
    table = models.credential_templates_table

    with engine.connect() as conn:
        query = select(table).order_by(table.c.name,desc(table.c.id))
        result = conn.execute(query)
        return [row._asdict() for row in result.fetchall()]


def delete_credential_template(engine, template_id: int) -> bool:
    """
    删除凭据模板
    :param engine: SQLAlchemy 引擎
    :param template_id: 模板ID
    :return: 是否成功删除（bool）
    """
    table = models.credential_templates_table

    with engine.connect() as conn:
        stmt = delete(table).where(table.c.id == template_id)
        result = conn.execute(stmt)
        conn.commit()
        return result.rowcount > 0

def update_pj(engine: Engine, template_id: int, pj: CredentialTemplateCreate) -> dict:
    stmt = (
        update(credential_templates_table)
        .where(credential_templates_table.c.id == template_id)
        .values(**pj.__dict__)
    )
    with engine.begin() as conn:
        try:
            result = conn.execute(stmt)
            if result.rowcount == 0:
                return None
            # 返回更新后的数据
            select_stmt = select(credential_templates_table).where(credential_templates_table.c.id == template_id)
            row = conn.execute(select_stmt).mappings().first()
            return dict(row)
        except IntegrityError as e:
            conn.rollback()  # 回滚事务
            # 检查是否是名称重复
            if "UNIQUE constraint failed: credential_templates.name" in str(e) or "Duplicate entry" in str(e):
                raise HTTPException(
                    status_code=400,
                    detail="凭据模板名称已存在，请使用其他名称"
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="数据校验失败"
                )
        except Exception as e:
            conn.rollback()
            raise HTTPException(
                status_code=500,
                detail="服务器内部错误"
            )

