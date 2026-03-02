import logging

from fastapi import APIRouter, Request

from app.core.pojo.response import BaseResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/example", tags=["example"])

@router.get("/health")
async def health_check():
    from pathlib import Path
    import os
    return BaseResponse.success(
        {
            "cwd": os.getcwd(),
            "file": Path(__file__),
        },"服务运行正123常")

@router.get("/health/{user_id}")
def get_user(user_id: int):
    if user_id%2 == 0:
        from app.core.exception.exceptions import NotFoundException
        raise NotFoundException(detail=f"点击次数为偶数报错：第{user_id}次")
    return BaseResponse.success(data={"id": user_id, "name": "Alice"})

@router.get("/getip")
def getip(request: Request):  # ← 注意：参数名是 request，类型是 Request
    xff = request.headers.get("X-Forwarded-For", "Not set")
    real_ip = request.headers.get("X-Real-IP", "Not set")
    client_host = request.client.host if request.client else "Unknown"
    return {
        "X-Forwarded-For": xff,
        "X-Real-IP": real_ip,
        "TCP Source IP": client_host
    }
