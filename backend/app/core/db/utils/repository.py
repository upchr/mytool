# app/core/db/utils/repository.py
from sqlalchemy import Table, select, insert, update, delete
from sqlalchemy.engine import Engine
from typing import List, Dict, Any, Optional

class BaseRepository:
    """基础仓储类，封装常用数据库操作"""

    def __init__(self, engine: Engine, table: Table):
        self.engine = engine
        self.table = table

    def get_all(self, order_by=None) -> List[Dict[str, Any]]:
        stmt = select(self.table)
        if order_by is not None:
            stmt = stmt.order_by(order_by)

        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            return [dict(row) for row in result.mappings()]

    def get_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        stmt = select(self.table).where(self.table.c.id == id)
        with self.engine.connect() as conn:
            row = conn.execute(stmt).mappings().first()
            return dict(row) if row else None

    def create(self, data: Dict[str, Any]) -> int:
        stmt = insert(self.table).values(**data)
        with self.engine.begin() as conn:
            result = conn.execute(stmt)
            return result.inserted_primary_key[0]

    def update(self, id: int, data: Dict[str, Any]) -> bool:
        stmt = (
            update(self.table)
            .where(self.table.c.id == id)
            .values(**data)
        )
        with self.engine.begin() as conn:
            result = conn.execute(stmt)
            return result.rowcount > 0

    def delete(self, id: int) -> bool:
        stmt = delete(self.table).where(self.table.c.id == id)
        with self.engine.begin() as conn:
            result = conn.execute(stmt)
            return result.rowcount > 0

    def delete_many(self, ids: List[int]) -> int:
        stmt = delete(self.table).where(self.table.c.id.in_(ids))
        with self.engine.begin() as conn:
            result = conn.execute(stmt)
            return result.rowcount

# 示例
# from app.core.db.repository import BaseRepository
# from .models import notes_table
#
# class NoteRepository(BaseRepository):
#     def __init__(self, engine):
#         super().__init__(engine, notes_table)
#
#     def search_by_title(self, keyword: str):
#         stmt = select(self.table).where(
#             self.table.c.title.like(f'%{keyword}%')
#         )
#         with self.engine.connect() as conn:
#             result = conn.execute(stmt)
#             return [dict(row) for row in result.mappings()]

# 使用
# note_repo = NoteRepository(engine)
# notes = note_repo.get_all(order_by=desc(notes_table.c.id))
# note = note_repo.get_by_id(1)
# new_id = note_repo.create({"title": "test", "content": "content"})
