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
