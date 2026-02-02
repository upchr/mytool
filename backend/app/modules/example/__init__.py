import logging

from fastapi import APIRouter

from app.core.pojo.response import BaseResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/example", tags=["example"])

@router.get("/health")
async def health_check():
    from pathlib import Path
    import os
    return BaseResponse.success(
        "服务运行正123常",{
            "cwd": os.getcwd(),
            "file": Path(__file__),
        })

@router.get("/health/{user_id}")
def get_user(user_id: int):
    if user_id%2 == 0:
        from app.core.exception.exceptions import NotFoundException
        raise NotFoundException(detail="必须偶数")
    return BaseResponse.success(data={"id": user_id, "name": "Alice"})
