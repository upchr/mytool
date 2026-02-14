# app/modules/note/services.py
from sqlalchemy import select, insert, delete, update, desc
from sqlalchemy.engine import Engine
from .models import notes_table
from .schemas import NoteCreate
from ...core.db.database import engine
from ...core.db.utils.repository import BaseRepository


class NoteRepository(BaseRepository):
    def __init__(self, engine):
        super().__init__(engine, notes_table)

    def search_by_title(self, keyword: str):
        stmt = select(self.table).where(
            self.table.c.title.like(f'%{keyword}%')
        )
        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            return [dict(row) for row in result.mappings()]
note_repo = NoteRepository(engine)

def get_by_title(title: str) -> list[dict]:
    return note_repo.search_by_title(title)


def create_note(engine: Engine, note: NoteCreate) -> dict:
    stmt = insert(notes_table).values(title=note.title, content=note.content)
    with engine.begin() as conn:
        result = conn.execute(stmt)
        note_id = result.inserted_primary_key[0]
        return {"id": note_id, "title": note.title, "content": note.content}

def get_notes(engine: Engine) -> list[dict]:
    return note_repo.get_all(order_by=desc(notes_table.c.id))
    # stmt = select(notes_table).order_by(desc(notes_table.c.id ))
    # with engine.connect() as conn:
    #     result = conn.execute(stmt)
    #     # 每行转成 dict
    #     return [dict(row) for row in result.mappings()]

def delete_note(engine: Engine, note_id: int) -> bool:
    stmt = delete(notes_table).where(notes_table.c.id == note_id)
    with engine.begin() as conn:
        result = conn.execute(stmt)
        return result.rowcount > 0  # True 表示删除成功

def update_note(engine: Engine, note_id: int, note: NoteCreate) -> dict:
    stmt = (
        update(notes_table)
        .where(notes_table.c.id == note_id)
        .values(title=note.title, content=note.content)
    )
    with engine.begin() as conn:
        result = conn.execute(stmt)
        if result.rowcount == 0:
            return None
        # 返回更新后的数据
        select_stmt = select(notes_table).where(notes_table.c.id == note_id)
        row = conn.execute(select_stmt).mappings().first()
        return dict(row)

def batch_delete_notes(engine: Engine, note_ids: list[int]):
    with engine.begin() as conn:
        stmt = delete(notes_table).where(notes_table.c.id.in_(note_ids))
        conn.execute(stmt)
