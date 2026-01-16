# backend/app/modules/note/api.py
from fastapi import APIRouter, Depends, HTTPException
from . import services, schemas
from app.core.database import engine, metadata
from .schemas import NoteRequest

router = APIRouter(prefix="/notes", tags=["notes"])

metadata.create_all(engine)

@router.get("", response_model=list[schemas.NoteRead])
def read_notes():
    return services.get_notes(engine)

@router.post("", response_model=schemas.NoteRead)
def create_note(note: schemas.NoteCreate):
    return services.create_note(engine, note)

@router.delete("/{note_id}", response_model=dict)
def remove_note(note_id: int):
    success = services.delete_note(engine, note_id)
    if success:
        return {"status": "ok", "id": note_id}
    return {"status": "not found", "id": note_id}

# 在现有路由下添加
@router.put("/{note_id}", response_model=dict)
def update_note(note_id: int, note: schemas.NoteCreate):
    updated = services.update_note(engine, note_id, note)
    if updated:
        return updated
    return {"status": "not found", "id": note_id}

@router.post("/deleteBatch")
def batch_delete_notes(req:NoteRequest):
    if not req.note_ids:
        raise HTTPException(status_code=400, detail="便签ID列表不能为空")

    success_count = services.batch_delete_notes(engine, req.note_ids)
    return {"success": True, "deleted_count": success_count}
