from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import FileResponse
import json
import os
import tempfile
from datetime import datetime
from sqlalchemy import MetaData, Table, select, delete
from sqlalchemy.exc import SQLAlchemyError
from app.core.database import engine, metadata
import shutil

router = APIRouter(prefix="/database", tags=["database"])

@router.get("/export")
async def export_database():
    """导出数据库为 JSON"""
    try:
        reflected_metadata = MetaData()
        reflected_metadata.reflect(bind=engine)

        db_data = {}

        with engine.connect() as conn:
            for table_name, table in reflected_metadata.tables.items():
                if table_name.startswith('sqlite_'):
                    continue

                result = conn.execute(select(table))
                rows = []
                for row in result:
                    row_dict = {}
                    for column in table.columns:
                        value = getattr(row, column.name)
                        # 转换 datetime 对象为 ISO 格式字符串
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

        return FileResponse(
            temp_file.name,
            filename=f"database_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            media_type="application/json"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")

@router.post("/import")
async def import_database(file: UploadFile):
    """导入数据库（修复 DateTime 和 Windows 文件锁定问题）"""
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="只支持 JSON 文件")

    try:
        content = await file.read()
        if len(content) > 50 * 1024 * 1024:  # 50MB
            raise HTTPException(status_code=413, detail="文件太大")
        db_data = json.loads(content.decode('utf-8'))

        # 创建备份（先关闭所有连接）
        backup_path = create_backup()

        # 关闭所有现有连接（解决 Windows 文件锁定）
        engine.dispose()

        # 重新创建引擎
        from app.core.database import DATABASE_URL
        new_engine = engine  # 使用现有的 engine，但已 dispose

        # 反射目标数据库结构
        target_metadata = MetaData()
        target_metadata.reflect(bind=new_engine)

        with new_engine.begin() as conn:
            # 清空所有表（按依赖顺序）
            for table in reversed(target_metadata.sorted_tables):
                if table.name.startswith('sqlite_'):
                    continue
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
                            # 检查是否为 DateTime 类型
                            if hasattr(column.type, 'python_type') and column.type.python_type == datetime:
                                if value is not None:
                                    # 转换 ISO 字符串为 datetime 对象
                                    processed_row[col_name] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                                else:
                                    processed_row[col_name] = None
                            else:
                                processed_row[col_name] = value
                    insert_data.append(processed_row)

                if insert_data:
                    conn.execute(table.insert(), insert_data)

        return {"success": True, "message": "导入成功", "backup_file": backup_path}

    except Exception as e:
        # 恢复备份
        try:
            restore_backup(backup_path)
        except Exception as restore_error:
            print(f"恢复备份失败: {restore_error}")
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")

def create_backup():
    """创建数据库备份（处理 Windows 路径）"""
    from app.core.database import DATABASE_URL

    # 正确解析数据库路径
    if DATABASE_URL.startswith("sqlite:///"):
        # 处理 Windows 路径 (sqlite:///C:/path/to/db)
        path_part = DATABASE_URL[10:]  # 移除 "sqlite:///"
        if path_part.startswith("/"):  # Unix 路径
            db_path = path_part
        else:  # Windows 路径
            db_path = path_part.replace("/", "\\")
    else:
        raise ValueError("仅支持 SQLite 数据库")

    # 确保路径存在
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_path, backup_path)
    return backup_path

def restore_backup(backup_path):
    """恢复数据库备份"""
    from app.core.database import DATABASE_URL

    if DATABASE_URL.startswith("sqlite:///"):
        path_part = DATABASE_URL[10:]
        if path_part.startswith("/"):
            db_path = path_part
        else:
            db_path = path_part.replace("/", "\\")

        # 确保目标目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # 强制删除现有文件（Windows 需要）
        if os.path.exists(db_path):
            os.remove(db_path)

        shutil.copy2(backup_path, db_path)

@router.delete("/clear")
async def clear_database_sqlalchemy():
    try:
        backup_path = create_backup()

        target_metadata = MetaData()
        target_metadata.reflect(bind=engine)

        with engine.begin() as conn:
            # 按依赖顺序删除数据（先删除外键依赖的表）
            for table in reversed(target_metadata.sorted_tables):
                if table.name.startswith('sqlite_'):
                    continue
                conn.execute(delete(table))
        return {
            "success": True,
            "message": "数据库已清空",
            "backup_file": backup_path
        }

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"清空失败: {str(e)}")

