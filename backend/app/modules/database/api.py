from fastapi import APIRouter, HTTPException, UploadFile, Query
from fastapi.responses import FileResponse
import json
import os
import tempfile
from datetime import datetime
from sqlalchemy import MetaData, Table, select, delete
from app.core.db.database import engine, metadata, DATABASE_URL, logger
import shutil
from typing import List, Optional

from app.core.exception.exceptions import ServerException
from app.core.pojo.response import BaseResponse

router = APIRouter(prefix="/database", tags=["database"])

# 模块表映射配置
MODULE_TABLES = {
    "notes": {"label":"便签管理","tables":["notes"]},
    "nodes": {"label":"节点管理","tables":["nodes"]},
    "jobs": {"label":"任务管理","tables":["cron_jobs", "job_executions"]},
    "credentials": {"label":"凭据管理","tables":["credential_templates"]},
    "notifications": {"label":"消息通知","tables":["notification_services", "notification_settings"]},
    # 添加更多模块...
}

# 白名单表（清空时保留）
WHITELIST_TABLES = [

]

def get_tables_by_modules(modules: List[str]) -> List[str]:
    """根据模块名获取对应的表名列表"""
    tables = []
    for module in modules:
        if module in MODULE_TABLES:
            tables.extend(MODULE_TABLES[module]["tables"])
        else:
            raise HTTPException(status_code=400, detail=f"未知模块: {module}")
    return list(set(tables))  # 去重

def filter_whitelist_tables(tables: List[Table]) -> List[Table]:
    """过滤掉白名单表"""
    return [table for table in tables if table.name not in WHITELIST_TABLES]

@router.get("/models")
def models():
    result = [
        {"label": info["label"], "value": key}
        for key, info in MODULE_TABLES.items()
    ]
    return BaseResponse.success(result)

@router.get("/export")
async def export_database(
        modules: Optional[List[str]] = Query(None, description="要导出的模块列表，如: nodes,jobs")
):
    """
    导出数据库为 JSON
    - 不指定 modules: 导出所有表
    - 指定 modules: 只导出指定模块的表
    """
    try:
        reflected_metadata = MetaData()
        reflected_metadata.reflect(bind=engine)

        # 确定要导出的表
        if modules:
            target_table_names = get_tables_by_modules(modules)
            target_tables = {
                name: table for name, table in reflected_metadata.tables.items()
                if name in target_table_names
            }
        else:
            target_tables = {
                name: table for name, table in reflected_metadata.tables.items()
                if not name.startswith('sqlite_')
            }

        db_data = {}

        with engine.connect() as conn:
            for table_name, table in target_tables.items():
                result = conn.execute(select(table))
                rows = []
                for row in result:
                    row_dict = {}
                    for column in table.columns:
                        value = getattr(row, column.name)
                        if hasattr(value, 'isoformat'):
                            row_dict[column.name] = value.isoformat()
                        else:
                            row_dict[column.name] = value
                    rows.append(row_dict)

                columns = [col.name for col in table.columns]
                db_data[table_name] = {
                    "columns": columns,
                    "data": rows
                }

        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False,
            encoding='utf-8'
        )
        json.dump(db_data, temp_file, ensure_ascii=False, indent=2)
        temp_file.close()

        filename_suffix = f"_{'_'.join(modules)}" if modules else ""
        filename = f"database_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}{filename_suffix}.json"

        return FileResponse(
            temp_file.name,
            filename=filename,
            media_type="application/json"
        )

    except Exception as e:
        raise ServerException(detail=f"导出失败: {str(e)}")

