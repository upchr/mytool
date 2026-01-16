# backend/app/modules/note/schemas.py
from typing import List

from pydantic import BaseModel

class NoteBase(BaseModel):
    title: str
    content: str | None = None

class NoteCreate(NoteBase):
    pass

class NoteRead(BaseModel):
    id: int
    title: str
    content: str

    model_config = {
        "from_attributes": True  # 替代 orm_mode=True
    }
class NoteRequest(BaseModel):
    note_ids: List[int]
