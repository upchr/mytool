# backend/app/modules/note/models.py
from sqlalchemy import Table, Column, Integer, String, Text, MetaData
from app.core.db.database import metadata, engine

notes_table = Table(
    "notes",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("title", String(100), nullable=False),
    Column("content", Text),
)
if __name__ != "__main__":
    metadata.create_all(engine, tables=[
        notes_table,
    ])
