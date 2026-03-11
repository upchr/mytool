# feishu.py
import httpx
import time
import hmac
import hashlib
import base64
from typing import Dict, Any
from .base import NotificationStrategy


class FeishuStrategy(NotificationStrategy):
    """飞书自定义机器人通知策略（Webhook 模式）"""

    strategy_name = "feishu"

    def _validate_config(self):
        """验证飞书配置"""
        required_fields = ['webhook_url']
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"飞书配置缺少必要字段：{field}")

    def _generate_sign(self, timestamp: str, secret: str) -> str:
        """生成飞书签名（用于 webhook 签名校验）"""
        string_to_sign = f'{timestamp}\n{secret}'
        hmac_code = hmac.new(
            string_to_sign.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        sign = base64.b64encode(hmac_code).decode('utf-8')
        return sign

    async def send(self, title: str, content: str, **kwargs) -> Dict[str, Any]:
        """
        发送飞书机器人通知

        Args:
            title: 通知标题
            content: 通知内容
            **kwargs: 额外参数
                - msg_type: 'text', 'post', 'interactive'
                - webhook_url: 覆盖 webhook 地址
                - secret: 覆盖签名密钥
                - mentioned_list: @用户列表 (open_id)

        Returns:
            发送结果字典
        """
        webhook_url = kwargs.get('webhook_url', self.config['webhook_url'])
        secret = kwargs.get('secret', self.config.get('secret', ''))
        msg_type = kwargs.get('msg_type', 'interactive')

        # 构建消息内容
        if msg_type == 'text':
            data = {
                "msg_type": "text",
                "content": {
                    "text": f"**{title}**\n\n{content}"
                }
            }
        elif msg_type == 'post':
            # 富文本格式（推荐）
            data = {
                "msg_type": "post",
                "content": {
                    "post": {
                        "zh_cn": {
                            "title": title,
                            "content": [
                                [{"tag": "text", "text": content}]
                            ]
                        }
                    }
                }
            }
        elif msg_type == 'interactive':
            # 交互卡片
            data = {
                "msg_type": "interactive",
                "card": {
                    "header": {
                        "title": {"tag": "plain_text", "content": title}
                    },
                    "elements": [
                        {
                            "tag": "markdown",
                            "content": content
                        }
                    ]
                }
            }
        else:
            data = {
                "msg_type": "text",
                "content": {
                    "text": f"{title}\n\n{content}"
                }
            }

        # 添加签名（如果配置了 secret）
        if secret:
            timestamp = str(int(time.time()))
            sign = self._generate_sign(timestamp, secret)
            data["timestamp"] = timestamp
            data["sign"] = sign

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    webhook_url,
                    json=data,
                    headers={'Content-Type': 'application/json'}
                )
                response.raise_for_status()

                result = response.json()
                return {
                    'success': result.get('code') == 0,
                    'message': result.get('msg', ''),
                    'raw_response': result
                }
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
                'raw_response': None
            }

    def test_connection(self) -> bool:
        """测试连接（发送测试消息）"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(
                self.send("🔔 测试通知", "这是一条测试消息，确认飞书机器人配置正常。")
            )
            return result.get('success', False)
        except Exception:
            return False
