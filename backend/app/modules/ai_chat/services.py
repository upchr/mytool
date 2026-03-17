import httpx
import logging
import os
import asyncio
import re
from typing import AsyncIterator, List, Optional
import json
from sqlalchemy import select

logger = logging.getLogger(__name__)


class AIChatService:
    def __init__(self):
        # 使用你提供的默认配置，可通过环境变量覆盖
        self.api_key = os.getenv("AI_API_KEY")
        self.api_base = os.getenv("AI_API_BASE")
        # 默认使用你指定的模型，可通过 AI_MODEL 覆盖
        self.model = os.getenv("AI_MODEL")
        self.timeout = 30.0
        # 尝试从数据库加载配置
        self._load_from_db()

    def _load_from_db(self):
        """从数据库加载配置"""
        try:
            from app.core.db.database import get_engine
            from . import models
            
            engine = get_engine()
            with engine.connect() as conn:
                stmt = select(models.ai_config_table).where(
                    models.ai_config_table.c.id == 1
                )
                result = conn.execute(stmt).first()
                
                if result and result.is_enabled:
                    # 优先使用数据库配置
                    if result.api_key:
                        self.api_key = result.api_key
                    if result.api_base:
                        self.api_base = result.api_base
                    if result.model:
                        self.model = result.model
                    
                    logger.info(f"从数据库加载 AI 配置: api_base={self.api_base}, model={self.model}")
        except Exception as e:
            logger.warning(f"从数据库加载 AI 配置失败: {e}，使用环境变量配置")

    def reload_config(self):
        """重新加载配置"""
        logger.info("重新加载 AI 配置")
        self._load_from_db()

    async def chat(self, message: str, history: Optional[List] = None) -> str:
        """
        直接按照官方 API 文档调用 iFlow /chat/completions 接口。
        参考: https://platform.iflow.cn/docs/api-reference
        """
        try:
            # 构建 messages（system + history + 当前消息）
            messages = [
                {
                    "role": "system",
                    "content": "你是一个有帮助的 AI 助手，专注于回答用户的问题和提供帮助。",
                }
            ]

            if history:
                for msg in history:
                    # history 可能是 dict，也可能是 Pydantic 模型（schemas.Message）
                    role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else None) or "user"
                    content = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else None) or ""
                    messages.append(
                        {
                            "role": role,
                            "content": content,
                        }
                    )

            messages.append({"role": "user", "content": message})

            if not self.api_key:
                logger.warning("AI_API_KEY 未配置，使用本地模拟响应")
                return self._get_mock_response(message)

            url = f"{self.api_base.rstrip('/')}/chat/completions"

            # 严格按官方 curl 示例构造 payload
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "max_tokens": 512,
                "stop": ["null"],
                "temperature": 0.7,
                "top_p": 0.7,
                "top_k": 50,
                "frequency_penalty": 0.5,
                "n": 1,
                "response_format": {"type": "text"},
                # tools 字段留空，不使用函数调用
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )

                # 如果是 4xx/5xx，尽量把错误内容打到日志里方便排查
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as e:
                    # 把 iFlow 返回的具体错误内容直接透传给前端，方便你排查
                    error_text = e.response.text
                    logger.error(
                        f"iFlow API HTTP 错误: {e.response.status_code} {e}\n"
                        f"响应内容: {error_text}"
                    )
                    return f"iflow 接口调用失败，HTTP {e.response.status_code}，响应：{error_text}"

                data = response.json()
                # 按官方文档解析 choices[0].message.content
                content = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )
                if not content:
                    logger.error(f"iFlow 返回内容为空或结构异常: {data}")
                    return self._get_error_response()

                return content

        except httpx.HTTPError as e:
            logger.error(f"iFlow API 请求失败: {e}")
            return self._get_error_response()
        except Exception as e:
            logger.error(f"AI chat 调用异常: {e}")
            return self._get_error_response()

    async def chat_stream(self, message: str, history: Optional[List] = None) -> AsyncIterator[str]:
        """
        流式调用 iFlow /chat/completions，并把增量内容逐段 yield 出去（不包含 SSE 包装）。
        """
        # 构建 messages（system + history + 当前消息）
        messages = [
            {
                "role": "system",
                "content": "你是一个有帮助的 AI 助手，专注于回答用户的问题和提供帮助。",
            }
        ]

        if history:
            for msg in history:
                role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else None) or "user"
                content = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else None) or ""
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": message})

        if not self.api_key:
            # 未配置 API Key 时，使用流式输出模拟响应（按短句分段，模拟真实效果）
            mock_response = self._get_mock_response(message)
            # 按标点符号分割成小段，模拟流式输出效果
            segments = re.split(r'([,.!?.,:;\s]+)', mock_response)
            for segment in segments:
                if segment:
                    yield segment
                    await asyncio.sleep(0.05)  # 添加微小延迟，模拟网络传输
            return

        url = f"{self.api_base.rstrip('/')}/chat/completions"
        payload = {
            "model": self.model,
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

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream",
                },
                json=payload,
            ) as resp:
                try:
                    resp.raise_for_status()
                except httpx.HTTPStatusError as e:
                    text = await e.response.aread()
                    raise RuntimeError(f"iflow stream http error {e.response.status_code}: {text!r}") from e

                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    # iflow SSE: "data: {...}"
                    if line.startswith("data:"):
                        data_str = line[len("data:"):].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = (
                                chunk.get("choices", [{}])[0]
                                .get("delta", {})
                                .get("content", "")
                            )
                            if delta:
                                yield delta
                        except Exception:
                            # 忽略解析失败的分片
                            continue

    def _get_mock_response(self, message: str) -> str:
        """本地模拟响应"""
        return (
            f"我收到了你的消息：'{message}'。目前还没有配置有效的 iflow API Key，"
            f"请在后端环境变量 AI_API_KEY 中配置。"
        )

    def _get_error_response(self) -> str:
        """错误兜底响应"""
        return "抱歉，AI 服务暂时不可用。请稍后重试或检查 iflow API 配置。"


# 全局服务实例
ai_chat_service = AIChatService()
