# backend/app/modules/note/models.py
from sqlalchemy import Table, Column, Integer, String, Text, MetaData
from app.core.db.database import metadata, engine

notes_table = Table(
    "notes",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("title", String(100), nullable=False),
    Column("content", Text),
    sqlite_autoincrement=True,
)
__all__ = ["notes_table"]
