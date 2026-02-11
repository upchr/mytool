# backend/app/modules/note/schemas.py
from typing import List
from pydantic import BaseModel

class SysBase(BaseModel):
    password: str