@router.post("/import")
async def import_database(file: UploadFile):
    """
    导入数据库
    - 只处理上传文件中包含的表
    - 自动备份并清空这些表的数据
    - 不影响其他表
    """
    if not file.filename.endswith('.json'):
        raise ServerException(detail="只支持 JSON 文件")

    try:
        content = await file.read()
        if len(content) > 50 * 1024 * 1024:  # 50MB
            raise ServerException(detail="文件太大")
        db_data = json.loads(content.decode('utf-8'))

        # 创建备份（先关闭所有连接）
        backup_path = create_backup()

        # 关闭所有现有连接
        engine.dispose()

        # 重新创建引擎
        new_engine = engine

        # 反射目标数据库结构
        target_metadata = MetaData()
        target_metadata.reflect(bind=new_engine)

        with new_engine.begin() as conn:
            # 只处理上传文件中包含的表
            tables_to_process = []
            for table_name in db_data.keys():
                if table_name in target_metadata.tables and not table_name.startswith('sqlite_'):
                    tables_to_process.append(target_metadata.tables[table_name])

            # 清空这些表的数据（按依赖顺序）
            for table in reversed(target_metadata.sorted_tables):
                if table in tables_to_process:
                    conn.execute(delete(table))

            # 插入数据
            for table_name, table_info in db_data.items():
                if table_name not in target_metadata.tables:
                    continue

                table = target_metadata.tables[table_name]
                data = table_info["data"]

                if table_name.startswith('sqlite_'):
                    continue

                # 准备插入数据（转换日期时间）
                insert_data = []
                for row in data:
                    processed_row = {}
                    for col_name, value in row.items():
                        if col_name in table.columns:
                            column = table.columns[col_name]
                            if hasattr(column.type, 'python_type') and column.type.python_type == datetime:
                                if value is not None:
                                    processed_row[col_name] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                                else:
                                    processed_row[col_name] = None
                            else:
                                processed_row[col_name] = value
                    insert_data.append(processed_row)

                if insert_data:
                    conn.execute(table.insert(), insert_data)

        return BaseResponse.success({"backup_file": backup_path},"导入成功")

    except Exception as e:
        # 恢复备份
        try:
            restore_backup(backup_path)
        except Exception as restore_error:
            print(f"恢复备份失败: {restore_error}")
        raise ServerException(detail=f"导入失败: {str(e)}")

@router.delete("/clear")
async def clear_database_sqlalchemy(
        modules: Optional[List[str]] = Query(None, description="要清空的模块列表"),
        keep_whitelist: bool = Query(True, description="是否保留白名单表")
):
    """
    清空数据库
    - 不指定 modules: 清空所有表（可选保留白名单）
    - 指定 modules: 只清空指定模块的表
    """
    try:
        backup_path = create_backup()

        target_metadata = MetaData()
        target_metadata.reflect(bind=engine)

        with engine.begin() as conn:
            if modules:
                # 只清空指定模块的表
                target_table_names = get_tables_by_modules(modules)
                tables_to_clear = [
                    table for table in target_metadata.sorted_tables
                    if table.name in target_table_names and not table.name.startswith('sqlite_')
                ]
            else:
                # 清空所有表
                tables_to_clear = [
                    table for table in reversed(target_metadata.sorted_tables)
                    if not table.name.startswith('sqlite_')
                ]
                # 应用白名单过滤
                if keep_whitelist:
                    tables_to_clear = filter_whitelist_tables(tables_to_clear)

            # 执行清空操作
            for table in tables_to_clear:
                conn.execute(delete(table))
        message = f"已清空模块: {', '.join(modules)}" if modules else "数据库已清空"
        return BaseResponse.success({"backup_file": backup_path},message)

    except ServerException as e:
        logger.error(e.detail)
        raise e
    except Exception as e:
        logger.error(e)
        raise ServerException(detail=f"清空失败: {str(e)}")

def create_backup():
    """创建数据库备份"""

    if DATABASE_URL.startswith("sqlite:///"):
        path_part = DATABASE_URL[10:]
        if path_part.startswith("/"):
            db_path = path_part
        else:
            db_path = path_part.replace("/", "\\")
    else:
        raise ValueError("仅支持 SQLite 数据库")

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_path, backup_path)
    return backup_path

def restore_backup(backup_path):
    """恢复数据库备份"""

    if DATABASE_URL.startswith("sqlite:///"):
        path_part = DATABASE_URL[10:]
        if path_part.startswith("/"):
            db_path = path_part
        else:
            db_path = path_part.replace("/", "\\")

        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        if os.path.exists(db_path):
            os.remove(db_path)
        shutil.copy2(backup_path, db_path)
