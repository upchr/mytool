# backend/app/modules/note/services.py
from sqlalchemy import select, insert,delete
from sqlalchemy.engine import Engine
from .models import notes_table
from .schemas import NoteCreate

def create_note(engine: Engine, note: NoteCreate) -> dict:
    stmt = insert(notes_table).values(title=note.title, content=note.content)
    with engine.begin() as conn:
        result = conn.execute(stmt)
        note_id = result.inserted_primary_key[0]
        return {"id": note_id, "title": note.title, "content": note.content}

def get_notes(engine: Engine) -> list[dict]:
    stmt = select(notes_table)
    with engine.connect() as conn:
        result = conn.execute(stmt)
        # 每行转成 dict
        return [dict(row) for row in result.mappings()]

def delete_note(engine: Engine, note_id: int) -> bool:
    stmt = delete(notes_table).where(notes_table.c.id == note_id)
    with engine.begin() as conn:
        result = conn.execute(stmt)
        return result.rowcount > 0  # True 表示删除成功
