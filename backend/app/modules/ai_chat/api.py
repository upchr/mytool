from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List
from datetime import datetime
from sqlalchemy import select, delete, update
from . import services, schemas, models
from app.core.pojo.response import BaseResponse
from app.core.db.database import get_engine
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


# 对话管理接口

@router.get("/conversations")
async def get_conversations():
    """
    获取对话列表

    Returns:
        对话列表，按更新时间倒序排列
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            stmt = select(models.conversations_table).order_by(
                models.conversations_table.c.updated_at.desc()
            )
            result = conn.execute(stmt)
            conversations = []
            for row in result:
                conv = {
                    "id": row.id,
                    "title": row.title,
                    "user_id": row.user_id,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                    "messages": []
                }
                conversations.append(conv)
            return BaseResponse.success(data=conversations)
    except Exception as e:
        logger.error(f"获取对话列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取对话列表失败")


@router.post("/conversations")
async def create_conversation(request: schemas.ConversationCreate):
    """
    创建新对话

    Args:
        request: 对话创建请求

    Returns:
        创建的对话信息
    """
    try:
        engine = get_engine()
        now = datetime.utcnow()
        with engine.connect() as conn:
            stmt = models.conversations_table.insert().values(
                title=request.title,
                user_id=None,
                created_at=now,
                updated_at=now
            )
            result = conn.execute(stmt)
            conn.commit()
            conversation_id = result.inserted_primary_key[0]
            
            return BaseResponse.success(data={
                "id": conversation_id,
                "title": request.title,
                "user_id": None,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "messages": []
            })
    except Exception as e:
        logger.error(f"创建对话失败: {e}")
        raise HTTPException(status_code=500, detail="创建对话失败")


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: int):
    """
    获取指定对话的详细信息

    Args:
        conversation_id: 对话ID

    Returns:
        对话详细信息，包含消息列表
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            # 获取对话
            conv_stmt = select(models.conversations_table).where(
                models.conversations_table.c.id == conversation_id
            )
            conv_result = conn.execute(conv_stmt).first()
            
            if not conv_result:
                raise HTTPException(status_code=404, detail="对话不存在")
            
            # 获取消息
            msg_stmt = select(models.messages_table).where(
                models.messages_table.c.conversation_id == conversation_id
            ).order_by(models.messages_table.c.created_at)
            msg_result = conn.execute(msg_stmt)
            
            messages = []
            for msg_row in msg_result:
                messages.append({
                    "id": msg_row.id,
                    "conversation_id": msg_row.conversation_id,
                    "role": msg_row.role,
                    "content": msg_row.content,
                    "created_at": msg_row.created_at.isoformat() if msg_row.created_at else None
                })
            
            return BaseResponse.success(data={
                "id": conv_result.id,
                "title": conv_result.title,
                "user_id": conv_result.user_id,
                "created_at": conv_result.created_at.isoformat() if conv_result.created_at else None,
                "updated_at": conv_result.updated_at.isoformat() if conv_result.updated_at else None,
                "messages": messages
            })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取对话失败: {e}")
        raise HTTPException(status_code=500, detail="获取对话失败")


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int):
    """
    删除对话及其所有消息

    Args:
        conversation_id: 对话ID

    Returns:
        删除结果
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            # 先检查对话是否存在
            conv_stmt = select(models.conversations_table).where(
                models.conversations_table.c.id == conversation_id
            )
            conv_result = conn.execute(conv_stmt).first()
            
            if not conv_result:
                raise HTTPException(status_code=404, detail="对话不存在")
            
            # 删除消息（级联删除会自动处理）
            delete_msg_stmt = delete(models.messages_table).where(
                models.messages_table.c.conversation_id == conversation_id
            )
            conn.execute(delete_msg_stmt)
            
            # 删除对话
            delete_conv_stmt = delete(models.conversations_table).where(
                models.conversations_table.c.id == conversation_id
            )
            conn.execute(delete_conv_stmt)
            
            conn.commit()
            return BaseResponse.success(data={"message": "对话已删除"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除对话失败: {e}")
        raise HTTPException(status_code=500, detail="删除对话失败")


@router.post("/conversations/{conversation_id}/messages")
async def create_message(conversation_id: int, request: schemas.MessageCreate):
    """
    在指定对话中添加消息

    Args:
        conversation_id: 对话ID
        request: 消息创建请求

    Returns:
        创建的消息信息
    """
    try:
        engine = get_engine()
        now = datetime.utcnow()
        with engine.connect() as conn:
            # 检查对话是否存在
            conv_stmt = select(models.conversations_table).where(
                models.conversations_table.c.id == conversation_id
            )
            conv_result = conn.execute(conv_stmt).first()
            
            if not conv_result:
                raise HTTPException(status_code=404, detail="对话不存在")
            
            # 插入消息
            stmt = models.messages_table.insert().values(
                conversation_id=conversation_id,
                role=request.role,
                content=request.content,
                created_at=now
            )
            result = conn.execute(stmt)
            
            # 更新对话的更新时间
            update_conv_stmt = update(models.conversations_table).where(
                models.conversations_table.c.id == conversation_id
            ).values(updated_at=now)
            conn.execute(update_conv_stmt)
            
            conn.commit()
            message_id = result.inserted_primary_key[0]
            
            return BaseResponse.success(data={
                "id": message_id,
                "conversation_id": conversation_id,
                "role": request.role,
                "content": request.content,
                "created_at": now.isoformat()
            })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建消息失败: {e}")
        raise HTTPException(status_code=500, detail="创建消息失败")