from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from . import services, schemas
from app.core.pojo.response import BaseResponse
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai-chat", tags=["ai-chat"])


@router.post("/chat")
async def chat(request: schemas.ChatRequest):
    """
    AI 聊天接口
    
    Args:
        request: 聊天请求，包含用户消息和历史消息
        
    Returns:
        AI 响应
    """
    try:
        # 调用 AI 服务（修正为通过 services 模块访问全局实例）
        content = await services.ai_chat_service.chat(
            message=request.message,
            history=request.history,
        )

        return BaseResponse.success(
            data={
                "content": content,
                "role": "assistant",
            }
        )
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail="AI 服务暂时不可用")


@router.post("/chat/stream")
async def chat_stream(request: schemas.ChatRequest):
    """
    AI 聊天接口（流式 SSE）

    前端通过 fetch 读取 text/event-stream，逐步追加内容。
    """

    async def event_gen():
        try:
            async for delta in services.ai_chat_service.chat_stream(
                message=request.message,
                history=request.history,
            ):
                yield f"data: {json.dumps({'delta': delta}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error(f"Chat stream endpoint error: {e}")
            yield f"data: {json.dumps({'error': 'AI 服务暂时不可用'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")


@router.get("/config")
async def get_config():
    """
    获取 AI 配置信息
    
    Returns:
        当前 AI 配置状态
    """
    is_configured = bool(services.ai_chat_service.api_key)
    return BaseResponse.success(
        data={
            "configured": is_configured,
            "model": services.ai_chat_service.model,
            "api_base": services.ai_chat_service.api_base,
        }
    )