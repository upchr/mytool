#app/core/db/db_upgrade.py
import logging
from sqlalchemy import inspect, text
import hashlib
import json

logger = logging.getLogger(__name__)

class VersionedAutoMigrator:
    """
    带版本控制的自动迁移器（SQLAlchemy Core 兼容版）
    """

    def __init__(self, engine, metadata):
        self.engine = engine
        self.metadata = metadata
        self.inspector = inspect(engine)
        self._ensure_migrations_table()

    def _ensure_migrations_table(self):
        """确保迁移记录表存在"""
        try:
            if not self.inspector.has_table('_migrations'):
                with self.engine.connect() as conn:
                    conn.execute(text("""
                        CREATE TABLE _migrations (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            table_name VARCHAR(100) NOT NULL,
                            field_name VARCHAR(100) NOT NULL,
                            field_type VARCHAR(50),
                            applied_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
                            checksum VARCHAR(64),
                            UNIQUE(table_name, field_name)
                        )
                    """))
                    conn.commit()
                logger.info("✅ 创建迁移记录表")
        except Exception as e:
            logger.error(f"创建迁移记录表失败: {e}")

    def _get_applied_fields(self, table_name: str):
        """获取已应用的字段"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT field_name, checksum FROM _migrations WHERE table_name = :table"),
                    {"table": table_name}
                )
                return {row[0]: row[1] for row in result}
        except Exception:
            return {}

    def _record_migration(self, table_name: str,
                          field_name: str, field_type: str, checksum: str):
        """记录迁移"""
        with self.engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT OR REPLACE INTO _migrations 
                    (table_name, field_name, field_type, checksum)
                    VALUES (:table, :field, :type, :checksum)
                """),
                {
                    "table": table_name,
                    "field": field_name,
                    "type": field_type,
                    "checksum": checksum
                }
            )
            conn.commit()

    def _calculate_checksum(self, column) -> str:
        """计算字段的校验和"""
        col_info = {
            'name': column.name,
            'type': str(column.type),
            'nullable': getattr(column, 'nullable', True),  # Table.Column 可能没有 nullable
            'default': str(column.default.arg) if hasattr(column, 'default') and column.default else None
        }
        return hashlib.md5(json.dumps(col_info, sort_keys=True).encode()).hexdigest()[:8]

    def sync_table(self, table_name: str, table_obj) -> list:
        """同步单个表，返回新添加的字段"""
        # 检查表是否存在
        if not self.inspector.has_table(table_name):
            logger.info(f"📦 创建表: {table_name}")
            table_obj.create(self.engine)
            return ['__table_created__']

        # 获取现有字段
        existing_columns = [
            col['name'] for col in self.inspector.get_columns(table_name)
        ]

        # 获取已迁移的字段
        applied_fields = self._get_applied_fields(table_name)
        added_fields = []

        with self.engine.connect() as conn:
            for column in table_obj.columns:
                # 跳过主键（可选）
                # if column.primary_key:
                #     continue

                name = column.name
                # 计算当前字段的校验和
                checksum = self._calculate_checksum(column)

                # 如果字段已存在且已记录，跳过
                if name in existing_columns:
                    if name in applied_fields and applied_fields[name] == checksum:
                        continue
                    continue

                # 添加缺失的字段
                try:
                    # SQLite 兼容的字段类型
                    col_type = self._get_sqlite_compatible_type(column)

                    # SQLite 的 ALTER TABLE 不支持 DEFAULT，所以只添加字段
                    sql = f"ALTER TABLE {table_name} ADD COLUMN {name} {col_type}"

                    conn.execute(text(sql))

                    # 记录迁移
                    self._record_migration(
                        table_name, name,
                        str(column.type), checksum
                    )

                    logger.info(f"✅ 添加字段: {table_name}.{name} ({col_type})")
                    added_fields.append(name)

                except Exception as e:
                    logger.error(f"❌ 添加字段失败 {table_name}.{name}: {e}")

            conn.commit()

        # 为新字段设置默认值
        if added_fields:
            self._update_default_values(conn, table_name, table_obj, added_fields)

        return added_fields

    def _get_sqlite_compatible_type(self, column) -> str:
        """获取 SQLite 兼容的类型"""
        from sqlalchemy import types

        col_type = column.type

        if isinstance(col_type, types.Integer):
            return "INTEGER"
        elif isinstance(col_type, types.String):
            return f"VARCHAR({col_type.length})" if col_type.length else "TEXT"
        elif isinstance(col_type, types.Text):
            return "TEXT"
        elif isinstance(col_type, types.Boolean):
            return "INTEGER"  # SQLite 用 INTEGER 表示 BOOLEAN
        elif isinstance(col_type, types.DateTime):
            return "TIMESTAMP"
        elif isinstance(col_type, types.Date):
            return "DATE"
        elif isinstance(col_type, types.Float):
            return "REAL"
        else:
            return "TEXT"

    def _update_default_values(self, conn, table_name, table_obj, added_fields):
        """为新添加的字段设置默认值"""
        updates = []
        params = {}

        for field_name in added_fields:
            column = table_obj.columns[field_name]
            if hasattr(column, 'default') and column.default is not None:
                default_value = column.default.arg
                if callable(default_value):
                    if 'now' in str(default_value).lower():
                        updates.append(f"{field_name} = CURRENT_TIMESTAMP")
                    else:
                        continue
                else:
                    if isinstance(default_value, bool):
                        updates.append(f"{field_name} = :{field_name}_default")
                        params[f"{field_name}_default"] = 1 if default_value else 0
                    elif isinstance(default_value, (int, float, str)):
                        updates.append(f"{field_name} = :{field_name}_default")
                        params[f"{field_name}_default"] = default_value

        if updates:
            update_sql = f"UPDATE {table_name} SET {', '.join(updates)}"
            try:
                conn.execute(text(update_sql), params)
                conn.commit()
                logger.info(f"✅ 为表 {table_name} 的新字段设置了默认值")
            except Exception as e:
                logger.warning(f"⚠️ 设置默认值失败: {e}")

    def sync_all(self) -> dict:
        """同步所有表"""
        results = {}

        # 遍历 metadata 中的所有表
        for table_name, table_obj in self.metadata.tables.items():
            try:
                added = self.sync_table(table_name, table_obj)
                if added and added != ['__table_created__']:
                    results[table_name] = added
            except Exception as e:
                logger.error(f"同步表 {table_name} 失败: {e}")

        return results
