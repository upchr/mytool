# app/modules/note/api.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from .models import *
import logging
from .ssl_repository import dnsauth_repo
from ...core.pojo.response import BaseResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ssl", tags=["ssl"])

@router.get("")
def read_ssl():
    new_id = dnsauth_repo.create({"name": "test", "description": "description"})

    notes = dnsauth_repo.get_all(order_by=desc(ssl_dns_auth_table.c.id))
    note = dnsauth_repo.get_by_id(1)
