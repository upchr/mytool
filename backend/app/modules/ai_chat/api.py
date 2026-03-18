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


# @router.get("/config")
# async def get_config():
#     """
#     获取 AI 配置信息
#
#     Returns:
#         当前 AI 配置状态
#     """
#     is_configured = bool(services.ai_chat_service.api_key)
#     return BaseResponse.success(
#         data={
#             "configured": is_configured,
#             "model": services.ai_chat_service.model,
#             "api_base": services.ai_chat_service.api_base,
#         }
#     )


@router.get("/config/list")
async def get_config_list():
    """
    获取 AI 配置列表

    Returns:
        所有 AI 配置的列表
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            stmt = select(models.ai_config_table).order_by(
                models.ai_config_table.c.id
            )
            result = conn.execute(stmt)

            configs = []
            for row in result:
                config = {
                    "id": row.id,
                    "name": row.name,
                    "api_key": row.api_key,
                    "api_base": row.api_base,
                    "model": row.model,
                    "is_enabled": row.is_enabled,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                }
                configs.append(config)

            return BaseResponse.success(data=configs)
    except Exception as e:
        logger.error(f"获取配置列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取配置列表失败")


@router.get("/config/detail")
async def get_config_detail(config_id: int = 1):
    """
    获取 AI 配置详情（从数据库读取）

    Args:
        config_id: 配置 ID，默认为 1

    Returns:
        完整的 AI 配置信息
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            stmt = select(models.ai_config_table).where(
                models.ai_config_table.c.id == config_id
            )
            result = conn.execute(stmt).first()

            if result:
                config = {
                    "id": result.id,
                    "name": result.name,
                    "api_key": result.api_key,
                    "api_base": result.api_base,
                    "model": result.model,
                    "is_enabled": result.is_enabled,
                    "created_at": result.created_at.isoformat() if result.created_at else None,
                    "updated_at": result.updated_at.isoformat() if result.updated_at else None,
                }
            else:
                raise HTTPException(status_code=404, detail="配置不存在")

            return BaseResponse.success(data=config)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取配置详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取配置详情失败")

@router.post("/config/create")
async def create_config(request: schemas.AIConfigCreate):
    """
    创建新的 AI 配置

    Args:
        request: 配置创建请求

    Returns:
        创建的配置信息
    """
    try:
        engine = get_engine()
        now = datetime.now()

        with engine.connect() as conn:
            # 创建新配置
            insert_stmt = models.ai_config_table.insert().values(
                name=request.name,
                api_key=request.api_key,
                api_base=request.api_base,
                model=request.model,
                is_enabled=request.is_enabled,
                created_at=now,
                updated_at=now
            )
            result = conn.execute(insert_stmt)
            conn.commit()

            config_id = result.inserted_primary_key[0]

            logger.info(f"创建配置成功，ID: {config_id}")

            return BaseResponse.success(data={
                "id": config_id,
                "message": "配置创建成功"
            })
    except Exception as e:
        logger.error(f"创建配置失败: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建配置失败: {str(e)}")

@router.post("/config/test-connection")
async def test_connection(request: schemas.TestConnectionRequest):
    """
    测试 AI 配置连接

    使用传入的配置直接测试连接，不修改数据库中的激活状态。

    Args:
        request: 测试连接请求，包含 api_key, api_base, model

    Returns:
        测试结果
    """
    try:
        result = await services.ai_chat_service.test_connection(
            api_key=request.api_key,
            api_base=request.api_base,
            model=request.model,
            message=request.message
        )

        if result["success"]:
            return BaseResponse.success(data={
                "success": True,
                "content": result["content"]
            })
        else:
            return BaseResponse.error(
                error_code="CONNECTION_FAILED",
                error_msg=result["error"]
            )
    except Exception as e:
        logger.error(f"测试连接接口错误: {e}")
        return BaseResponse.error(
            error_code="CONNECTION_FAILED",
            error_msg=str(e)
        )

