# backend/app/modules/note/api.py
from fastapi import APIRouter, Depends, HTTPException
from app.core.db.database import engine, metadata
from . import services, schemas, models

import logging

from ...core.exception.exceptions import NotFoundException, ServerException
from ...core.pojo.response import BaseResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notes", tags=["notes"])

@router.get("")
def read_notes():
    return BaseResponse.success(data=services.get_notes(engine))

@router.post("")
def create_note(note: schemas.NoteCreate):
    return BaseResponse.success(data=services.create_note(engine, note))

@router.delete("/{note_id}")
def remove_note(note_id: int):
    success = services.delete_note(engine, note_id)
    if success:
        return BaseResponse.success(data={"status": "ok", "id": note_id})
    raise NotFoundException(detail=f"便签不存在")
    # return {"status": "not found", "id": note_id}

# 在现有路由下添加
@router.put("/{note_id}")
def update_note(note_id: int, note: schemas.NoteCreate):
    updated = services.update_note(engine, note_id, note)
    if updated:
        # return updated
        return BaseResponse.success(data=updated)

    # return {"status": "not found", "id": note_id}
    raise NotFoundException(detail=f"便签不存在")

@router.post("/deleteBatch")
def batch_delete_notes(req:schemas.NoteRequest):
    if not req.note_ids:
        raise ServerException(detail="便签ID列表不能为空")

    services.batch_delete_notes(engine, req.note_ids)
    # return {"success": True, "deleted_count": success_count}
    return BaseResponse.success()