@router.post("/config/{config_id}")
async def save_config(config_id: int, request: schemas.AIConfigUpdate):
    """
    保存 AI 配置

    Args:
        config_id: 配置 ID
        request: 配置更新请求

    Returns:
        保存结果
    """
    try:
        engine = get_engine()
        now = datetime.now()

        with engine.connect() as conn:
            # 检查配置是否存在
            stmt = select(models.ai_config_table).where(
                models.ai_config_table.c.id == config_id
            )
            result = conn.execute(stmt).first()

            if not result:
                raise HTTPException(status_code=404, detail="配置不存在")

            # 更新配置
            update_values = {"updated_at": now}
            if request.name is not None:
                update_values["name"] = request.name
            if request.api_key is not None:
                update_values["api_key"] = request.api_key
            if request.api_base is not None:
                update_values["api_base"] = request.api_base
            if request.model is not None:
                update_values["model"] = request.model
            if request.is_enabled is not None:
                update_values["is_enabled"] = request.is_enabled

            update_stmt = update(models.ai_config_table).where(
                models.ai_config_table.c.id == config_id
            ).values(**update_values)
            conn.execute(update_stmt)

            conn.commit()

            # 重新加载配置到服务
            services.ai_chat_service.reload_config()

            return BaseResponse.success(data={"message": "配置保存成功"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"保存配置失败: {e}")
        raise HTTPException(status_code=500, detail="保存配置失败")

@router.delete("/config/{config_id}")
async def delete_config(config_id: int):
    """
    删除 AI 配置

    Args:
        config_id: 配置 ID

    Returns:
        删除结果
    """
    try:
        engine = get_engine()

        with engine.connect() as conn:
            # 检查配置是否存在
            stmt = select(models.ai_config_table).where(
                models.ai_config_table.c.id == config_id
            )
            result = conn.execute(stmt).first()

            if not result:
                raise HTTPException(status_code=404, detail="配置不存在")

            # 删除配置
            delete_stmt = delete(models.ai_config_table).where(
                models.ai_config_table.c.id == config_id
            )
            conn.execute(delete_stmt)

            conn.commit()

            # 重新加载配置到服务
            services.ai_chat_service.reload_config()

            return BaseResponse.success(data={"message": "配置删除成功"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除配置失败: {e}")
        raise HTTPException(status_code=500, detail="删除配置失败")


@router.post("/config/{config_id}/set-active")
async def set_active_config(config_id: int):
    """
    设置当前激活的 AI 配置

    Args:
        config_id: 配置 ID

    Returns:
        设置结果
    """
    try:
        engine = get_engine()

        with engine.connect() as conn:
            # 检查配置是否存在
            stmt = select(models.ai_config_table).where(
                models.ai_config_table.c.id == config_id
            )
            result = conn.execute(stmt).first()

            if not result:
                raise HTTPException(status_code=404, detail="配置不存在")

            # 先禁用所有配置
            disable_all_stmt = update(models.ai_config_table).values(
                is_enabled=False
            )
            conn.execute(disable_all_stmt)

            # 启用指定配置
            enable_stmt = update(models.ai_config_table).where(
                models.ai_config_table.c.id == config_id
            ).values(is_enabled=True)
            conn.execute(enable_stmt)

            conn.commit()

            # 重新加载配置到服务
            services.ai_chat_service.reload_config()

            return BaseResponse.success(data={"message": "已切换到指定配置"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"切换配置失败: {e}")
        raise HTTPException(status_code=500, detail="切换配置失败")


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
        now = datetime.now()
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


@router.put("/conversations/{conversation_id}")
async def update_conversation(conversation_id: int, request: schemas.ConversationUpdate):
    """
    更新对话标题

    Args:
        conversation_id: 对话ID
        request: 更新请求

    Returns:
        更新结果
    """
    try:
        engine = get_engine()
        now = datetime.now()

        with engine.connect() as conn:
            # 检查对话是否存在
            conv_stmt = select(models.conversations_table).where(
                models.conversations_table.c.id == conversation_id
            )
            conv_result = conn.execute(conv_stmt).first()

            if not conv_result:
                raise HTTPException(status_code=404, detail="对话不存在")

            # 更新对话标题
            update_values = {"updated_at": now}
            if request.title is not None:
                update_values["title"] = request.title

            update_stmt = update(models.conversations_table).where(
                models.conversations_table.c.id == conversation_id
            ).values(**update_values)
            conn.execute(update_stmt)

            conn.commit()

            return BaseResponse.success(data={"message": "对话标题已更新"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新对话标题失败: {e}")
        raise HTTPException(status_code=500, detail="更新对话标题失败")


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
        now = datetime.now()
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


# ========== 知识库管理接口 ==========

@router.get("/knowledge-base")
async def get_knowledge_bases():
    """
    获取所有知识库

    Returns:
        知识库列表
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            stmt = select(models.knowledge_base_table).order_by(
                models.knowledge_base_table.c.created_at.desc()
            )
            result = conn.execute(stmt)

            bases = []
            for row in result:
                bases.append({
                    "id": row.id,
                    "name": row.name,
                    "description": row.description,
                    "is_active": row.is_active,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                })

            return BaseResponse.success(data=bases)
    except Exception as e:
        logger.error(f"获取知识库列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取知识库列表失败")


@router.post("/knowledge-base")
async def create_knowledge_base(request: schemas.KnowledgeBaseCreate):
    """
    创建知识库

    Args:
        request: 知识库创建请求

    Returns:
        创建的知识库信息
    """
    try:
        engine = get_engine()
        now = datetime.now()

        with engine.connect() as conn:
            stmt = models.knowledge_base_table.insert().values(
                name=request.name,
                description=request.description,
                is_active=True,
                created_at=now,
                updated_at=now
            )
            result = conn.execute(stmt)
            conn.commit()

            base_id = result.inserted_primary_key[0]
            logger.info(f"创建知识库成功，ID: {base_id}")

            return BaseResponse.success(data={
                "id": base_id,
                "message": "知识库创建成功"
            })
    except Exception as e:
        logger.error(f"创建知识库失败: {e}")
        raise HTTPException(status_code=500, detail="创建知识库失败")


@router.put("/knowledge-base/{base_id}")
async def update_knowledge_base(base_id: int, request: schemas.KnowledgeBaseUpdate):
    """
    更新知识库

    Args:
        base_id: 知识库ID
        request: 更新请求

    Returns:
        更新结果
    """
    try:
        engine = get_engine()
        now = datetime.now()

        with engine.connect() as conn:
            # 检查知识库是否存在
            stmt = select(models.knowledge_base_table).where(
                models.knowledge_base_table.c.id == base_id
            )
            result = conn.execute(stmt).first()

            if not result:
                raise HTTPException(status_code=404, detail="知识库不存在")

            # 更新知识库
            update_values = {"updated_at": now}
            if request.name is not None:
                update_values["name"] = request.name
            if request.description is not None:
                update_values["description"] = request.description
            if request.is_active is not None:
                update_values["is_active"] = request.is_active

            update_stmt = update(models.knowledge_base_table).where(
                models.knowledge_base_table.c.id == base_id
            ).values(**update_values)
            conn.execute(update_stmt)

            conn.commit()

            return BaseResponse.success(data={"message": "知识库更新成功"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新知识库失败: {e}")
        raise HTTPException(status_code=500, detail="更新知识库失败")


@router.delete("/knowledge-base/{base_id}")
async def delete_knowledge_base(base_id: int):
    """
    删除知识库

    Args:
        base_id: 知识库ID

    Returns:
        删除结果
    """
    try:
        engine = get_engine()

        with engine.connect() as conn:
            # 检查知识库是否存在
            stmt = select(models.knowledge_base_table).where(
                models.knowledge_base_table.c.id == base_id
            )
            result = conn.execute(stmt).first()

            if not result:
                raise HTTPException(status_code=404, detail="知识库不存在")

            # 删除知识库（会级联删除文档和分片）
            delete_stmt = delete(models.knowledge_base_table).where(
                models.knowledge_base_table.c.id == base_id
            )
            conn.execute(delete_stmt)

            conn.commit()

            return BaseResponse.success(data={"message": "知识库删除成功"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除知识库失败: {e}")
        raise HTTPException(status_code=500, detail="删除知识库失败")


# ========== 知识文档管理接口 ==========

@router.get("/knowledge-base/{base_id}/documents")
async def get_documents(base_id: int):
    """
    获取知识库的所有文档

    Args:
        base_id: 知识库ID

    Returns:
        文档列表
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            stmt = select(models.knowledge_document_table).where(
                models.knowledge_document_table.c.knowledge_base_id == base_id
            ).order_by(
                models.knowledge_document_table.c.created_at.desc()
            )
            result = conn.execute(stmt)

            documents = []
            for row in result:
                documents.append({
                    "id": row.id,
                    "knowledge_base_id": row.knowledge_base_id,
                    "title": row.title,
                    "content": row.content,
                    "category": row.category,
                    "tags": row.tags,
                    "is_active": row.is_active,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                })

            return BaseResponse.success(data=documents)
    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取文档列表失败")


@router.post("/knowledge-base/{base_id}/documents")
async def create_document(base_id: int, request: schemas.KnowledgeDocumentCreate):
    """
    创建知识文档

    Args:
        base_id: 知识库ID
        request: 文档创建请求

    Returns:
        创建的文档信息
    """
    try:
        engine = get_engine()
        now = datetime.now()

        with engine.connect() as conn:
            # 检查知识库是否存在
            base_stmt = select(models.knowledge_base_table).where(
                models.knowledge_base_table.c.id == base_id
            )
            base_result = conn.execute(base_stmt).first()

            if not base_result:
                raise HTTPException(status_code=404, detail="知识库不存在")

            # 创建文档
            doc_stmt = models.knowledge_document_table.insert().values(
                knowledge_base_id=base_id,
                title=request.title,
                content=request.content,
                category=request.category,
                tags=request.tags,
                is_active=True,
                created_at=now,
                updated_at=now
            )
            doc_result = conn.execute(doc_stmt)
            conn.commit()

            doc_id = doc_result.inserted_primary_key[0]

            # 将文档内容分片（简单按段落分片）
            content = request.content
            chunks = content.split('\n\n')

            for idx, chunk in enumerate(chunks):
                if chunk.strip():
                    chunk_stmt = models.knowledge_chunk_table.insert().values(
                        document_id=doc_id,
                        chunk_index=idx,
                        content=chunk.strip(),
                        created_at=now
                    )
                    conn.execute(chunk_stmt)

            conn.commit()

            logger.info(f"创建文档成功，ID: {doc_id}，分片数: {len(chunks)}")

            return BaseResponse.success(data={
                "id": doc_id,
                "message": "文档创建成功"
            })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建文档失败: {e}")
        raise HTTPException(status_code=500, detail="创建文档失败")


@router.put("/documents/{doc_id}")
async def update_document(doc_id: int, request: schemas.KnowledgeDocumentUpdate):
    """
    更新知识文档

    Args:
        doc_id: 文档ID
        request: 更新请求

    Returns:
        更新结果
    """
    try:
        engine = get_engine()
        now = datetime.now()

        with engine.connect() as conn:
            # 检查文档是否存在
            stmt = select(models.knowledge_document_table).where(
                models.knowledge_document_table.c.id == doc_id
            )
            result = conn.execute(stmt).first()

            if not result:
                raise HTTPException(status_code=404, detail="文档不存在")

            # 更新文档
            update_values = {"updated_at": now}
            if request.title is not None:
                update_values["title"] = request.title
            if request.content is not None:
                update_values["content"] = request.content
            if request.category is not None:
                update_values["category"] = request.category
            if request.tags is not None:
                update_values["tags"] = request.tags
            if request.is_active is not None:
                update_values["is_active"] = request.is_active

            update_stmt = update(models.knowledge_document_table).where(
                models.knowledge_document_table.c.id == doc_id
            ).values(**update_values)
            conn.execute(update_stmt)

            # 如果更新了内容，重新生成分片
            if request.content is not None:
                # 删除旧分片
                delete_chunks_stmt = delete(models.knowledge_chunk_table).where(
                    models.knowledge_chunk_table.c.document_id == doc_id
                )
                conn.execute(delete_chunks_stmt)

                # 生成新分片
                chunks = request.content.split('\n\n')
                for idx, chunk in enumerate(chunks):
                    if chunk.strip():
                        chunk_stmt = models.knowledge_chunk_table.insert().values(
                            document_id=doc_id,
                            chunk_index=idx,
                            content=chunk.strip(),
                            created_at=now
                        )
                        conn.execute(chunk_stmt)

            conn.commit()

            return BaseResponse.success(data={"message": "文档更新成功"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新文档失败: {e}")
        raise HTTPException(status_code=500, detail="更新文档失败")


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: int):
    """
    删除知识文档

    Args:
        doc_id: 文档ID

    Returns:
        删除结果
    """
    try:
        engine = get_engine()

        with engine.connect() as conn:
            # 检查文档是否存在
            stmt = select(models.knowledge_document_table).where(
                models.knowledge_document_table.c.id == doc_id
            )
            result = conn.execute(stmt).first()

            if not result:
                raise HTTPException(status_code=404, detail="文档不存在")

            # 删除文档（会级联删除分片）
            delete_stmt = delete(models.knowledge_document_table).where(
                models.knowledge_document_table.c.id == doc_id
            )
            conn.execute(delete_stmt)

            conn.commit()

            return BaseResponse.success(data={"message": "文档删除成功"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文档失败: {e}")
        raise HTTPException(status_code=500, detail="删除文档失败")


# ========== 知识检索接口 ==========

@router.post("/knowledge-search")
async def search_knowledge(request: schemas.KnowledgeSearchRequest):
    """
    搜索知识库

    Args:
        request: 搜索请求

    Returns:
        搜索结果
    """
    try:
        search_results = services.ai_chat_service.search_knowledge(
            query=request.query,
            knowledge_base_id=request.knowledge_base_id,
            limit=request.limit
        )

        # 转换为响应格式
        results = []
        for item in search_results:
            results.append({
                "document_id": item["document_id"],
                "document_title": item["document_title"],
                "chunk_index": item["chunk_index"],
                "content": item["content"],
                "category": item["category"],
                "score": item["score"]
            })

        return BaseResponse.success(data=results)
    except Exception as e:
        logger.error(f"知识搜索失败: {e}")
        raise HTTPException(status_code=500, detail="知识搜索失败")


# ========== 带知识库的聊天接口 ==========

@router.post("/chat-with-knowledge")
async def chat_with_knowledge(request: schemas.ChatRequestWithKnowledge):
    """
    带知识库检索的聊天（流式 SSE）

    Args:
        request: 聊天请求（包含知识库配置）

    Returns:
        AI 响应（流式）
    """
    async def event_gen():
        try:
            knowledge_context = ""
            knowledge_used = False
            knowledge_sources = 0

            logger.info(f"开始带知识库的聊天，use_knowledge={request.use_knowledge}, knowledge_base_id={request.knowledge_base_id}")

            # 如果启用了知识库搜索
            if request.use_knowledge:
                try:
                    search_results = services.ai_chat_service.search_knowledge(
                        query=request.message,
                        knowledge_base_id=request.knowledge_base_id,
                        limit=3
                    )
                    logger.info(f"知识库搜索结果数量: {len(search_results)}")
                except Exception as search_error:
                    logger.error(f"知识库搜索失败: {search_error}")
                    search_results = []

                if search_results:
                    knowledge_context = services.ai_chat_service.build_knowledge_context(
                        search_results,
                        max_tokens=800
                    )
                    knowledge_used = True
                    knowledge_sources = len(search_results)
                    logger.info(f"使用知识库上下文，找到 {len(search_results)} 个相关片段")

            # 构建系统提示
            system_prompt = "你是一个有帮助的 AI 助手，专注于回答用户的问题和提供帮助。"

            if knowledge_context:
                system_prompt += f"\n\n请参考以下知识内容来回答用户的问题：\n\n{knowledge_context}"
                system_prompt += "\n\n如果知识内容中没有相关信息，请基于你的通用知识回答，并说明未在知识库中找到相关信息。"

            # 构建 messages
            messages = [
                {
                    "role": "system",
                    "content": system_prompt,
                }
            ]

            # 添加历史消息
            if request.history:
                for msg in request.history:
                    role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else None) or "user"
                    content = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else None) or ""
                    messages.append({"role": role, "content": content})

            # 添加当前用户消息
            messages.append({"role": "user", "content": request.message})

            logger.info(f"准备调用 AI API，消息数量: {len(messages)}")

            # 构建 payload
            payload = {
                "model": services.ai_chat_service.model,
                "messages": messages,
                "stream": True,
                "max_tokens": 512,
                "stop": ["null"],
                "temperature": 0.7,
                "top_p": 0.7,
                "top_k": 50,
                "frequency_penalty": 0.5,
                "n": 1,
                "response_format": {"type": "text"},
            }

            url = f"{services.ai_chat_service.api_base.rstrip('/')}/chat/completions"
            logger.info(f"API URL: {url}")

            import httpx
            async with httpx.AsyncClient(timeout=services.ai_chat_service.timeout) as client:
                async with client.stream(
                    "POST",
                    url,
                    headers={
                        "Authorization": f"Bearer {services.ai_chat_service.api_key}",
                        "Content-Type": "application/json",
                        "Accept": "text/event-stream",
                    },
                    json=payload,
                ) as resp:
                    try:
                        resp.raise_for_status()
                        logger.info(f"API 响应状态码: {resp.status_code}")
                    except httpx.HTTPStatusError as e:
                        text = await e.response.aread()
                        logger.error(f"iflow stream http error {e.response.status_code}: {text}")
                        raise RuntimeError(f"iflow stream http error {e.response.status_code}: {text!r}") from e

                    async for line in resp.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("data:"):
                            data_str = line[len("data:"):].strip()
                            if data_str == "[DONE]":
                                logger.info("收到 [DONE] 标记")
                                break
                            try:
                                chunk = json.loads(data_str)
                                delta = (
                                    chunk.get("choices", [{}])[0]
                                    .get("delta", {})
                                    .get("content", "")
                                )
                                if delta:
                                    logger.debug(f"收到数据块: {delta[:50]}...")
                                    yield f"data: {json.dumps({'delta': delta}, ensure_ascii=False)}\n\n"
                            except Exception as parse_error:
                                logger.warning(f"解析 SSE 数据失败: {data_str}, 错误: {parse_error}")
                                continue

            # 流式完成后发送知识库使用信息
            logger.info("流式响应完成，发送知识库使用信息")
            yield f"data: {json.dumps({'knowledge_used': knowledge_used, 'knowledge_sources': knowledge_sources, 'done': True}, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"带知识库的聊天失败: {e}", exc_info=True)
            yield f"data: {json.dumps({'error': 'AI 服务暂时不可用'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")
